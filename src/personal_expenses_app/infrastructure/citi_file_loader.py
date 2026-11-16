"""Citi credit card statements.

Each cardholder has a section of purchases, and payments/credits have their own. The
usual transaction is one line::

    12/09 12/10 DAIRY QUEEN #15096 TUCSON AZ $11.50        (sale date, post date)
    11/03 AUTOPAY 999990000037199RAUTOPAY AUTO-PMT -$3,993.51   (negative = credit)

but pdfplumber often spreads one over several lines, mixed with the rewards summary
printed beside the table:

* description first, date and amount after::

      BREW CITY BRAND - AIRPORTMILWAUKEE
      02/28 02/28 $23.74

* foreign purchases, whose dollar amount comes on the exchange-rate line::

      12/20 PURO PA DELANTE HERMOSILLO SOMX
      1,250.00 MEXICAN PESO $68.00

* lodging charges, with folio lines between the description and a bare amount.

The parser therefore walks the lines keeping a "pending" description: text that still
needs an amount (and sometimes a date) from a line further down.

The "Account Summary" on the first page gives the totals the transactions are checked
against::

    Payments -$5,644.82
    Credits -$602.22
    Purchases +$4,621.54
    Cash advances +$0.00
    Fees +$0.00
    Interest +$0.00
"""

from __future__ import annotations

import logging
import re
from typing import NamedTuple, Optional, Sequence

from personal_expenses_app.infrastructure.statement_loader import (
    StatementLoader,
    Transaction,
    parse_amount,
)
from personal_expenses_app.infrastructure.statement_period import StatementPeriod
from personal_expenses_app.infrastructure.statement_reconciliation import StatementTotals

logger = logging.getLogger(__name__)

# The names that head each cardholder's section of the statement.
CARDHOLDER_NAMES = ("MANUEL SALAS", "REYNA VARELA")

# Stored when a transaction's description cannot be found. It is part of the saved rows'
# natural key, so it must not change.
_MISSING_DESCRIPTION = "PENDING_DESCRIPTION"

_DATE = r"\d{1,2}/\d{1,2}"
_AMOUNT = r"-?\$?[\d,]+\.\d{2}"

_STARTS_WITH_DATE = re.compile(rf"^({_DATE})")
_STARTS_WITH_TWO_DATES = re.compile(rf"^{_DATE}\s+{_DATE}")
_DATE_THEN_REST = re.compile(rf"^({_DATE})\s*(.*)$")
_DATE_THEN_TEXT = re.compile(rf"^({_DATE})\s+(.+)")
_DATE_AMOUNT = re.compile(rf"^({_DATE})\s+({_AMOUNT})")
_DATE_DESCRIPTION_AMOUNT = re.compile(rf"^({_DATE})\s+(.+?)\s+({_AMOUNT})")
_TWO_DATES_AMOUNT = re.compile(rf"^({_DATE})\s+{_DATE}\s+({_AMOUNT})(?=\s|$)")
_TWO_DATES_AMOUNT_ONLY = re.compile(rf"^{_DATE}\s+{_DATE}\s+{_AMOUNT}\s*$")
_TWO_DATES_DESCRIPTION_AMOUNT = re.compile(rf"^({_DATE})\s+{_DATE}\s+(.+?)\s+({_AMOUNT})")
_BARE_AMOUNT = re.compile(rf"^({_AMOUNT})\s*$")
_DOLLAR_AMOUNT = re.compile(r"\$[\d,]+\.\d{2}")

# "1,250.00 MEXICAN PESO $68.00": the dollar amount of the foreign purchase above it.
_FOREIGN_AMOUNT_LINE = re.compile(r"^[\d,]+\.\d+-?\s+MEXICAN\s+PESO")
_FOREIGN_AMOUNT = re.compile(rf"^[\d,]+\.\d+-?\s+MEXICAN\s+PESO\s+({_AMOUNT})")
_FOREIGN_CURRENCY = "MEXICAN PESO"

