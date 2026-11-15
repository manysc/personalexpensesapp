import os
import threading
from collections import defaultdict
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, Integer, Numeric, String, UniqueConstraint, create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session

_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(_project_root / ".env")


class _Base(DeclarativeBase):
    pass


class _AllExpense(_Base):
    __tablename__ = "all_expenses"
    __table_args__ = (
        # NULLS NOT DISTINCT: every row has a NULL debit or credit, and the upsert in
        # save_expenses only finds the existing row if NULLs compare equal.
        UniqueConstraint(
            "date", "bank", "description", "debit", "credit",
            name="uix_expense_natural_key",
            postgresql_nulls_not_distinct=True,
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


# The schema checks need to run once per database per process, not on every import.
_schema_ready: set[str] = set()
_schema_lock = threading.Lock()

# Each statement is idempotent and cheap when there is nothing to change: it only reads
# the catalog. The duplicate cleanup in particular runs only while the natural key is not
# enforced, which is the only time duplicates can exist.
_MIGRATIONS = (
    # Widen the date column if an earlier version created it narrower.
    """
    DO $$ BEGIN
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'all_expenses' AND column_name = 'date'
          AND character_maximum_length < 20
      ) THEN
        ALTER TABLE all_expenses ALTER COLUMN date TYPE VARCHAR(20);
      END IF;
    END $$;
    """,
    # Enforce the natural key with NULLs comparing equal. Before (re)creating it, remove
    # duplicate rows that the missing or NULLs-distinct key let in, keeping the most
    # recently inserted (highest id) of each.
    """
    DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c JOIN pg_index i ON i.indexrelid = c.conindid
        WHERE c.conname = 'uix_expense_natural_key' AND i.indnullsnotdistinct
      ) THEN
        DELETE FROM all_expenses a
        USING all_expenses b
        WHERE a.id < b.id
          AND a.date = b.date
          AND a.bank = b.bank
          AND a.description = b.description
          AND (a.debit = b.debit OR (a.debit IS NULL AND b.debit IS NULL))
          AND (a.credit = b.credit OR (a.credit IS NULL AND b.credit IS NULL));
        ALTER TABLE all_expenses DROP CONSTRAINT IF EXISTS uix_expense_natural_key;
        ALTER TABLE all_expenses
          ADD CONSTRAINT uix_expense_natural_key
          UNIQUE NULLS NOT DISTINCT (date, bank, description, debit, credit);
      END IF;
    END $$;
    """,
    """
    DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'all_expenses' AND column_name = 'overridden'
      ) THEN
        ALTER TABLE all_expenses ADD COLUMN overridden BOOLEAN NOT NULL DEFAULT FALSE;
      END IF;
    END $$;
    """,
)


class ExpenseDbPersistence:
    """Persists labeled expense DataFrames into the all_expenses table in a PostgreSQL database.

    Pass the application's ``engine`` to share its connection pool; otherwise an engine is
    created from ``connection_string`` or the ``DATABASE_URL`` environment variable.
    """

    _COLUMN_MAP = {
        "Date": "date",
        "Bank": "bank",
        "Description": "description",
        "Debit": "debit",
        "Credit": "credit",
        "Category": "category",
    }

    def __init__(self, connection_string: Optional[str] = None, *, engine: Optional[Engine] = None):
        if engine is None:
            connection_string = connection_string or os.environ.get("DATABASE_URL")
            if not connection_string:
                raise ValueError(
                    "A database connection string must be provided or set via the "
                    "DATABASE_URL environment variable."
                )
            engine = create_engine(connection_string)
        self._engine = engine
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create the table and apply migrations, the first time this process sees the database."""
        database = self._engine.url.render_as_string(hide_password=False)
        with _schema_lock:
            if database in _schema_ready:
                return
            _Base.metadata.create_all(self._engine)
            with self._engine.begin() as conn:
                for migration in _MIGRATIONS:
                    conn.execute(text(migration))
            _schema_ready.add(database)

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
        # Deduplicate within-batch: if two rows share the same natural key
        # (date, bank, description, debit, credit), append " (2)", " (3)", ...
        # so each row gets a distinct key and all occurrences are stored.
        # NaN != NaN in Python (IEEE 754), so normalise NaN → None before
        # using values as dict keys to ensure identical rows compare equal.
        def _norm(v):
            try:
                return None if pd.isna(v) else v
            except (TypeError, ValueError):
                return v

        seen: dict = defaultdict(int)
        for record in records:
            key = (_norm(record["date"]), _norm(record["bank"]), _norm(record["description"]),
                   _norm(record["debit"]), _norm(record["credit"]))
            seen[key] += 1
            if seen[key] > 1:
                record["description"] = f"{record['description']} ({seen[key]})"
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
