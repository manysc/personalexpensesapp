"""ExpenseDbPersistence against a real PostgreSQL (15 or newer, for NULLS NOT DISTINCT).

Skipped unless TEST_DATABASE_URL points at a server where the user may create databases,
e.g. the docker-compose one: ``postgresql://postgres:<password>@localhost:5432/postgres``.
Each test runs in a throwaway database.
"""

import os
import uuid

import pandas as pd
import pytest
from sqlalchemy import create_engine, event, make_url, text

from personal_expenses_app.infrastructure import expense_db_persistence
from personal_expenses_app.infrastructure.expense_db_persistence import ExpenseDbPersistence

ADMIN_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not ADMIN_URL, reason="TEST_DATABASE_URL is not set")


@pytest.fixture
def engine(monkeypatch):
    name = f"expenses_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    engine = create_engine(make_url(ADMIN_URL).set(database=name))
    monkeypatch.setattr(expense_db_persistence, "_schema_ready", set())
    yield engine
    engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
    admin.dispose()


def expenses(*rows):
    """Build a DataFrame shaped like a categorized statement."""
    df = pd.DataFrame(rows, columns=["Date", "Bank", "Description", "Debit", "Credit", "Category"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df.astype({"Debit": "float64", "Credit": "float64"})


GYM = ("2026-10-02", "chase", "Acme Gym", 30.0, None, "Pharmacy/Health")
PAYROLL = ("2026-10-05", "chase", "Acme Payroll", None, 2500.0, "Income")


def scalar(engine, sql):
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


def natural_key_treats_nulls_as_equal(engine):
    return scalar(
        engine,
        "SELECT i.indnullsnotdistinct FROM pg_constraint c "
        "JOIN pg_index i ON i.indexrelid = c.conindid WHERE c.conname = 'uix_expense_natural_key'",
    )


def test_new_database_gets_a_natural_key_that_treats_nulls_as_equal(engine):
    ExpenseDbPersistence(engine=engine)

    assert natural_key_treats_nulls_as_equal(engine) is True


def test_saving_the_same_rows_again_updates_instead_of_inserting(engine):
    db = ExpenseDbPersistence(engine=engine)

    db.save_expenses(expenses(GYM, PAYROLL))
    with engine.begin() as conn:
        conn.execute(text("UPDATE all_expenses SET category = 'Mine', overridden = TRUE WHERE description = 'Acme Gym'"))
    db.save_expenses(expenses(GYM, PAYROLL))

    assert scalar(engine, "SELECT count(*) FROM all_expenses") == 2
    assert scalar(engine, "SELECT category FROM all_expenses WHERE description = 'Acme Gym'") == "Mine"


def test_identical_rows_in_one_batch_are_all_kept(engine):
    ExpenseDbPersistence(engine=engine).save_expenses(expenses(GYM, GYM))

    with engine.connect() as conn:
        descriptions = conn.execute(text("SELECT description FROM all_expenses ORDER BY id")).scalars().all()
    assert descriptions == ["Acme Gym", "Acme Gym (2)"]


def test_missing_amounts_are_stored_as_nan_like_the_existing_rows(engine):
    ExpenseDbPersistence(engine=engine).save_expenses(expenses(GYM))

    assert scalar(engine, "SELECT credit = 'NaN'::numeric FROM all_expenses") is True


def test_find_missing_returns_the_rows_that_are_not_stored(engine):
    db = ExpenseDbPersistence(engine=engine)
    statement = expenses(GYM, PAYROLL, GYM)
    assert len(db.find_missing(statement)) == 3

    db.save_expenses(statement)
    assert db.find_missing(statement).empty

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM all_expenses WHERE description IN ('Acme Payroll', 'Acme Gym (2)')"))
    missing = db.find_missing(statement)

    assert list(missing.index) == [1, 2]
    # As stored: the repeat of a row in the same statement carries a suffix.
    assert list(missing["Description"]) == ["Acme Payroll", "Acme Gym (2)"]


def test_stored_descriptions_number_the_repeats_and_are_idempotent():
    statement = expenses(GYM, PAYROLL, GYM, GYM)

    once = ExpenseDbPersistence.with_stored_descriptions(statement)

    assert list(once["Description"]) == ["Acme Gym", "Acme Payroll", "Acme Gym (2)", "Acme Gym (3)"]
    assert ExpenseDbPersistence.with_stored_descriptions(once).equals(once)
    assert list(statement["Description"]) == ["Acme Gym", "Acme Payroll", "Acme Gym", "Acme Gym"]


def test_find_missing_matches_manual_rows_stored_with_null(engine):
    db = ExpenseDbPersistence(engine=engine)
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO all_expenses (date, bank, description, debit, credit) "
            "VALUES ('2026-10-02 00:00:00', 'chase', 'Acme Gym', 30.00, NULL)"
        ))

    assert db.find_missing(expenses(GYM)).empty


