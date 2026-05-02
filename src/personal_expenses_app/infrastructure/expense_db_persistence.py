import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, Integer, Numeric, String, UniqueConstraint, create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import DeclarativeBase, Session

_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(_project_root / ".env")


class _Base(DeclarativeBase):
    pass


class _AllExpense(_Base):
    __tablename__ = "all_expenses"
    __table_args__ = (
        UniqueConstraint(
            "date", "bank", "description", "debit", "credit",
            name="uix_expense_natural_key",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(20), nullable=False)
    bank = Column(String(50), nullable=False)
    description = Column(String(500), nullable=False)
    debit = Column(Numeric(12, 2), nullable=True)
    credit = Column(Numeric(12, 2), nullable=True)
    category = Column(String(100), nullable=True)
    overridden = Column(Boolean, nullable=False, default=False, server_default="false")
    comments = Column(String(2000), nullable=True)


class ExpenseDbPersistence:
    """Persists labeled expense DataFrames into the all_expenses table in a PostgreSQL database."""

    _COLUMN_MAP = {
        "Date": "date",
        "Bank": "bank",
        "Description": "description",
        "Debit": "debit",
        "Credit": "credit",
        "Category": "category",
    }

    def __init__(self, connection_string: str | None = None):
        if connection_string is None:
            connection_string = os.environ.get("DATABASE_URL")
        if not connection_string:
            raise ValueError(
                "A database connection string must be provided or set via the "
                "DATABASE_URL environment variable."
            )
        self._engine = create_engine(connection_string)
        _Base.metadata.create_all(self._engine)
        self._run_migrations()

    def _run_migrations(self) -> None:
        """Apply incremental schema migrations."""
        with self._engine.connect() as conn:
            # Widen date column if created with a smaller size in an earlier version.
            conn.execute(
                text(
                    "ALTER TABLE all_expenses "
                    "ALTER COLUMN date TYPE VARCHAR(20)"
                )
            )
            # Before adding the unique constraint, remove duplicate rows that
            # may have been inserted by earlier runs of save_expenses, keeping
            # the most-recently inserted record (highest id) for each group.
            conn.execute(
                text(
                    "DELETE FROM all_expenses a "
                    "USING all_expenses b "
                    "WHERE a.id < b.id "
                    "  AND a.date = b.date "
                    "  AND a.bank = b.bank "
                    "  AND a.description = b.description "
                    "  AND (a.debit = b.debit OR (a.debit IS NULL AND b.debit IS NULL)) "
                    "  AND (a.credit = b.credit OR (a.credit IS NULL AND b.credit IS NULL))"
                )
            )
            # Add the unique constraint (idempotent: skipped if already present).
            # NULLS NOT DISTINCT ensures two NULL debit/credit values are treated
            # as equal, which is required for correct duplicate detection.
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "  IF NOT EXISTS ( "
                    "    SELECT 1 FROM pg_constraint "
                    "    WHERE conname = 'uix_expense_natural_key' "
                    "  ) THEN "
                    "    ALTER TABLE all_expenses "
                    "    ADD CONSTRAINT uix_expense_natural_key "
                    "    UNIQUE NULLS NOT DISTINCT (date, bank, description, debit, credit); "
                    "  END IF; "
                    "END $$;"
                )
            )
            # Add overridden column if it doesn't exist yet.
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "  IF NOT EXISTS ( "
                    "    SELECT 1 FROM information_schema.columns "
                    "    WHERE table_name = 'all_expenses' AND column_name = 'overridden' "
                    "  ) THEN "
                    "    ALTER TABLE all_expenses "
                    "    ADD COLUMN overridden BOOLEAN NOT NULL DEFAULT FALSE; "
                    "  END IF; "
                    "END $$;"
                )
            )
            conn.commit()

    def save_expenses(self, labeled_expenses: pd.DataFrame) -> None:
        """Upsert all rows from labeled_expenses into the all_expenses table.

        Rows already present (matched by date, bank, description, debit, and
        credit) have their category updated; new rows are inserted.  Calling
        this method multiple times with the same data is therefore idempotent.

        Args:
            labeled_expenses: DataFrame with columns Date, Bank, Description,
                              Debit, Credit, and Category.
        """
        renamed = labeled_expenses.rename(columns=self._COLUMN_MAP)[
            list(self._COLUMN_MAP.values())
        ]
        records = renamed.where(pd.notnull(renamed), None).to_dict(orient="records")
        if not records:
            return
        stmt = pg_insert(_AllExpense)
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uix_expense_natural_key",
            set_={
                "category": text(
                    "CASE WHEN all_expenses.overridden = TRUE "
                    "THEN all_expenses.category "
                    "ELSE EXCLUDED.category END"
                ),
            },
        )
        with Session(self._engine) as session:
            session.execute(upsert_stmt, records)
            session.commit()