# A pending description as "MM/DD [MM/DD] text".
_PENDING_WITH_DATE = re.compile(rf"^({_DATE})\s+(?:{_DATE}\s+)?(.*)")
_PENDING_DATE_PREFIX = re.compile(rf"^{_DATE}\s+(.*)")

# Rewards-summary text that pdfplumber appends to transaction lines.
_YEAR_TO_DATE_LABEL = re.compile(r"Year to Date\s*:\s*$", re.IGNORECASE)
_REWARD_RATE_SUFFIX = re.compile(r"\s+\d%\s+on\s+.*?\+\$[\d,]+\.\d{2}.*$", re.IGNORECASE)
_REWARDS_HEADER_SUFFIX = re.compile(r"\s+Costco\s+Cash\s+Back\s+Rewards$", re.IGNORECASE)
_MERCHANT_BEFORE_REWARD_TEXT = re.compile(r"^([A-Z0-9][A-Z0-9\s\*\-]+?)(?:\s+\d+%\s+on\s+|\s+Total\s+Earned)")
_REWARDS_TOTAL_LABEL = "Total Earned:"

# Lodging charges list these between the merchant line and the amount.
_LODGING_FOLIO_METADATA = re.compile(
    r"^(PHONE NUMBER:|FOLIO NUMBER:|ARRIVE:\s*\d{1,2}/\d{1,2}/\d{2,4}\s+DEPART:)", re.IGNORECASE
)
_URL_FRAGMENT = re.compile(r"^WWW\.", re.IGNORECASE)

_PAYMENTS_SECTION_HEADER = "Payments, Credits and Adjustments"
_REWARDS_SECTION_HEADER = "Costco Cash Back Rewards"
_SECTION_END_PREFIXES = (
    "CARDHOLDER SUMMARY",
    "Foreign Currency Transactions",
    "Interest Charged",
    "Fees",
    "Year-To-Date Totals",
)
# "2026 totals year-to-date": the fees and interest summary that follows the transactions.
_YEARLY_TOTALS_HEADER = re.compile(r"^\d{4}\s+totals\s+year-to-date", re.IGNORECASE)
# "Fees Charged" and "Interest Charged" are short tables of dated lines, each closed by a
# "TOTAL ... FOR THIS PERIOD" line.
_CHARGES_SECTION_HEADERS = ("Fees Charged", "Interest Charged")
_CHARGES_COLUMN_HEADER = "Description"

# Account Summary lines. Their signs tell them apart from the same words elsewhere, and
# the layout often puts other text on the same line.
_SUMMARY_DEBITS = tuple(
    re.compile(rf"{label}\s+\+\$([\d,]+\.\d{{2}})")
    for label in ("Purchases", "Cash advances", "Fees", "Interest")
)
_SUMMARY_CREDITS = tuple(
    re.compile(rf"{label}\s+-\$([\d,]+\.\d{{2}})") for label in ("Payments", "Credits")
)

_NOISE_MARKERS = (
    "Sale Post",
    "Date Date Description Amount",
    "Balance:",
    "New Charges",
    "Earned this period",
)


class _ParsedLine(NamedTuple):
    """What one line that starts with a date holds; the missing parts are on other lines."""

    date: str  # "MM/DD"
    description: Optional[str]
    amount: Optional[float]


def _parse_dated_line(stripped: str) -> Optional[_ParsedLine]:
    """Split a line that starts with a date into date, description and amount."""
    match = _TWO_DATES_DESCRIPTION_AMOUNT.match(stripped)
    # "... Year to Date : $509.64" is the rewards summary, not this transaction's amount.
    if match and not _YEAR_TO_DATE_LABEL.search(match.group(2)):
        return _ParsedLine(match.group(1), match.group(2).strip(), parse_amount(match.group(3)))

    match = _DATE_DESCRIPTION_AMOUNT.match(stripped)
    if match and not _STARTS_WITH_DATE.match(match.group(2).strip()):
        return _ParsedLine(match.group(1), match.group(2).strip(), parse_amount(match.group(3)))

    match = _TWO_DATES_AMOUNT.match(stripped) or _DATE_AMOUNT.match(stripped)
    if match:
        return _ParsedLine(match.group(1), None, parse_amount(match.group(2)))

    match = _DATE_THEN_TEXT.match(stripped)
    if match:
        return _ParsedLine(match.group(1), None, None)
    return None


