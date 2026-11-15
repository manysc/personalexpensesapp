"""Bank statement parsers, exercised on made-up page text shaped like each bank's PDFs."""

import pandas as pd
import pytest

from personal_expenses_app.infrastructure import statement_loader
from personal_expenses_app.infrastructure.banamex_file_loader import BanamexFileLoader
from personal_expenses_app.infrastructure.chase_file_loader import ChaseFileLoader
from personal_expenses_app.infrastructure.citi_file_loader import CARDHOLDER_NAMES, CitiFileLoader
from personal_expenses_app.infrastructure.statement_loader import COLUMNS
from personal_expenses_app.infrastructure.wellsfargo_file_loader import WellsfargoFileLoader


def rows(df: pd.DataFrame) -> list[tuple]:
    """Return ``(date, description, debit, credit)`` per row, with None for a missing amount."""
    return [
        (
            row.Date.strftime("%Y-%m-%d"),
            row.Description,
            None if pd.isna(row.Debit) else row.Debit,
            None if pd.isna(row.Credit) else row.Credit,
        )
        for row in df.itertuples()
    ]


# ---------------------------------------------------------------------------
# Chase
# ---------------------------------------------------------------------------

CHASE_KEY = "resources/chase/2026/chase-oct-2026.pdf"
CHASE_PAGES = [
    "September 18, 2026 through October 19, 2026\n"
    "CHECKING SUMMARY\n"
    "10/01 Listed Outside Any Section $9.99",
    "DEPOSITS AND ADDITIONS\n"
    "DATE DESCRIPTION AMOUNT\n"
    "09/23 Zelle Payment From Jane Doe Abc123 $600.00\n"
    "10/05 Acme Corp Payroll 2,500.00\n"
    "Total Deposits and Additions $3,100.00\n"
    "ELECTRONIC WITHDRAWALS\n"
    "DATE DESCRIPTION AMOUNT\n"
    "10/02 Acme Mortgage Payment $1,200.50",
    "",
    "10/08 Acme Water Bill $45.10\n"
    "Total Electronic Withdrawals $1,245.60\n"
    "OTHER WITHDRAWALS\n"
    "10/12 Cashier Check $80.00\n"
    "Total Other Withdrawals $80.00",
]


def test_chase_reads_credits_and_debits_by_section():
    df = ChaseFileLoader().parse_statement(CHASE_KEY, CHASE_PAGES)

    assert list(df.columns) == COLUMNS
    assert set(df["Bank"]) == {"chase"}
    assert rows(df) == [
        ("2026-09-23", "Zelle Payment From Jane Doe Abc123", None, 600.00),
        ("2026-10-02", "Acme Mortgage Payment", 1200.50, None),
        ("2026-10-05", "Acme Corp Payroll", None, 2500.00),
        ("2026-10-08", "Acme Water Bill", 45.10, None),
        ("2026-10-12", "Cashier Check", 80.00, None),
    ]


def test_chase_recovers_transaction_garbled_into_end_marker():
    pages = [
        "September 18, 2026 through October 19, 2026",
        "DEPOSITS AND ADDITIONS\n"
        "*end*deposi1ts and additio0ns /07 Zelle Payment From John Roe 1,325.00\n"
        "10/09 After The Section Ended $1.00",
    ]

    df = ChaseFileLoader().parse_statement(CHASE_KEY, pages)

    # The month is unreadable, so the statement's closing month is used.
    assert rows(df) == [("2026-10-07", "Zelle Payment From John Roe", None, 1325.00)]


def test_months_after_the_closing_month_belong_to_the_previous_year():
    pages = [
        "December 18, 2025 through January 19, 2026",
        "ELECTRONIC WITHDRAWALS\n12/23 Acme Gift Shop $20.00\n01/05 Acme Gym $30.00",
    ]

    df = ChaseFileLoader().parse_statement("resources/chase/2026/chase-jan-2026.pdf", pages)

    assert rows(df) == [
        ("2025-12-23", "Acme Gift Shop", 20.00, None),
        ("2026-01-05", "Acme Gym", 30.00, None),
    ]


