from personal_expenses_app.infrastructure.statement_period import (
    resolve_statement_period,
    statement_closing_month,
)

CITI = "OCTOBER STATEMENT Costco Cash Back Rewards Summary\nBilling Period: 09/09/26-10/08/26\nNew balance as of 10/08/26"
CITI_JAN = "Billing Period: 12/09/25-01/08/26"
CHASE = "22000000010202122310\nSeptember 18, 2026throughOctober 19, 2026\n"
CHASE_SPACED = "December 18, 2025 through January 19, 2026"
WELLS = "October 26, 2026 Page 1 of 5\nWells Fargo Everyday Checking"


def test_closing_month_per_bank():
    assert statement_closing_month("citi", CITI) == (2026, 10)
    assert statement_closing_month("citi", CITI_JAN) == (2026, 1)
    assert statement_closing_month("chase", CHASE) == (2026, 10)
    assert statement_closing_month("chase", CHASE_SPACED) == (2026, 1)
    assert statement_closing_month("wellsfargo", WELLS) == (2026, 10)


def test_unknown_layout_or_bank_returns_none():
    assert statement_closing_month("citi", "no period here") is None
    assert statement_closing_month("banamex", CITI) is None
    assert statement_closing_month("citi", None) is None


def test_matching_filename_is_kept_without_warning(capsys):
    assert resolve_statement_period("citi", CITI, "resources/citi/2026/citi-oct-2026.pdf", "2026", 10) == ("2026", 10)
    assert capsys.readouterr().out == ""


def test_mislabeled_statement_uses_pdf_period_and_warns(capsys):
    # Regression: the October statement uploaded as September dated Oct 1-7 charges as 2025.
    year, month = resolve_statement_period("citi", CITI, "resources/citi/2026/citi-sep-2026.pdf", "2026", 9)
    assert (year, month) == ("2026", 10)
    out = capsys.readouterr().out
    assert "WARNING" in out and "oct 2026" in out and "sep 2026" in out


def test_falls_back_to_filename_when_period_missing(capsys):
    assert resolve_statement_period("citi", "", "citi-sep-2026.pdf", "2026", 9) == ("2026", 9)
    assert capsys.readouterr().out == ""
