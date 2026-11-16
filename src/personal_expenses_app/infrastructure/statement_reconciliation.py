"""Checking the transactions read from a statement against the totals the bank prints on it.

Every statement states how much was charged and credited in its period. If the
transactions the parser read do not add up to those figures, some were missed or misread,
and the import says so instead of silently loading an incomplete month.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import NamedTuple, Optional

import pandas as pd


class StatementTotals(NamedTuple):
    """Debit and credit totals, in the statement's own currency."""

    debits: float
    credits: float
    debit_count: Optional[int] = None
    credit_count: Optional[int] = None


@dataclass(frozen=True)
class Reconciliation:
    """How the transactions read from one statement compare with its printed totals."""

    statement: str  # The statement's S3 key.
    read: StatementTotals
    printed: Optional[StatementTotals]  # None when no totals were found on the statement.
    currency: str = "USD"
    note: str = ""

    @property
    def matches(self) -> Optional[bool]:
        """True or False once compared; None when there were no printed totals to compare with."""
        if self.printed is None:
            return None
        return not self.differences

    @property
    def differences(self) -> list[str]:
        """One phrase per total (or count) that disagrees with the statement."""
        if self.printed is None:
            return []
        found = []
        for label, read, printed in (
            ("debits", self.read.debits, self.printed.debits),
            ("credits", self.read.credits, self.printed.credits),
        ):
            gap = round(printed - read, 2)
            if gap:
                direction = "missing" if gap > 0 else "too much"
                found.append(f"{label} read {read:,.2f}, statement {printed:,.2f} ({abs(gap):,.2f} {direction})")
        for label, read, printed in (
            ("debits", self.read.debit_count, self.printed.debit_count),
            ("credits", self.read.credit_count, self.printed.credit_count),
        ):
            if printed is not None and read != printed:
                found.append(f"{read} {label} read, statement lists {printed}")
        return found

    def describe(self) -> str:
        """Return the line shown in the import log."""
        name = self.statement.rsplit("/", 1)[-1]
        count = (self.read.debit_count or 0) + (self.read.credit_count or 0)
        totals = f"debits {self.read.debits:,.2f}, credits {self.read.credits:,.2f}"
        if self.currency != "USD":
            totals += f" {self.currency}"

        if self.printed is None:
            text = (
                f"WARNING: {name}: read {count} transaction(s) ({totals}) but found no totals "
                f"on the statement to check them against."
            )
        elif self.differences:
            text = (
                f"WARNING: {name} does not add up to the statement's totals: "
                f"{'; '.join(self.differences)}. Transactions are missing or misread."
            )
        else:
            text = f"{name}: {count} transaction(s) add up to the statement's totals ({totals})."
        return f"{text} {self.note}".rstrip()


# Kinds of follow-up, stored as action item types.
STATEMENT_UNVERIFIED = "statement_unverified"  # Does not add up, has no totals, or could not be read.
STATEMENT_NOT_STORED = "statement_not_stored"  # One transaction on the statement is not in the app.
STATEMENT_NOT_IMPORTED = "statement_not_imported"  # Many are not: likely never imported.
FOLLOW_UP_TYPES = (STATEMENT_UNVERIFIED, STATEMENT_NOT_STORED, STATEMENT_NOT_IMPORTED)

_MAX_MESSAGE_LENGTH = 500  # action_items.message is VARCHAR(500).
# Up to this many missing transactions get one follow-up each; more get one for the statement.
MAX_SEPARATE_FOLLOW_UPS = 5
_ROWS_LISTED = 3


class FollowUp(NamedTuple):
    """A problem with one statement, for a person to look into."""

    type: str
    # Identifies this exact problem: the same problem found again gets the same
    # fingerprint, a different one a new one. For STATEMENT_NOT_STORED it is the
    # transaction's fingerprint.
    fingerprint: str
    message: str


def _fingerprint(*parts: object) -> str:
    return hashlib.sha1(repr(parts).encode()).hexdigest()[:12]


def transaction_fingerprint(row) -> str:
    """Identify one transaction of a statement by what is stored for it.

    ``row`` is a row (from ``itertuples``) of a statement's DataFrame whose descriptions
    are as stored (see ExpenseDbPersistence.with_stored_descriptions).
    """

    def cents(amount) -> Optional[int]:
        return None if pd.isna(amount) else round(float(amount) * 100)

    return _fingerprint(str(row.Date), row.Description, cents(row.Debit), cents(row.Credit))


def _name(statement: str) -> str:
    return statement.rsplit("/", 1)[-1]


def _shorten(message: str) -> str:
    if len(message) <= _MAX_MESSAGE_LENGTH:
        return message
    return message[: _MAX_MESSAGE_LENGTH - 1].rstrip() + "…"


def _describe_row(row) -> str:
    amount = f"${row.Debit:,.2f}" if pd.notna(row.Debit) else f"credit ${row.Credit:,.2f}"
    date = row.Date.strftime("%Y-%m-%d") if pd.notna(row.Date) else "no date"
    return f"{row.Description} ({date}, {amount})"


def statement_follow_ups(reconciliation: Reconciliation, not_stored: pd.DataFrame) -> list[FollowUp]:
    """Return what needs a person's attention after reading a statement and checking the database.

    ``not_stored`` holds the statement's transactions that are not in the database, as
    ExpenseDbPersistence.find_missing returns them, leaving out those a person chose to
    keep out.
    """
    name = _name(reconciliation.statement)
    follow_ups = []

    if reconciliation.printed is None:
        follow_ups.append(FollowUp(
            STATEMENT_UNVERIFIED,
            _fingerprint("no totals", reconciliation.read),
            f"{name} could not be checked: no totals were found on the statement. "
            f"Compare its transactions in the app with the statement.",
        ))
    elif reconciliation.differences:
        follow_ups.append(FollowUp(
            STATEMENT_UNVERIFIED,
            _fingerprint(reconciliation.differences),
            _shorten(
                f"{name} does not add up to the totals printed on it: "
                f"{'; '.join(reconciliation.differences)}. Some transactions were missed or "
                f"misread: compare the statement with the app."
            ),
        ))

    rows = list(not_stored.itertuples())
    if len(rows) > MAX_SEPARATE_FOLLOW_UPS:
        listed = ", ".join(_describe_row(row) for row in rows[:_ROWS_LISTED])
        follow_ups.append(FollowUp(
            STATEMENT_NOT_IMPORTED,
            _fingerprint(sorted(transaction_fingerprint(row) for row in rows)),
            _shorten(
                f"{len(rows)} transactions on {name} are not in the app, e.g. {listed}. "
                f"Load them all, or dismiss this if that is intended."
            ),
        ))
    else:
        follow_ups.extend(
            FollowUp(
                STATEMENT_NOT_STORED,
                transaction_fingerprint(row),
                _shorten(
                    f"{name} lists {_describe_row(row)}, which is not in the app. "
                    f"Load it, or keep it out if it was removed on purpose."
                ),
            )
            for row in rows
        )
    return follow_ups


def unreadable_statement_follow_up(statement: str, error: Exception) -> FollowUp:
    """Return the follow-up for a statement whose transactions could not be read at all."""
    return FollowUp(
        STATEMENT_UNVERIFIED,
        _fingerprint("unreadable", str(error)),
        _shorten(f"{_name(statement)} could not be imported: {error}"),
    )
