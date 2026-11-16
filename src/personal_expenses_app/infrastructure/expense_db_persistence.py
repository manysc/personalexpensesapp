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
        # Every row lacks a debit or a credit. Imports store the missing one as NaN, which
        # equals itself; manual entries store NULL, which only does with NULLS NOT DISTINCT.
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


_NATURAL_KEY_COLUMNS = ["Date", "Bank", "Description", "Debit", "Credit"]


def _natural_key(date, bank, description, debit, credit) -> tuple:
    """Return a row's natural key in a form that is equal for a stored row and a parsed one."""

    def cents(amount) -> Optional[int]:
        is_missing = amount is None or amount != amount  # NaN is the only value unequal to itself.
        return None if is_missing else round(float(amount) * 100)

    return str(date), bank, description, cents(debit), cents(credit)


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
        records = self._records(labeled_expenses, list(self._COLUMN_MAP))
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

    def find_missing(self, expenses: pd.DataFrame) -> pd.DataFrame:
        """Return the rows of ``expenses`` that are not stored, e.g. because they were deleted.

        ``expenses`` has the columns Date, Bank, Description, Debit and Credit, as a
        statement loader returns them; rows are matched on exactly those, the way
        save_expenses stores them. The rows are returned with their descriptions as they
        would be stored (see with_stored_descriptions).
        """
        stored_form = self.with_stored_descriptions(expenses)
        records = self._records(stored_form, _NATURAL_KEY_COLUMNS)
        if not records:
            return stored_form
        dates = [str(record["date"]) for record in records]
        with self._engine.connect() as conn:
            stored = conn.execute(
                text(
                    "SELECT date, bank, description, debit, credit FROM all_expenses "
                    "WHERE bank = ANY(:banks) AND date >= :first AND date <= :last"
                ),
                {"banks": sorted({r["bank"] for r in records}), "first": min(dates), "last": max(dates)},
            ).all()
        stored_keys = {_natural_key(*row) for row in stored}
        is_missing = [_natural_key(**record) not in stored_keys for record in records]
        return stored_form[pd.Series(is_missing, index=stored_form.index, dtype=bool)]

    @staticmethod
    def with_stored_descriptions(expenses: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with each description as it is stored.

        Rows sharing a natural key (date, bank, description, debit, credit) get " (2)",
        " (3)", ... appended to the description of the repeats, so that each occurrence
        is stored. Applying this twice changes nothing.
        """
        seen: dict = defaultdict(int)
        descriptions = []
        for date, bank, description, debit, credit in expenses[_NATURAL_KEY_COLUMNS].itertuples(index=False):
            key = _natural_key(date, bank, description, debit, credit)
            seen[key] += 1
            descriptions.append(description if seen[key] == 1 else f"{description} ({seen[key]})")
        result = expenses.copy()
        result["Description"] = pd.Series(descriptions, index=expenses.index, dtype=object)
        return result

    def _records(self, expenses: pd.DataFrame, columns: list[str]) -> list[dict]:
        """Convert a DataFrame to the rows to store, one dict per row.

        A missing debit or credit stays NaN, and is stored as NaN: that is what the rows
        already in the database hold, so sending NULL instead would no longer match them
        and every re-import would insert its rows a second time.
        """
        renamed = self.with_stored_descriptions(expenses)[columns].rename(columns=self._COLUMN_MAP)
        return renamed.where(pd.notnull(renamed), None).to_dict(orient="records")
