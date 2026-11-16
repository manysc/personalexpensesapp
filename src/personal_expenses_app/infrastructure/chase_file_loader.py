"""Chase checking statements.

Transactions are listed as ``MM/DD Description $Amount`` under section headers that say
whether they are deposits or withdrawals, e.g.::

    DEPOSITS AND ADDITIONS
    DATE DESCRIPTION AMOUNT
    12/23 Zelle Payment From Jane Doe Wfct0Yclh2Kt $600.00
    Total Deposits and Additions $600.00

The "CHECKING SUMMARY" at the top gives one total per section, which the transactions are
checked against. A linked Chase Savings account printed in the same PDF is not imported.
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Optional, Sequence

from personal_expenses_app.infrastructure.statement_loader import (
    StatementLoader,
    Transaction,
    parse_amount,
)
from personal_expenses_app.infrastructure.statement_period import StatementPeriod
from personal_expenses_app.infrastructure.statement_reconciliation import StatementTotals

logger = logging.getLogger(__name__)


class _Section(Enum):
    CREDITS = "credits"
    DEBITS = "debits"


# Each section closes with "Total <section name> $amount".
_SECTION_TOTAL_PREFIXES = (
    "Total Deposits",
    "Total Electronic",
    "Total Other Withdrawals",
    "Total ATM",
    "Total Fees",
)
_END_OF_SECTION_MARKER = "*end*"

_SUMMARY_HEADER = "CHECKING SUMMARY"
_SUMMARY_FIRST_LINE = "Beginning Balance"
_SUMMARY_LAST_LINE = "Ending Balance"
# "Deposits and Additions 16,782.67" / "Electronic Withdrawals -17,053.49"
_SUMMARY_LINE = re.compile(r"^.+?\s+(-?)\$?([\d,]+\.\d{2})$")
_SAVINGS_HEADER = "SAVINGS SUMMARY"

_TRANSACTION = re.compile(r"^(\d{1,2})/(\d{1,2})\s+(.+?)\s+\$?([\d,]+\.\d{2})$")
# A page break can scatter a transaction's month digits into the "*end*" marker, e.g.
#   "*end*deposi0ts and additio2ns /05 Zelle Payment From ... 1,325.00"
# (the "02" of "02/05"). What survives is "/DD description amount".
_GARBLED_TRANSACTION = re.compile(r"/(\d{2})\s+(.+?)\s+([\d,]+\.\d{2})$")


def _transaction(section: _Section, month: int, day: int, description: str, amount: float) -> Transaction:
    if section is _Section.CREDITS:
        return Transaction(month, day, description, credit=amount)
    return Transaction(month, day, description, debit=amount)


def _section_started_by(line: str, stripped: str) -> Optional[_Section]:
    if "DEPOSITS AND ADDITIONS" in line:
        return _Section.CREDITS
    if "ELECTRONIC WITHDRAWALS" in line:
        return _Section.DEBITS
    if "OTHER WITHDRAWALS" in line and not stripped.startswith("Total"):
        return _Section.DEBITS
    if "ATM & DEBIT CARD WITHDRAWALS" in line or stripped == "FEES":
        return _Section.DEBITS
    return None


def _recover_garbled_transaction(
    stripped: str, section: _Section, period: StatementPeriod
) -> Optional[Transaction]:
    """Rebuild the transaction a page break merged into an "*end*" marker, if there is one.

    Its month is unreadable, so it is taken to be the statement's closing month.
    """
    match = _GARBLED_TRANSACTION.search(stripped)
    if not match:
        return None
    day, description, amount = match.groups()
    transaction = _transaction(section, period.month, int(day), description.strip(), parse_amount(amount))
    logger.info("Recovered garbled transaction from *end* line: %s", transaction)
    return transaction


class ChaseFileLoader(StatementLoader):
    bank = "chase"

    def _parse_transactions(self, page_texts: Sequence[str], period: StatementPeriod) -> list[Transaction]:
        transactions: dict[_Section, list[Transaction]] = {_Section.CREDITS: [], _Section.DEBITS: []}
        section: Optional[_Section] = None

        for text in page_texts:
            for line in text.split("\n"):
                stripped = line.strip()

                started = _section_started_by(line, stripped)
                if started:
                    section = started
                    continue
                if stripped.startswith(_SECTION_TOTAL_PREFIXES):
                    section = None
                    continue
                if stripped.startswith(_END_OF_SECTION_MARKER) and section:
                    recovered = _recover_garbled_transaction(stripped, section, period)
                    if recovered:
                        transactions[section].append(recovered)
                    section = None
                    continue
                if not section or "DATE DESCRIPTION AMOUNT" in line:
                    continue

                match = _TRANSACTION.match(stripped)
                if match:
                    month, day, description, amount = match.groups()
                    transactions[section].append(
                        _transaction(section, int(month), int(day), description.strip(), parse_amount(amount))
                    )

        return transactions[_Section.CREDITS] + transactions[_Section.DEBITS]

    def _printed_totals(self, page_texts: Sequence[str]) -> Optional[StatementTotals]:
        """Add up the checking summary: negative lines are withdrawals, the rest deposits."""
        lines = (line.strip() for text in page_texts for line in text.split("\n"))
        if not any(_SUMMARY_HEADER in line for line in lines):
            return None

        debits = credits = 0.0
        for line in lines:  # Continues after the header.
            if line.startswith(_SUMMARY_LAST_LINE):
                return StatementTotals(round(debits, 2), round(credits, 2))
            match = _SUMMARY_LINE.match(line)
            if not match or line.startswith(_SUMMARY_FIRST_LINE):
                continue
            if match.group(1):
                debits += parse_amount(match.group(2))
            else:
                credits += parse_amount(match.group(2))
        return None

    def _note(self, page_texts: Sequence[str]) -> str:
        has_savings = any(_SAVINGS_HEADER in text for text in page_texts)
        return "(Its Chase Savings section is not imported.)" if has_savings else ""