def test_schema_is_checked_once_per_process(engine):
    statements = []
    event.listen(engine, "before_cursor_execute", lambda *args: statements.append(args[2]))

    ExpenseDbPersistence(engine=engine)
    first = len(statements)
    ExpenseDbPersistence(engine=engine)

    assert first > 0
    assert len(statements) == first


def test_healthy_database_is_left_alone(engine):
    ExpenseDbPersistence(engine=engine).save_expenses(expenses(GYM, PAYROLL))
    constraint = scalar(engine, "SELECT oid FROM pg_constraint WHERE conname = 'uix_expense_natural_key'")
    expense_db_persistence._schema_ready.clear()

    ExpenseDbPersistence(engine=engine)

    assert scalar(engine, "SELECT oid FROM pg_constraint WHERE conname = 'uix_expense_natural_key'") == constraint
    assert scalar(engine, "SELECT count(*) FROM all_expenses") == 2


def test_legacy_database_is_migrated(engine):
    # As created by an early version: narrow date, no "overridden", and a key that lets
    # rows with a NULL debit or credit be duplicated.
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE all_expenses ("
            "  id SERIAL PRIMARY KEY, date VARCHAR(10) NOT NULL, bank VARCHAR(50) NOT NULL,"
            "  description VARCHAR(500) NOT NULL, debit NUMERIC(12, 2), credit NUMERIC(12, 2),"
            "  category VARCHAR(100), comments VARCHAR(2000),"
            "  CONSTRAINT uix_expense_natural_key UNIQUE (date, bank, description, debit, credit))"
        ))
        for category in ("Old", "Older", "Newest"):
            conn.execute(text(
                "INSERT INTO all_expenses (date, bank, description, debit, credit, category) "
                "VALUES ('2026-10-02', 'chase', 'Acme Gym', 30.00, NULL, :category)"
            ), {"category": category})
        conn.execute(text(
            "INSERT INTO all_expenses (date, bank, description, debit, credit, category) "
            "VALUES ('2026-10-05', 'chase', 'Acme Payroll', NULL, 2500.00, 'Income')"
        ))

    ExpenseDbPersistence(engine=engine)

    assert natural_key_treats_nulls_as_equal(engine) is True
    assert scalar(engine, "SELECT count(*) FROM all_expenses") == 2
    assert scalar(engine, "SELECT category FROM all_expenses WHERE description = 'Acme Gym'") == "Newest"
    assert scalar(engine, "SELECT overridden FROM all_expenses WHERE description = 'Acme Gym'") is False
    assert scalar(
        engine,
        "SELECT character_maximum_length FROM information_schema.columns "
        "WHERE table_name = 'all_expenses' AND column_name = 'date'",
    ) == 20


def test_connection_string_from_the_environment(engine, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", engine.url.render_as_string(hide_password=False))

    db = ExpenseDbPersistence()

    assert db._engine.url == engine.url
    db._engine.dispose()


def test_missing_connection_string_is_an_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError, match="DATABASE_URL"):
        ExpenseDbPersistence()