def test_key_without_month_and_year_is_dated_from_the_pdf():
    df = ChaseFileLoader().parse_statement("resources/chase/statement.pdf", CHASE_PAGES)

    assert df["Date"].min() == pd.Timestamp("2026-09-23")


def test_undatable_statement_is_an_error():
    pages = ["No statement period here", "ELECTRONIC WITHDRAWALS\n10/02 Acme Gym $30.00"]

    with pytest.raises(ValueError, match="Cannot tell which month resources/chase/statement.pdf covers"):
        ChaseFileLoader().parse_statement("resources/chase/statement.pdf", pages)


def test_statement_without_transactions_is_an_error():
    with pytest.raises(ValueError, match="No transactions found in PDF: " + CHASE_KEY):
        ChaseFileLoader().parse_statement(CHASE_KEY, ["Nothing to see here"])


# ---------------------------------------------------------------------------
# Wells Fargo
# ---------------------------------------------------------------------------

WELLS_PAGES = [
    "October 26, 2026 Page 1 of 5\nWells Fargo Everyday Checking\n10/1 Not In The Table 1.00",
    "Transaction history\n"
    "Date Number Description Additions Subtractions balance\n"
    "10/2 Acme Mortgage 261002 P12739652 798.44 3,157.01\n"
    "10/5 Recurring Transfer From Acme Bank Ref #Op0Abc 500.00\n"
    "10/9 Online Transfer To Doe J Everyday Checking\n"
    "Xxxxxx1234 Ref #Ib0Xyz On 10/09/26 250.00 3,407.01\n"
    "10/15 Interest Payment 0.03 3,407.04\n"
    "Totals $500.03 $1,048.44\n"
    "10/20 After The Totals 5.00",
]


def test_wellsfargo_reads_transaction_history():
    df = WellsfargoFileLoader().parse_statement("resources/wellsfargo/2026/wellsfargo-oct-2026.pdf", WELLS_PAGES)

    assert set(df["Bank"]) == {"wellsfargo"}
    assert rows(df) == [
        # With two amounts on the row, the last one is the running balance.
        ("2026-10-02", "Acme Mortgage 261002 P12739652", 798.44, None),
        ("2026-10-05", "Recurring Transfer From Acme Bank Ref #Op0Abc", None, 500.00),
        # A wrapped description is joined with the line carrying its amounts.
        ("2026-10-09", "Online Transfer To Doe J Everyday Checking Xxxxxx1234 Ref #Ib0Xyz On 10/09/26", 250.00, None),
        ("2026-10-15", "Interest Payment", None, 0.03),
    ]


# ---------------------------------------------------------------------------
# Banamex
# ---------------------------------------------------------------------------

BANAMEX_KEY = "resources/banamex/2026/banamex-mar-2026.pdf"
BANAMEX_PAGES = [
    "ESTADO DE CUENTA\n"
    "Detalle de Operaciones\n"
    "FECHA CONCEPTO RETIROS DEPOSITOS SALDO\n"
    "01 MAR SALDO ANTERIOR 10,000.00\n"
    "05 MAR PAGO RECIBIDO DE ACME POR ORDEN DE JOHN ROE\n"
    "SUC 0123 CAJA 04\n"
    "HORA 12:30 1,850.00 11,850.00\n"
    "09 MAR COMPRA TIENDA EJEMPLO\n"
    "SUCURSAL CENTRO\n"
    "AUT 123456 370.00 11,480.00\n"
    "Página 1 de 3",
    "FECHA CONCEPTO RETIROS DEPOSITOS SALDO\n"
    "12 MAR DEVOLUCION TIENDA 185.00 11,665.00\n"
    "Resumen Operaciones\n"
    "15 MAR FUERA DE LA TABLA 1.00 2.00",
]


