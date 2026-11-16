"""Statement follow-ups stored as dashboard action items, against a real PostgreSQL.

Skipped unless TEST_DATABASE_URL is set; see test_expense_db_persistence.py.
"""

import os
import uuid

import pytest
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import Session

from personal_expenses_app.infrastructure.statement_reconciliation import (
    STATEMENT_NOT_STORED,
    STATEMENT_UNVERIFIED,
    FollowUp,
)

ADMIN_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not ADMIN_URL, reason="TEST_DATABASE_URL is not set")

JAN = "resources/chase/2026/chase-jan-2026.pdf"
FEB = "resources/chase/2026/chase-feb-2026.pdf"
FEES_MISSING = FollowUp(STATEMENT_NOT_STORED, "aaa", "2 transaction(s) on chase-jan-2026.pdf are not in the app")
FEE_MISSING = FollowUp(STATEMENT_NOT_STORED, "bbb", "1 transaction(s) on chase-jan-2026.pdf are not in the app")
DOES_NOT_ADD_UP = FollowUp(STATEMENT_UNVERIFIED, "ccc", "chase-jan-2026.pdf does not add up")


@pytest.fixture
def app(monkeypatch):
    name = f"expenses_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(ADMIN_URL).set(database=name)
    monkeypatch.setenv("DATABASE_URL", url.render_as_string(hide_password=False))

    from personal_expenses_app.api import app as app_module

    engine = create_engine(url)
    monkeypatch.setattr(app_module, "_get_engine", lambda: engine)
    app_module._Base.metadata.create_all(engine)
    app_module._run_migrations(engine)
    yield app_module
    engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
    admin.dispose()


def items(app):
    with app._get_engine().connect() as conn:
        return [
            tuple(row)
            for row in conn.execute(text("SELECT type, month, message, status FROM action_items ORDER BY id"))
        ]


def resolve_all(app):
    with app._get_engine().begin() as conn:
        conn.execute(text("UPDATE action_items SET status = 'resolved'"))


def test_problems_become_open_action_items(app):
    verdict = app._record_statement_follow_ups({JAN: [FEES_MISSING, DOES_NOT_ADD_UP], FEB: []})

    assert items(app) == [
        (STATEMENT_NOT_STORED, "2026-01", FEES_MISSING.message, "open"),
        (STATEMENT_UNVERIFIED, "2026-01", DOES_NOT_ADD_UP.message, "open"),
    ]
    assert verdict == (
        "WARNING: 1 of 2 statement(s) need follow-up: chase-jan-2026.pdf. See Action Items on the dashboard."
    )


def test_finding_the_same_problem_again_adds_nothing(app):
    app._record_statement_follow_ups({JAN: [FEES_MISSING]})
    app._record_statement_follow_ups({JAN: [FEES_MISSING]})

    assert len(items(app)) == 1


def test_a_fixed_problem_disappears(app):
    app._record_statement_follow_ups({JAN: [FEES_MISSING, DOES_NOT_ADD_UP]})

    verdict = app._record_statement_follow_ups({JAN: [], FEB: []})

    assert items(app) == []
    assert verdict == "All 2 statement(s) add up to their printed totals and are fully stored."


def test_a_resolved_problem_stays_resolved(app):
    app._record_statement_follow_ups({JAN: [FEES_MISSING]})
    resolve_all(app)

    app._record_statement_follow_ups({JAN: [FEES_MISSING]})
    app._record_statement_follow_ups({JAN: []})

    assert items(app) == [(STATEMENT_NOT_STORED, "2026-01", FEES_MISSING.message, "resolved")]


def test_a_changed_problem_replaces_the_open_item(app):
    app._record_statement_follow_ups({JAN: [FEES_MISSING]})

    app._record_statement_follow_ups({JAN: [FEE_MISSING]})

    assert items(app) == [(STATEMENT_NOT_STORED, "2026-01", FEE_MISSING.message, "open")]


