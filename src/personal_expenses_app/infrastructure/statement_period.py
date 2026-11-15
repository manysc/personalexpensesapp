"""Read a statement's closing month from the PDF itself instead of trusting the filename.

Loaders date transactions as MM/DD plus a year, and treat any transaction month later
than the statement's month as belonging to the previous year (December charges on a
January statement). Both the year and that month used to come from the filename only,
so a statement filed under the wrong month (e.g. the October Citi statement saved as
"citi-sep-2026.pdf") silently shifted its October charges back a year.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

MONTH_ABBR = ["", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
_MONTH_BY_NAME = {name: i for i, name in enumerate(MONTH_ABBR) if name}

# Each pattern captures (closing month, closing year) from the first page's text.
_PATTERNS: dict[str, re.Pattern[str]] = {
    # "Billing Period: 09/09/26-10/08/26"
    "citi": re.compile(
        r"Billing\s+Period:\s*\d{1,2}/\d{1,2}/\d{2,4}\s*-\s*(\d{1,2})/\d{1,2}/(\d{2,4})", re.IGNORECASE
    ),
    # "September 18, 2026 through October 19, 2026" (pdfplumber may drop the spaces around "through")
    "chase": re.compile(
        r"[A-Za-z]+\s+\d{1,2},\s*\d{4}\s*through\s*([A-Za-z]+)\s+\d{1,2},\s*(\d{4})", re.IGNORECASE
    ),
    # Statement date at the top of page 1: "October 26, 2026 Page 1 of 5"
    "wellsfargo": re.compile(r"^\s*([A-Za-z]+)\s+\d{1,2},\s*(\d{4})\s+Page\s+1\s+of\s+\d+", re.IGNORECASE | re.MULTILINE),
}

# Statement keys look like "resources/citi/2026/citi-oct-2026.pdf".
_FILENAME_PERIOD = re.compile(r"-([a-z]{3})-(\d{4})\.pdf$", re.IGNORECASE)


@dataclass(frozen=True)
class StatementPeriod:
    """The month a statement closes in."""

    year: int
    month: int

    def year_of(self, transaction_month: int) -> int:
        """Return the year of a transaction that the statement lists only as MM/DD.

        A month later than the closing month can only belong to the previous year
        (December charges on a January statement).
        """
        return self.year - 1 if transaction_month > self.month else self.year


def period_from_filename(filename: str) -> Optional[tuple[str, int]]:
    """Return the ``(year, month_num)`` a statement was filed under, or None if the key has none."""
    match = _FILENAME_PERIOD.search(filename)
    month = _MONTH_BY_NAME.get(match.group(1).lower()) if match else None
    if month is None:
        return None
    return match.group(2), month


def _month_number(token: str) -> Optional[int]:
    if token.isdigit():
        n = int(token)
        return n if 1 <= n <= 12 else None
    return _MONTH_BY_NAME.get(token[:3].lower())


def statement_closing_month(bank: str, first_page_text: Optional[str]) -> Optional[tuple[int, int]]:
    """Return ``(year, month)`` of the statement's closing date, or None if it can't be found."""
    pattern = _PATTERNS.get(bank)
    if pattern is None or not first_page_text:
        return None
    match = pattern.search(first_page_text)
    if not match:
        return None
    month = _month_number(match.group(1))
    year = int(match.group(2))
    if year < 100:
        year += 2000
    if month is None:
        return None
    return year, month


def resolve_statement_period(
    bank: str, first_page_text: Optional[str], filename: str, year: str, month_num: int
) -> tuple[str, int]:
    """Return the ``(year, month_num)`` to date this statement's transactions with.

    Uses the closing month printed in the PDF when it can be found, otherwise the values
    parsed from the filename. Prints a warning (shown in the import log) when the two
    disagree, since that means the file was uploaded under the wrong month.
    """
    closing = statement_closing_month(bank, first_page_text)
    if closing is None:
        return year, month_num
    closing_year, closing_month = closing
    if (str(closing_year), closing_month) != (str(year), month_num):
        print(
            f"WARNING: {filename} is the {bank} statement for {MONTH_ABBR[closing_month]} {closing_year} "
            f"(per the PDF), not {MONTH_ABBR[month_num] if 1 <= month_num <= 12 else month_num} {year}. "
            f"Dating its transactions from the PDF. Re-upload it as "
            f"{bank} {closing_year} {MONTH_ABBR[closing_month]} and upload the correct statement for "
            f"{MONTH_ABBR[month_num] if 1 <= month_num <= 12 else month_num} {year}."
        )
    return str(closing_year), closing_month


def statement_period(bank: str, first_page_text: Optional[str], filename: str) -> StatementPeriod:
    """Return the period to date a statement's transactions with.

    The period printed in the PDF wins (see :func:`resolve_statement_period`); the month
    and year in the statement's key are the fallback. Raises ValueError when neither is
    available, rather than guessing a month and misdating every transaction.
    """
    filed = period_from_filename(filename)
    if filed is not None:
        year, month = resolve_statement_period(bank, first_page_text, filename, *filed)
        return StatementPeriod(int(year), month)

    closing = statement_closing_month(bank, first_page_text)
    if closing is None:
        raise ValueError(
            f"Cannot tell which month {filename} covers: its name has no month and year "
            f"(expected <bank>-<mon>-<yyyy>.pdf) and the PDF shows no statement period."
        )
    return StatementPeriod(*closing)
