"""Banamex account statements (amounts in Mexican pesos, converted to US dollars).

The "Detalle de Operaciones" table has the columns
``FECHA | CONCEPTO | RETIROS | DEPÓSITOS | SALDO``. A transaction starts on a line with
its date (``DD MMM``) and can continue over several lines, some of them branch metadata
(SUC, CAJA, HORA, AUT). The last line carrying amounts holds the transaction amount
followed by the running balance.

The "Resumen" block counts and totals the period's movements, which the transactions are
checked against (in pesos)::

    (+) 1 Depósitos 10,636.00
    (-) 5 Retiros/Otros cargos 10,944.00
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

from personal_expenses_app.infrastructure.statement_loader import StatementLoader, Transaction
from personal_expenses_app.infrastructure.statement_period import StatementPeriod
from personal_expenses_app.infrastructure.statement_reconciliation import StatementTotals

PESOS_PER_DOLLAR = 18.5

_MONTH_BY_SPANISH_ABBREVIATION = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12,
}
_UNKNOWN_MONTH = 1

_TRANSACTION_START = re.compile(r"^(\d{1,2})\s+([A-Z]{3})\s+(.+)$")
# pdfplumber sometimes splits the cents: "1,234.5 6".
_AMOUNT = re.compile(r"[\d,]+\.\d\s?\d")
_PAGE_FOOTER = re.compile(r"Página \d+ de \d+")
_REFERENCE_NUMBER = re.compile(r"^\d{8,}$")
_DEPOSITS_TOTAL = re.compile(r"\(\+\)\s*(\d+)\s+Dep[oó]sitos\s+([\d,]+\.\d{2})")
_WITHDRAWALS_TOTAL = re.compile(r"\(-\)\s*(\d+)\s+Retiros/Otros cargos\s+([\d,]+\.\d{2})")

_METADATA_PREFIXES = ("SUC ", "CAJA ", "HORA ", "AUT ")
_OPENING_BALANCE = "SALDO ANTERIOR"
_CREDIT_KEYWORDS = (
    "PAGO RECIBIDO", "DEPOSITO", "DEPÓSITO", "ABONO", "TRANSFERENCIA RECIBIDA",
    "EXENCION", "EXENCIÓN", "INTERES", "INTERÉS",
)


def _parse_pesos(printed_amount: str) -> float:
    return float(printed_amount.replace(" ", "").replace(",", ""))


def _split_amounts(text: str) -> tuple[str, list[float]]:
    """Separate a line into its description text and the amounts printed on it."""
    printed_amounts = _AMOUNT.findall(text)
    for printed_amount in printed_amounts:
        text = text.replace(printed_amount, "", 1)
    return " ".join(text.split()), [_parse_pesos(amount) for amount in printed_amounts]


def _is_table_header(line: str) -> bool:
    return "FECHA CONCEPTO" in line and ("RETIROS" in line or "DEP" in line)


def _ends_table(line: str, stripped: str) -> bool:
    return "Resumen Operaciones" in line or stripped.startswith("TARJETA ")


def _is_boilerplate(line: str, stripped: str) -> bool:
    return (
        not stripped
        or "FECHA CONCEPTO" in line
        or stripped.startswith("000")
        or "Detalle de Operaciones" in line
        or "En pesos Moneda Nacional" in line
        or stripped.startswith("Ciudad de México:")
        or stripped.startswith("Resto del país:")
    )


def _is_metadata(stripped: str) -> bool:
    return stripped.startswith(_METADATA_PREFIXES) or bool(_REFERENCE_NUMBER.match(stripped))


@dataclass
class _OpenTransaction:
    """A transaction whose lines are still being read."""

    day: int
    month: int
    description_lines: list[str] = field(default_factory=list)
    amounts: list[float] = field(default_factory=list)


class _StatementParser:
    """Reads one statement; keeps the running balance used to tell deposits from withdrawals."""

    def __init__(self) -> None:
        self.transactions: list[Transaction] = []
        self._in_table = False
        self._open: Optional[_OpenTransaction] = None
        self._previous_balance: Optional[float] = None

    def parse(self, page_texts: Sequence[str]) -> list[Transaction]:
        for text in page_texts:
            for line in text.split("\n"):
                self._read_line(line, line.strip())
        self._close_open_transaction()
        return self.transactions

    def _read_line(self, line: str, stripped: str) -> None:
        if _is_table_header(line):
            self._in_table = True
        elif _ends_table(line, stripped):
            self._close_open_transaction()
            self._in_table = False
        elif not self._in_table:
            pass
        elif _PAGE_FOOTER.search(stripped):
            # The table resumes at the next header; a transaction may continue across the break.
            self._in_table = False
        elif _is_boilerplate(line, stripped):
            pass
        elif start := _TRANSACTION_START.match(stripped):
            self._close_open_transaction()
            self._open_transaction(*start.groups())
        elif self._open:
            self._continue_transaction(stripped)

    def _open_transaction(self, day: str, month_abbreviation: str, rest: str) -> None:
        month = _MONTH_BY_SPANISH_ABBREVIATION.get(month_abbreviation, _UNKNOWN_MONTH)
        self._open = _OpenTransaction(int(day), month)
        description, amounts = _split_amounts(rest)
        if description and description.upper() != _OPENING_BALANCE:
            self._open.description_lines.append(description)
        if amounts:
            self._open.amounts = amounts

    def _continue_transaction(self, stripped: str) -> None:
        description, amounts = _split_amounts(stripped)
        if amounts:
            self._open.amounts = amounts
        if description and not description.startswith("$") and not _is_metadata(stripped):
            self._open.description_lines.append(description)

    def _close_open_transaction(self) -> None:
        transaction, self._open = self._open, None
        if transaction is None or not transaction.amounts:
            return

        description = " ".join(transaction.description_lines).strip()
        amounts = transaction.amounts
        if not description or _OPENING_BALANCE in description.upper():
            if len(amounts) == 1:
                self._previous_balance = amounts[0]
            return
        if len(amounts) == 1:
            return  # Only a balance: no transaction amount was printed.

        amount, balance = amounts[0], amounts[-1]
        is_credit = any(keyword in description.upper() for keyword in _CREDIT_KEYWORDS) or (
            self._previous_balance is not None and balance > self._previous_balance
        )
        self._previous_balance = balance

        if is_credit:
            self.transactions.append(Transaction(transaction.month, transaction.day, description, credit=amount))
        else:
            self.transactions.append(Transaction(transaction.month, transaction.day, description, debit=amount))


class BanamexFileLoader(StatementLoader):
    bank = "banamex"
    currency = "MXN"
    # An account with no movements in the month is a legitimate, empty statement.
    fail_when_empty = False

    def _parse_transactions(self, page_texts: Sequence[str], period: StatementPeriod) -> list[Transaction]:
        return _StatementParser().parse(page_texts)

    def _printed_totals(self, page_texts: Sequence[str]) -> Optional[StatementTotals]:
        text = "\n".join(page_texts)
        deposits = _DEPOSITS_TOTAL.search(text)
        withdrawals = _WITHDRAWALS_TOTAL.search(text)
        if not deposits or not withdrawals:
            return None
        return StatementTotals(
            debits=_parse_pesos(withdrawals.group(2)),
            credits=_parse_pesos(deposits.group(2)),
            debit_count=int(withdrawals.group(1)),
            credit_count=int(deposits.group(1)),
        )

    def _to_dollars(self, amount: float) -> float:
        return round(amount / PESOS_PER_DOLLAR, 2)
