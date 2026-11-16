"""Wells Fargo checking statements.

The "Transaction history" table lists one transaction per row::

    Date Number Description Additions Subtractions balance
    1/2 Bank of America Mortgage 250102 P12739652 798.44 3,157.01

The last amount on a row is the running balance when the row has two amounts. A long
description wraps, pushing the amounts onto a following line.

The "Statement period activity summary" above the table gives the totals the transactions
are checked against::

    Deposits/Additions 950.00
    Withdrawals/Subtractions - 1,123.95
"""

from __future__ import annotations

import re
from typing import Optional, Sequence

from personal_expenses_app.infrastructure.statement_loader import (
    StatementLoader,
    Transaction,
    parse_amount,
)
from personal_expenses_app.infrastructure.statement_period import StatementPeriod
from personal_expenses_app.infrastructure.statement_reconciliation import StatementTotals

_STARTS_WITH_DATE = re.compile(r"^\d{1,2}/\d{1,2}\s+")
_DATED_LINE = re.compile(r"^(\d{1,2})/(\d{1,2})\s+(.+)$")
_AMOUNT = re.compile(r"[\d,]+\.\d{2}")
_DEPOSITS_TOTAL = re.compile(r"Deposits/Additions\s+\$?([\d,]+\.\d{2})")
_WITHDRAWALS_TOTAL = re.compile(r"Withdrawals/Subtractions\s+-\s*\$?([\d,]+\.\d{2})")

_COLUMN_HEADER_MARKERS = ("Date Number Description", "Deposits/", "Withdrawals/")
# The statement does not say which column an amount came from once it is text, so
# additions are recognised by their description.
_CREDIT_KEYWORDS = ("transfer from", "deposit", "credit", "interest", "refund")


def _parse_transaction(row: str) -> Optional[Transaction]:
    """Parse a complete ``M/D Description Amount [Balance]`` row; None if it is not one yet."""
    match = _DATED_LINE.match(row.strip())
    if not match:
        return None
    month, day, rest = match.groups()

    amounts = _AMOUNT.findall(rest)
    if not amounts:
        return None
    amount = parse_amount(amounts[-2] if len(amounts) >= 2 else amounts[0])

    description = rest
    for printed_amount in amounts:
        description = description.replace(printed_amount, "").strip()
    description = " ".join(description.split())

    lowered = description.lower()
    if any(keyword in lowered for keyword in _CREDIT_KEYWORDS):
        return Transaction(int(month), int(day), description, credit=amount)
    return Transaction(int(month), int(day), description, debit=amount)


class WellsfargoFileLoader(StatementLoader):
    bank = "wellsfargo"

    def _parse_transactions(self, page_texts: Sequence[str], period: StatementPeriod) -> list[Transaction]:
        transactions: list[Transaction] = []
        in_transaction_history = False
        wrapped_row: Optional[str] = None  # A row still waiting for the line with its amounts.

        for text in page_texts:
            for line in text.split("\n"):
                if "Transaction history" in line:
                    in_transaction_history = True
                    continue
                if line.strip().startswith("Totals"):
                    in_transaction_history = False
                    wrapped_row = None
                    continue
                if not in_transaction_history:
                    continue
                if any(marker in line for marker in _COLUMN_HEADER_MARKERS):
                    continue

                if _STARTS_WITH_DATE.match(line):
                    row = line
                elif wrapped_row:
                    row = f"{wrapped_row} {line.strip()}"
                else:
                    continue

                transaction = _parse_transaction(row)
                if transaction:
                    transactions.append(transaction)
                    wrapped_row = None
                else:
                    wrapped_row = row

        return transactions

    def _printed_totals(self, page_texts: Sequence[str]) -> Optional[StatementTotals]:
        text = "\n".join(page_texts)
        deposits = _DEPOSITS_TOTAL.search(text)
        withdrawals = _WITHDRAWALS_TOTAL.search(text)
        if not deposits or not withdrawals:
            return None
        return StatementTotals(parse_amount(withdrawals.group(1)), parse_amount(deposits.group(1)))
