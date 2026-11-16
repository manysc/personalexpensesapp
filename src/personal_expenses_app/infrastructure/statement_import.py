"""Loading a batch of statements, the way the import pipeline does.

Almost all of an import's time goes into extracting text from the PDFs, which is
CPU-bound. A batch of more than a month's worth of statements therefore has its text
extracted in worker processes, all started up front; the statements are then parsed one
at a time in the caller's order, so progress output and errors appear exactly as they
would without the workers.
"""

from __future__ import annotations

import logging
import multiprocessing
import os
from concurrent.futures import Future, ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from typing import Iterable, Optional

import pandas as pd

from personal_expenses_app.infrastructure.banamex_file_loader import BanamexFileLoader
from personal_expenses_app.infrastructure.chase_file_loader import ChaseFileLoader
from personal_expenses_app.infrastructure.citi_file_loader import CitiFileLoader
from personal_expenses_app.infrastructure.pdf_text import extract_page_texts
from personal_expenses_app.infrastructure.s3_storage import get_object_bytes
from personal_expenses_app.infrastructure.statement_loader import StatementLoader
from personal_expenses_app.infrastructure.statement_reconciliation import Reconciliation
from personal_expenses_app.infrastructure.wellsfargo_file_loader import WellsfargoFileLoader

logger = logging.getLogger(__name__)

# In the order a month's statements are loaded.
LOADERS: dict[str, StatementLoader] = {
    loader.bank: loader
    for loader in (CitiFileLoader(), WellsfargoFileLoader(), ChaseFileLoader(), BanamexFileLoader())
}

# Set to 1 to always extract text in the server process.
WORKERS_ENV_VAR = "STATEMENT_IMPORT_WORKERS"
# Starting worker processes costs more than it saves for a single month's statements.
_MIN_STATEMENTS_FOR_WORKERS = len(LOADERS) + 1


def statement_key(bank: str, year: str, month: str) -> str:
    """Return the S3 key of a bank's statement for a month (``jan``..``dec``)."""
    return f"resources/{bank}/{year}/{bank}-{month}-{year}.pdf"


def _worker_count(statement_count: int) -> int:
    if statement_count < _MIN_STATEMENTS_FOR_WORKERS:
        return 1
    configured = os.environ.get(WORKERS_ENV_VAR)
    limit = int(configured) if configured else (os.cpu_count() or 1)
    return max(1, min(limit, statement_count))


class StatementBatch:
    """Loads the statements of one import run; use as a context manager.

    ``keys`` are the statements the run will ask for. Keys loaded without having been
    announced, or announced to a small batch, are simply read in the calling process.
    """

    def __init__(self, keys: Iterable[str], max_workers: Optional[int] = None) -> None:
        self._keys = list(keys)
        self._max_workers = max_workers if max_workers is not None else _worker_count(len(self._keys))
        self._pool: Optional[ProcessPoolExecutor] = None
        self._page_texts: dict[str, Future[list[str]]] = {}

    def __enter__(self) -> StatementBatch:
        if self._max_workers > 1:
            self._start_extracting()
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._pool is not None:
            self._pool.shutdown(wait=True, cancel_futures=True)

    @property
    def worker_processes(self) -> int:
        """How many processes extract PDF text; 0 when it is done in this process."""
        return self._max_workers if self._page_texts else 0

    def load(self, bank: str, key: str) -> pd.DataFrame:
        """Return the transactions of one statement, as its bank's loader would."""
        return LOADERS[bank].parse_statement(key, self._page_texts_of(key))

    def read(self, bank: str, key: str) -> tuple[pd.DataFrame, Reconciliation]:
        """Return one statement's transactions and how they compare with its printed totals."""
        return LOADERS[bank].read_statement(key, self._page_texts_of(key))

    def _page_texts_of(self, key: str) -> list[str]:
        extraction = self._page_texts.get(key)
        if extraction is not None:
            try:
                return extraction.result()
            except BrokenProcessPool:
                logger.warning("Statement worker processes failed; reading %s in-process", key)
        return extract_page_texts(get_object_bytes(key))

    def _start_extracting(self) -> None:
        try:
            # "spawn" behaves the same on every OS and is safe to use from a threaded server.
            self._pool = ProcessPoolExecutor(
                max_workers=self._max_workers, mp_context=multiprocessing.get_context("spawn")
            )
            for key in self._keys:
                self._page_texts[key] = self._submit(key)
        except (OSError, RuntimeError, BrokenProcessPool):
            logger.warning("Could not start statement worker processes; reading in-process", exc_info=True)
            self._page_texts.clear()

    def _submit(self, key: str) -> Future[list[str]]:
        """Fetch a statement now, but keep a failure for when the run reaches that statement."""
        try:
            pdf_bytes = get_object_bytes(key)
        except Exception as error:  # Re-raised by Future.result() when the run gets there.
            failed: Future[list[str]] = Future()
            failed.set_exception(error)
            return failed
        return self._pool.submit(extract_page_texts, pdf_bytes)