def _could_be_description(stripped: str) -> bool:
    return (
        len(stripped) > 5
        and not _STARTS_WITH_DATE.match(stripped)
        and _FOREIGN_CURRENCY not in stripped
    )


def _is_merchant_line(stripped: str) -> bool:
    """True for a line holding only a merchant name, e.g. "BREW CITY BRAND - AIRPORTMILWAUKEE"."""
    return (
        len(stripped) > 5
        and stripped[0].isupper()
        and not _STARTS_WITH_DATE.match(stripped)
        and not stripped.lower().startswith("cont'd")
        and not stripped.startswith("Page ")
        and not _URL_FRAGMENT.match(stripped)  # "WWW.AMAZON.COWA" continues the line above.
        and len(stripped.split()) >= 2
    )


def _is_only_reward_or_info_text(text: str) -> bool:
    """True when the text after a line's leading date is no part of a transaction.

    Such a line is just the date of the description above it, followed by nothing or by
    text from the rewards summary ("Total Earned: $63.02", "for more information").
    """
    merchant = _MERCHANT_BEFORE_REWARD_TEXT.match(text)
    if merchant and len(merchant.group(1).strip()) > 5:
        return False

    has_amount = bool(_DOLLAR_AMOUNT.search(text))
    is_reward_or_info = (
        "Total Earned" in text
        or "on all other" in text
        or ("for more information" in text.lower() and not has_amount)
    )
    if (has_amount and not is_reward_or_info) or text.startswith("AUTOPAY"):
        return False

    capitalised_words = [word for word in text.split() if word[0].isupper() or word[0].isdigit()]
    looks_like_merchant = (
        len(text) > 10 and (text[0].isupper() or text[0].isdigit()) and len(capitalised_words) >= 2
    )
    if looks_like_merchant:
        return False
    return is_reward_or_info or not (len(text) > 10 and text[0].isupper())


def _without_reward_text(description: str) -> str:
    description = _REWARD_RATE_SUFFIX.sub("", description)
    description = _REWARDS_HEADER_SUFFIX.sub("", description)
    return description.strip()


