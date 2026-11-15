import pandas as pd
import pytest

from personal_expenses_app.infrastructure import statement_import, statement_loader
from personal_expenses_app.infrastructure.statement_import import LOADERS, StatementBatch, statement_key

CHASE_KEY = "resources/chase/2026/chase-oct-2026.pdf"
CHASE_PAGES = ["September 18, 2026 through October 19, 2026", "ELECTRONIC WITHDRAWALS\n10/02 Acme Gym $30.00"]


def test_statement_key():
    assert statement_key("chase", "2026", "oct") == CHASE_KEY


def test_loaders_are_registered_by_bank_in_load_order():
    assert list(LOADERS) == ["citi", "wellsfargo", "chase", "banamex"]
    assert all(loader.bank == bank for bank, loader in LOADERS.items())


@pytest.mark.parametrize(
    "statements, configured, cpus, expected",
    [
        (4, None, 8, 1),  # One month's statements: not worth starting processes.
        (5, None, 8, 5),
        (48, None, 8, 8),
        (48, "3", 8, 3),
        (48, "1", 8, 1),
    ],
)
def test_worker_count(monkeypatch, statements, configured, cpus, expected):
    monkeypatch.setattr(statement_import.os, "cpu_count", lambda: cpus)
    if configured is None:
        monkeypatch.delenv(statement_import.WORKERS_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(statement_import.WORKERS_ENV_VAR, configured)

    assert statement_import._worker_count(statements) == expected


def test_small_batch_loads_in_process(monkeypatch):
    monkeypatch.setattr(statement_loader, "get_object_bytes", lambda key: b"pdf")
    monkeypatch.setattr(statement_loader, "extract_page_texts", lambda pdf: CHASE_PAGES)

    with StatementBatch([CHASE_KEY]) as batch:
        df = batch.load("chase", CHASE_KEY)

    assert list(df["Description"]) == ["Acme Gym"]
    assert df["Date"].iloc[0] == pd.Timestamp("2026-10-02")
