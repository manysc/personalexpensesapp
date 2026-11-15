"""What every bank statement loader has in common.

A loader turns one statement PDF into a DataFrame with the columns
``Date, Description, Debit, Credit, Bank``. Fetching the PDF, extracting its text, dating
the transactions and building the DataFrame are identical for every bank and live here;
a bank's own module only knows how to read transactions out of that bank's page text.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import ClassVar, NamedTuple, Optional, Sequence

import pandas as pd

from personal_expenses_app.core.rule_based_expense_categorizer import (
    RuleBasedExpenseCategorizer,
)
from personal_expenses_app.infrastructure.pdf_text import extract_page_texts
from personal_expenses_app.infrastructure.s3_storage import get_object_bytes
from personal_expenses_app.infrastructure.statement_period import StatementPeriod, statement_period

logger = logging.getLogger(__name__)

COLUMNS = ["Date", "Description", "Debit", "Credit", "Bank"]


class Transaction(NamedTuple):
    """One statement line. Statements print dates without a year, hence month and day."""

    month: int
    day: int
    description: str
    debit: Optional[float] = None
    credit: Optional[float] = None

    @classmethod
    def from_signed_amount(cls, month: int, day: int, description: str, amount: float) -> Transaction:
        """Build a transaction from a card-style amount, where a negative is a credit."""
        if amount < 0:
            return cls(month, day, description, credit=abs(amount))
        return cls(month, day, description, debit=amount)


def parse_amount(text: str) -> float:
    """Convert a printed amount such as ``-$3,993.51`` or ``1,325.00`` to a float."""
    return float(text.replace(",", "").replace("$", ""))


class StatementLoader(ABC):
    """Loads the transactions of one bank's statement PDFs.

    ``key`` arguments are S3 object keys such as ``resources/chase/2026/chase-jan-2026.pdf``.
    """

    bank: ClassVar[str]
    # A statement without transactions normally means its layout was not understood.
    fail_when_empty: ClassVar[bool] = True

    @abstractmethod
    def _parse_transactions(self, page_texts: Sequence[str], period: StatementPeriod) -> list[Transaction]:
        """Read the transactions out of the statement's non-empty pages, in page order."""

    def load_expenses_and_credits(self, key: str) -> pd.DataFrame:
        """Load every transaction of the statement stored under ``key``."""
        return self.parse_statement(key, extract_page_texts(get_object_bytes(key)))

    def load_expenses(self, key: str) -> pd.DataFrame:
        """Load only the debits of the statement stored under ``key``."""
        df = self.load_expenses_and_credits(key)
        return df[df["Debit"].notnull()]

    def load_credits(self, key: str) -> pd.DataFrame:
        """Load only the credits of the statement stored under ``key``."""
        df = self.load_expenses_and_credits(key)
        return df[df["Credit"].notnull()]

    def load_and_label_multiple_files(self, keys: Sequence[str]) -> pd.DataFrame:
        """Load and categorize several statements, skipping any that do not exist."""
        categorizer = RuleBasedExpenseCategorizer()
        labeled = []
        for key in keys:
            try:
                df = self.load_expenses_and_credits(key)
            except FileNotFoundError:
                print(f"Warning: File not found: {key}")
                continue
            labeled.append(categorizer.categorize_expenses(df))

        if not labeled:
            raise ValueError(
                f"No valid expense files found. Checked {len(keys)} files. Please verify file paths."
            )
        return pd.concat(labeled, ignore_index=True)

    def parse_statement(self, key: str, page_texts: Sequence[str]) -> pd.DataFrame:
        """Build the statement's DataFrame from its already-extracted page texts."""
        period = statement_period(self.bank, page_texts[0] if page_texts else "", key)
        transactions = self._parse_transactions([text for text in page_texts if text], period)
        if not transactions:
            logger.warning("No transactions found in PDF: %s", key)
            if self.fail_when_empty:
                raise ValueError(f"No transactions found in PDF: {key}")
        return self._to_frame(transactions, period)

    def _to_frame(self, transactions: Sequence[Transaction], period: StatementPeriod) -> pd.DataFrame:
        dates = [f"{t.month}/{t.day}/{period.year_of(t.month)}" for t in transactions]
        df = pd.DataFrame(
            {
                # An impossible date (e.g. from a garbled line) becomes NaT rather than an error.
                "Date": pd.to_datetime(dates, format="%m/%d/%Y", errors="coerce"),
                "Description": [t.description for t in transactions],
                "Debit": pd.Series([t.debit for t in transactions], dtype="float64"),
                "Credit": pd.Series([t.credit for t in transactions], dtype="float64"),
                "Bank": self.bank,
            },
            columns=COLUMNS,
        )
        return df.sort_values("Date").reset_index(drop=True)