class _StatementParser:
    """Walks a statement's lines; the state carries over from one page to the next."""

    def __init__(self) -> None:
        self.transactions: list[Transaction] = []
        self._lines: list[str] = []  # The lines of the page being read.
        self._cardholder: Optional[str] = None
        self._in_transaction_section = False
        self._in_payments_section = False
        # A description (sometimes with its date in front) still waiting for its amount.
        self._pending: Optional[str] = None
        self._skip_next_line = False
        self._in_charges_section = False

    def parse(self, page_texts: Sequence[str]) -> list[Transaction]:
        for text in page_texts:
            self._lines = text.split("\n")
            for index, line in enumerate(self._lines):
                self._read_line(index, line, line.strip())
        return self.transactions

    def _read_line(self, index: int, line: str, stripped: str) -> None:
        """Try each kind of line in turn; the order of the checks matters."""
        if self._skip_next_line:
            self._skip_next_line = False
            return
        if _LODGING_FOLIO_METADATA.match(stripped):
            return
        if self._in_charges_section and self._read_charge(stripped):
            return
        if (
            self._read_cardholder_header(index, line)
            or self._read_foreign_amount(stripped)
            or self._read_bare_amount(stripped)
            or self._read_section_boundary(line, stripped)
            or self._is_noise(index, line, stripped)
            or self._read_date_of_previous_description(index, stripped)
        ):
            return
        if not self._in_transaction_section:
            return
        if self._read_description_ahead_of_its_date(index, stripped) or self._read_amount_of_pending(stripped):
            return
        self._read_dated_line(index, stripped)

    # -- Line handlers: each returns True when it has dealt with the line. --

    def _read_cardholder_header(self, index: int, line: str) -> bool:
        name = next((name for name in CARDHOLDER_NAMES if name in line), None)
        if name is None or "Card ending in" in line:
            return False

        self._cardholder = name
        # On a "cont'd" header the section simply carries on from the previous page.
        if "cont'd" not in self._line(index + 1).lower():
            self._in_transaction_section = self._transactions_follow(index)
            if "cont'd" not in line.lower():
                self._pending = None
        return True

    def _read_foreign_amount(self, stripped: str) -> bool:
        match = _FOREIGN_AMOUNT.match(stripped)
        if not match:
            return False
        self._add_pending_with_date(parse_amount(match.group(1)), strip_reward_text=True)
        self._pending = None
        return True

    def _read_bare_amount(self, stripped: str) -> bool:
        """An amount alone on a line (e.g. a lodging folio total) belongs to the pending description."""
        match = _BARE_AMOUNT.match(stripped)
        if not match or not self._pending:
            return False
        self._add_pending_with_date(parse_amount(match.group(1)), strip_reward_text=False)
        self._pending = None
        return True

    def _read_section_boundary(self, line: str, stripped: str) -> bool:
        if _PAYMENTS_SECTION_HEADER in line:
            self._in_transaction_section = True
            self._in_payments_section = True
        elif self._starts_purchases_section(line, stripped):
            # A section continuing on a new page repeats its header: keep the pending description.
            self._in_transaction_section = True
            self._in_payments_section = False
        elif stripped.startswith(_SECTION_END_PREFIXES) or _YEARLY_TOTALS_HEADER.match(stripped):
            self._in_transaction_section = False
            self._in_payments_section = False
            self._pending = None
            self._in_charges_section = stripped.startswith(_CHARGES_SECTION_HEADERS)
        else:
            return False
        return True

    def _read_charge(self, stripped: str) -> bool:
        """Read a line of the fees or interest table; any other line ends the table."""
        parsed = _parse_dated_line(stripped)
        if parsed and parsed.description and parsed.amount is not None:
            self._add(parsed.date, parsed.description, parsed.amount)
            return True
        if _CHARGES_COLUMN_HEADER in stripped:
            return True
        self._in_charges_section = False
        return False

    def _is_noise(self, index: int, line: str, stripped: str) -> bool:
        """True for blank lines, column headers and rewards-summary lines."""
        if not stripped or any(marker in line for marker in _NOISE_MARKERS):
            return True
        if _REWARDS_TOTAL_LABEL not in line:
            return False
        # "Total Earned: $61.68" also gets appended to lines that belong to a transaction.
        has_own_amount = bool(_STARTS_WITH_DATE.match(stripped)) and bool(
            _DOLLAR_AMOUNT.search(stripped.split(_REWARDS_TOTAL_LABEL)[0])
        )
        previous = self._line(index - 1).strip() if index > 0 else ""
        follows_description = _could_be_description(previous) and previous[0].isupper()
        return not (has_own_amount or follows_description or self._foreign_amount_within(index, 3))

    def _read_date_of_previous_description(self, index: int, stripped: str) -> bool:
        """Handle a date on its own line (maybe with reward text) under its description::

            GOB EDO SONORA E COM HERMOSILLO
            12/20 Total Earned: $63.02
        """
        match = _DATE_THEN_REST.match(stripped)
        if (
            not match
            or _STARTS_WITH_TWO_DATES.match(stripped)
            or self._in_payments_section
            or self._pending
            or not _is_only_reward_or_info_text(match.group(2).strip())
        ):
            return False

        previous = self._line(index - 1).strip() if index > 0 else ""
        if _could_be_description(previous):
            self._pending = f"{match.group(1)} {previous}"
        return True

    def _read_description_ahead_of_its_date(self, index: int, stripped: str) -> bool:
        if not _is_merchant_line(stripped) or index + 1 >= len(self._lines):
            return False

        next_line = self._line(index + 1).strip()
        if _TWO_DATES_AMOUNT_ONLY.match(next_line) or _DATE_AMOUNT.match(next_line):
            self._pending = stripped
            return True

        next_date = _STARTS_WITH_DATE.match(next_line)
        if next_date and self._foreign_amount_within(index, 4):
            # A foreign purchase: take the date from the next line and wait for the amount.
            self._pending = f"{next_date.group(1)} {stripped}"
            self._skip_next_line = True
            return True
        return False

    def _read_amount_of_pending(self, stripped: str) -> bool:
        """Handle "MM/DD $Amount [reward text]" under the description it belongs to."""
        match = _DATE_AMOUNT.match(stripped) if self._pending else None
        if not match:
            return False
        self._add(match.group(1), self._pending, parse_amount(match.group(2)))
        self._pending = None
        return True

    def _read_dated_line(self, index: int, stripped: str) -> None:
        parsed = _parse_dated_line(stripped)
        if parsed is None:
            return
        if parsed.amount is None:
            # The amount is further down (foreign currency); an earlier description wins.
            if not self._pending:
                self._pending = stripped
            return

        description = parsed.description
        if description is None:
            description = self._description_from_context(index)
        self._pending = None
        self._add(parsed.date, description, parsed.amount)

    # -- Helpers --

    def _line(self, index: int) -> str:
        return self._lines[index] if index < len(self._lines) else ""

    def _transactions_follow(self, header_index: int) -> bool:
        """True when the lines right under a cardholder header are already transactions."""
        next_line = self._line(header_index + 1).strip()
        if _FOREIGN_AMOUNT_LINE.match(next_line):
            # The amount of a purchase from the previous page; look past it.
            next_line = self._line(header_index + 2).strip()
        return bool(_STARTS_WITH_DATE.match(next_line))

    def _starts_purchases_section(self, line: str, stripped: str) -> bool:
        return (
            "Standard Purchases" in line
            or (bool(self._cardholder) and "Purchase" in line and "Payments" not in line)
            or stripped.startswith(_REWARDS_SECTION_HEADER)
            or (
                "Earned This Period" in line
                and "Earned this period" not in line
                and not _STARTS_WITH_DATE.match(stripped)
            )
        )

    def _foreign_amount_within(self, index: int, lookahead: int) -> bool:
        following = self._lines[index + 1 : index + 1 + lookahead]
        return any(_FOREIGN_CURRENCY in line for line in following)

    def _description_from_context(self, index: int) -> str:
        """Find the description of a line that has only a date and an amount."""
        if self._pending:
            match = _PENDING_DATE_PREFIX.match(self._pending)
            return match.group(1).strip() if match else self._pending
        # Nearest line first, so an "AMAZON MARK* ..." line wins over the URL fragment
        # ("WWW.AMAZON.COWA") left over from the transaction before it.
        for line in reversed(self._lines[max(0, index - 3) : index]):
            if _could_be_description(line.strip()):
                return line.strip()
        return _MISSING_DESCRIPTION

    def _add_pending_with_date(self, amount: float, *, strip_reward_text: bool) -> None:
        """Add the pending description as a transaction, if it carries its date."""
        match = _PENDING_WITH_DATE.match(self._pending or "")
        if not match:
            return
        description = match.group(2).strip()
        if strip_reward_text:
            description = _without_reward_text(description)
        self._add(match.group(1), description, amount)

    def _add(self, date: str, description: str, amount: float) -> None:
        month, day = date.split("/")
        transaction = Transaction.from_signed_amount(int(month), int(day), description, amount)
        self.transactions.append(transaction)
        logger.debug("Parsed transaction for %s: %s", self._cardholder, transaction)


class CitiFileLoader(StatementLoader):
    bank = "citi"

    def _parse_transactions(self, page_texts: Sequence[str], period: StatementPeriod) -> list[Transaction]:
        return _StatementParser().parse(page_texts)

    def _printed_totals(self, page_texts: Sequence[str]) -> Optional[StatementTotals]:
        text = "\n".join(page_texts)
        debits = [pattern.search(text) for pattern in _SUMMARY_DEBITS]
        credits = [pattern.search(text) for pattern in _SUMMARY_CREDITS]
        if not all(debits) or not all(credits):
            return None
        return StatementTotals(
            debits=round(sum(parse_amount(match.group(1)) for match in debits), 2),
            credits=round(sum(parse_amount(match.group(1)) for match in credits), 2),
        )