def test_other_statements_and_action_items_are_left_alone(app):
    app._record_statement_follow_ups({FEB: [FollowUp(STATEMENT_NOT_STORED, "ddd", "feb")]})
    with app._get_engine().begin() as conn:
        conn.execute(text(
            "INSERT INTO action_items (action_key, type, month, message) "
            "VALUES ('rent_unpaid:1:2026-11', 'rent_unpaid', '2026-11', 'Rent unpaid')"
        ))

    app._record_statement_follow_ups({JAN: []})

    assert [item[2] for item in items(app)] == ["feb", "Rent unpaid"]


# --- Keeping a transaction out, and loading one ------------------------------

@pytest.fixture
def statement(app, monkeypatch):
    """Serve one Chase statement whose page text is fixed, and an empty database."""
    from personal_expenses_app.api import app as app_module

    pages = [
        "December 18, 2025 through January 19, 2026\n"
        "CHECKING SUMMARY\n"
        "Beginning Balance $10,000.00\n"
        "Electronic Withdrawals -50.00\n"
        "Other Withdrawals -7,000.00\n"
        "Ending Balance $2,950.00",
        "ELECTRONIC WITHDRAWALS\n"
        "01/05 Acme Gym $25.00\n"
        "01/06 Acme Gym $25.00\n"
        "Total Electronic Withdrawals $50.00\n"
        "OTHER WITHDRAWALS\n"
        "01/13 Withdrawal $7,000.00\n"
        "Total Other Withdrawals $7,000.00",
    ]
    monkeypatch.setattr(app_module.StatementBatch, "_page_texts_of", lambda self, key: pages)
    monkeypatch.setattr(app_module, "_load_category_keywords", lambda: None)
    return app_module


def stored(app):
    with app._get_engine().connect() as conn:
        return conn.execute(text("SELECT description, debit FROM all_expenses ORDER BY date")).all()


def open_items(app):
    with app._get_engine().connect() as conn:
        return conn.execute(
            text("SELECT id, type, message FROM action_items WHERE status = 'open' ORDER BY id")
        ).all()


def check(app):
    return app.reconcile_statements_and_notify("2026", bank="chase", month="jan")


@pytest.fixture
def uploaded(monkeypatch):
    from personal_expenses_app.infrastructure import s3_storage

    monkeypatch.setattr(s3_storage, "list_keys", lambda prefix="": [JAN])


def test_check_files_each_missing_transaction(statement, uploaded):
    (result,) = check(statement)

    assert result.adds_up is True
    assert len(result.missing) == 3 and not result.complete
    assert [item.type for item in open_items(statement)] == [STATEMENT_NOT_STORED] * 3


def test_load_adds_only_that_transaction(statement, uploaded):
    check(statement)
    withdrawal = next(item for item in open_items(statement) if "Withdrawal" in item.message)

    assert statement.load_missing_transactions(withdrawal.id).loaded == 1

    assert [row.description for row in stored(statement)] == ["Withdrawal"]
    assert len(open_items(statement)) == 2


def test_a_kept_out_transaction_is_not_reported_or_imported_again(statement, uploaded):
    check(statement)
    withdrawal = next(item for item in open_items(statement) if "Withdrawal" in item.message)
    statement.resolve_action_item(withdrawal.id, session=Session(statement._get_engine()))
    for item in open_items(statement):
        statement.load_missing_transactions(item.id)

    (result,) = check(statement)
    assert result.complete is True
    assert [row.description for row in result.kept_out] == ["Withdrawal"]

    # Importing the statement again does not bring it back.
    df, _ = statement.StatementBatch([JAN]).read("chase", JAN)
    to_store, kept_out = statement._split_kept_out(JAN, df)
    assert list(kept_out["Description"]) == ["Withdrawal"]
    assert list(to_store["Description"]) == ["Acme Gym", "Acme Gym"]


def test_many_missing_transactions_load_together(statement, uploaded, monkeypatch):
    from personal_expenses_app.infrastructure import statement_reconciliation

    monkeypatch.setattr(statement_reconciliation, "MAX_SEPARATE_FOLLOW_UPS", 2)
    check(statement)
    (item,) = open_items(statement)
    assert item.type == "statement_not_imported"

    assert statement.load_missing_transactions(item.id).loaded == 3
    assert open_items(statement) == []
