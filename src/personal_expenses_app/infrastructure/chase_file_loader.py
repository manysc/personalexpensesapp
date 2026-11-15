"""Chase checking statements.

Transactions are listed as ``MM/DD Description $Amount`` under section headers that say
whether they are deposits or withdrawals, e.g.::

    DEPOSITS AND ADDITIONS
    DATE DESCRIPTION AMOUNT
    12/23 Zelle Payment From Jane Doe Wfct0Yclh2Kt $600.00
    Total Deposits and Additions $600.00
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

logger = logging.getLogger(__name__)


class _Section(Enum):
    CREDITS = "credits"
    DEBITS = "debits"


_SECTION_TOTAL_PREFIXES = ("Total Deposits", "Total Electronic", "Total Other Withdrawals")
_END_OF_SECTION_MARKER = "*end*"

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
