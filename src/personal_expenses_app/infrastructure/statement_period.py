"""Read a statement's closing month from the PDF itself instead of trusting the filename.

Loaders date transactions as MM/DD plus a year, and treat any transaction month later
than the statement's month as belonging to the previous year (December charges on a
January statement). Both the year and that month used to come from the filename only,
so a statement filed under the wrong month (e.g. the October Citi statement saved as
"citi-sep-2026.pdf") silently shifted its October charges back a year.
"""

from __future__ import annotations

import re
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