def test_banamex_reads_multi_line_transactions_in_dollars():
    df = BanamexFileLoader().parse_statement(BANAMEX_KEY, BANAMEX_PAGES)

    assert set(df["Bank"]) == {"banamex"}
    assert rows(df) == [
        # 1,850 pesos; a credit by its description.
        ("2026-03-05", "PAGO RECIBIDO DE ACME POR ORDEN DE JOHN ROE", None, 100.00),
        # Metadata lines (SUC, AUT...) give amounts but no description; the balance went down.
        ("2026-03-09", "COMPRA TIENDA EJEMPLO SUCURSAL CENTRO", 20.00, None),
        # No credit keyword, but the balance went up.
        ("2026-03-12", "DEVOLUCION TIENDA", None, 10.00),
    ]


def test_banamex_reads_amounts_whose_cents_were_split():
    pages = [
        "FECHA CONCEPTO RETIROS DEPOSITOS SALDO\n"
        "20 MAR RETIRO CAJERO\n"
        "REFERENCIA EJEMPLO 1,850.0 0 9,000.0 0"
    ]

    df = BanamexFileLoader().parse_statement(BANAMEX_KEY, pages)

    assert rows(df) == [("2026-03-20", "RETIRO CAJERO REFERENCIA EJEMPLO", 100.00, None)]


def test_banamex_statement_without_movements_is_empty():
    df = BanamexFileLoader().parse_statement(BANAMEX_KEY, ["ESTADO DE CUENTA\nSin movimientos"])

    assert df.empty
    assert list(df.columns) == COLUMNS


# ---------------------------------------------------------------------------
# Citi
# ---------------------------------------------------------------------------

CITI_KEY = "resources/citi/2026/citi-oct-2026.pdf"
CITI_PAGES = [
    "OCTOBER STATEMENT\nBilling Period: 09/09/26-10/08/26\nNew balance as of 10/08/26",
    "Payments, Credits and Adjustments\n"
    "Sale Post\n"
    "Date Date Description Amount\n"
    "10/03 AUTOPAY 999990000012345RAUTOPAY AUTO-PMT -$1,200.00\n"
    f"{CARDHOLDER_NAMES[0]}\n"
    "Standard Purchases\n"
    "09/10 09/11 CORNER DINER #12 TUCSON AZ $11.50\n"
    "ACME AIRPORT SHOP - TERMINAL\n"
    "09/12 09/12 $23.74\n"
    "09/15 09/16 BOOK STORE REFUND TUCSON AZ -$8.25\n"
    "09/20 TACOS EL EJEMPLO HERMOSILLO SOMX\n"
    "1,250.00 MEXICAN PESO $68.00\n"
    "10/01 10/02 GRAND EXAMPLE LODGE TUCSON AZ\n"
    "PHONE NUMBER: 5205550100\n"
    "FOLIO NUMBER: 778899\n"
    "ARRIVE: 10/01/26 DEPART: 10/03/26\n"
    "$412.36",
    f"{CARDHOLDER_NAMES[0]}\n"
    "Standard Purchases cont'd\n"
    "STATE TAX OFFICE E COM HERMOSILLO\n"
    "10/04 Total Earned: $63.02\n"
    "SOMX\n"
    "925.00 MEXICAN PESO $50.00\n"
    "10/05 10/05 GAS STOP 1499 TUCSON AZ $32.10 Total Earned: $61.68\n"
    "Interest Charged\n"
    "10/06 10/06 INTEREST CHARGE ON PURCHASES $5.00",
]


