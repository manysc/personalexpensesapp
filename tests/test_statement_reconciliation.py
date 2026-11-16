import pandas as pd

from personal_expenses_app.infrastructure.statement_reconciliation import (
    STATEMENT_NOT_IMPORTED,
    STATEMENT_NOT_STORED,
    STATEMENT_UNVERIFIED,
    Reconciliation,
    StatementTotals,
    statement_follow_ups,
    transaction_fingerprint,
    unreadable_statement_follow_up,
)

KEY = "resources/citi/2026/citi-oct-2026.pdf"
READ = StatementTotals(debits=100.00, credits=40.00, debit_count=3, credit_count=1)


def test_matching_totals():
    reconciliation = Reconciliation(KEY, READ, StatementTotals(100.00, 40.00))

    assert reconciliation.matches is True
    assert reconciliation.differences == []
    assert reconciliation.describe() == (
        "citi-oct-2026.pdf: 4 transaction(s) add up to the statement's totals (debits 100.00, credits 40.00)."
    )


def test_float_noise_is_not_a_difference():
    read = StatementTotals(0.1 + 0.2, 40.00, 2, 1)

    assert Reconciliation(KEY, read, StatementTotals(0.30, 40.00)).matches is True


def test_missing_and_extra_amounts_are_named():
    reconciliation = Reconciliation(KEY, READ, StatementTotals(150.00, 30.00))

    assert reconciliation.matches is False
    assert reconciliation.differences == [
        "debits read 100.00, statement 150.00 (50.00 missing)",
        "credits read 40.00, statement 30.00 (10.00 too much)",
    ]
    assert reconciliation.describe().startswith("WARNING: citi-oct-2026.pdf does not add up")


def test_counts_are_compared_when_the_statement_prints_them():
    reconciliation = Reconciliation(KEY, READ, StatementTotals(100.00, 40.00, debit_count=4, credit_count=1))

    assert reconciliation.differences == ["3 debits read, statement lists 4"]


def test_no_printed_totals_is_neither_a_match_nor_a_mismatch():
    reconciliation = Reconciliation(KEY, READ, None)

    assert reconciliation.matches is None
    assert reconciliation.describe().startswith("WARNING: citi-oct-2026.pdf: read 4 transaction(s)")


def test_currency_and_note_are_shown():
    reconciliation = Reconciliation(KEY, READ, StatementTotals(100.00, 40.00), currency="MXN", note="(A note.)")

    assert reconciliation.describe().endswith("(debits 100.00, credits 40.00 MXN). (A note.)")


def not_stored(*rows):
    df = pd.DataFrame(rows, columns=["Date", "Description", "Debit", "Credit"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df.astype({"Debit": "float64", "Credit": "float64"})


NOTHING = not_stored()


def test_a_complete_statement_needs_no_follow_up():
    assert statement_follow_ups(Reconciliation(KEY, READ, StatementTotals(100.00, 40.00)), NOTHING) == []


def test_a_statement_that_does_not_add_up_needs_follow_up():
    (follow_up,) = statement_follow_ups(Reconciliation(KEY, READ, StatementTotals(150.00, 40.00)), NOTHING)

    assert follow_up.type == STATEMENT_UNVERIFIED
    assert follow_up.message == (
        "citi-oct-2026.pdf does not add up to the totals printed on it: "
        "debits read 100.00, statement 150.00 (50.00 missing). "
        "Some transactions were missed or misread: compare the statement with the app."
    )


def test_a_statement_without_totals_needs_follow_up():
    (follow_up,) = statement_follow_ups(Reconciliation(KEY, READ, None), NOTHING)

    assert follow_up.type == STATEMENT_UNVERIFIED
    assert follow_up.message.startswith("citi-oct-2026.pdf could not be checked")


def test_each_transaction_missing_from_the_app_gets_a_follow_up():
    missing = not_stored(
        ("2026-01-13", "Withdrawal", 7000.0, None),
        ("2026-01-15", "Refund", None, 12.5),
    )

    follow_ups = statement_follow_ups(Reconciliation(KEY, READ, StatementTotals(100.00, 40.00)), missing)

    assert [(f.type, f.message) for f in follow_ups] == [
        (
            STATEMENT_NOT_STORED,
            "citi-oct-2026.pdf lists Withdrawal (2026-01-13, $7,000.00), which is not in the app. "
            "Load it, or keep it out if it was removed on purpose.",
        ),
        (
            STATEMENT_NOT_STORED,
            "citi-oct-2026.pdf lists Refund (2026-01-15, credit $12.50), which is not in the app. "
            "Load it, or keep it out if it was removed on purpose.",
        ),
    ]
    assert [f.fingerprint for f in follow_ups] == [transaction_fingerprint(row) for row in missing.itertuples()]


def test_many_missing_transactions_get_one_follow_up():
    missing = not_stored(*[(f"2026-01-{day:02d}", "X" * 150, 1.0, None) for day in range(1, 9)])

    (follow_up,) = statement_follow_ups(Reconciliation(KEY, READ, StatementTotals(100.00, 40.00)), missing)

    assert follow_up.type == STATEMENT_NOT_IMPORTED
    assert follow_up.message.startswith("8 transactions on citi-oct-2026.pdf are not in the app, e.g. ")
    assert len(follow_up.message) <= 500


def test_a_transaction_keeps_its_fingerprint():
    fee = not_stored(("2026-01-05", "Wire Fee", 25.0, None))
    fee_again = not_stored(("2026-01-05", "Wire Fee", 25.0, None), ("2026-01-13", "Withdrawal", 7000.0, None))
    other_fee = not_stored(("2026-01-06", "Wire Fee", 25.0, None))

    def fingerprint(df, position=0):
        return transaction_fingerprint(list(df.itertuples())[position])

    assert fingerprint(fee) == fingerprint(fee_again)
    assert fingerprint(fee) != fingerprint(other_fee)
    assert fingerprint(fee) != fingerprint(fee_again, 1)


def test_an_unreadable_statement_needs_follow_up():
    follow_up = unreadable_statement_follow_up(KEY, ValueError("No transactions found in PDF: " + KEY))

    assert follow_up.type == STATEMENT_UNVERIFIED
    assert follow_up.message == f"citi-oct-2026.pdf could not be imported: No transactions found in PDF: {KEY}"