def test_citi_reads_single_and_multi_line_transactions():
    df = CitiFileLoader().parse_statement(CITI_KEY, CITI_PAGES)

    assert set(df["Bank"]) == {"citi"}
    assert rows(df) == [
        ("2026-09-10", "CORNER DINER #12 TUCSON AZ", 11.50, None),
        # Description on the line above the dates and amount.
        ("2026-09-12", "ACME AIRPORT SHOP - TERMINAL", 23.74, None),
        # A negative amount is a credit.
        ("2026-09-15", "BOOK STORE REFUND TUCSON AZ", None, 8.25),
        # Foreign purchase: the dollar amount is on the exchange-rate line.
        ("2026-09-20", "TACOS EL EJEMPLO HERMOSILLO SOMX", 68.00, None),
        # Lodging: folio lines sit between the description and a bare amount.
        ("2026-10-01", "GRAND EXAMPLE LODGE TUCSON AZ", 412.36, None),
        ("2026-10-03", "AUTOPAY 999990000012345RAUTOPAY AUTO-PMT", None, 1200.00),
        # Description first, then its date beside text from the rewards summary.
        ("2026-10-04", "STATE TAX OFFICE E COM HERMOSILLO", 50.00, None),
        # Rewards text appended after the amount is ignored.
        ("2026-10-05", "GAS STOP 1499 TUCSON AZ", 32.10, None),
    ]


def test_citi_yearly_totals_end_the_transactions():
    pages = [
        "Billing Period: 09/09/26-10/08/26",
        "Standard Purchases\n"
        "09/10 09/11 CORNER DINER #12 TUCSON AZ $11.50\n"
        "2026 totals year-to-date\n"
        "09/30 09/30 NOT A TRANSACTION $0.00",
    ]

    df = CitiFileLoader().parse_statement(CITI_KEY, pages)

    assert rows(df) == [("2026-09-10", "CORNER DINER #12 TUCSON AZ", 11.50, None)]


def test_citi_dates_december_purchases_on_a_january_statement_in_the_previous_year():
    pages = [
        "Billing Period: 12/09/25-01/08/26",
        "Standard Purchases\n12/20 12/21 ACME TOY SHOP TUCSON AZ $5.00\n01/03 01/04 ACME BAKERY TUCSON AZ $6.00",
    ]

    df = CitiFileLoader().parse_statement("resources/citi/2026/citi-jan-2026.pdf", pages)

    assert rows(df) == [
        ("2025-12-20", "ACME TOY SHOP TUCSON AZ", 5.00, None),
        ("2026-01-03", "ACME BAKERY TUCSON AZ", 6.00, None),
    ]


# ---------------------------------------------------------------------------
# Loading from storage
# ---------------------------------------------------------------------------


@pytest.fixture
def stored_statements(monkeypatch):
    """Serve page texts as if they were PDFs in S3: ``{key: pages}``."""
    statements = {CHASE_KEY: CHASE_PAGES}

    def get_object_bytes(key):
        if key not in statements:
            raise FileNotFoundError(key)
        return key.encode()

    monkeypatch.setattr(statement_loader, "get_object_bytes", get_object_bytes)
    monkeypatch.setattr(statement_loader, "extract_page_texts", lambda pdf: statements[pdf.decode()])
    return statements


def test_load_expenses_and_credits_reads_the_stored_pdf(stored_statements):
    loader = ChaseFileLoader()

    assert len(loader.load_expenses_and_credits(CHASE_KEY)) == 5
    assert list(loader.load_expenses(CHASE_KEY)["Description"]) == [
        "Acme Mortgage Payment", "Acme Water Bill", "Cashier Check",
    ]
    assert list(loader.load_credits(CHASE_KEY)["Description"]) == [
        "Zelle Payment From Jane Doe Abc123", "Acme Corp Payroll",
    ]


def test_load_and_label_multiple_files_skips_missing_statements(stored_statements, capsys):
    labeled = ChaseFileLoader().load_and_label_multiple_files([CHASE_KEY, "resources/chase/2026/chase-nov-2026.pdf"])

    assert len(labeled) == 5
    assert "Category" in labeled.columns
    assert "Warning: File not found: resources/chase/2026/chase-nov-2026.pdf" in capsys.readouterr().out


def test_load_and_label_multiple_files_needs_at_least_one_statement(stored_statements):
    with pytest.raises(ValueError, match="No valid expense files found"):
        ChaseFileLoader().load_and_label_multiple_files(["resources/chase/2026/chase-nov-2026.pdf"])
