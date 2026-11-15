# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Personal finance app: parses monthly bank statement PDFs (Citi, Wells Fargo, Chase, Banamex), categorizes transactions by keyword rules, stores them in Postgres, and serves a FastAPI backend + Next.js dashboard (expenses, categories, rental properties, vehicles, import, Ollama-backed chat). Development is on Windows/PowerShell.

## Commands

Backend (Python ≥3.11, uv-managed `.venv`, package installed editable from `src/`):

```powershell
uv sync
docker compose up -d postgres seaweedfs          # DB + S3 storage the backend needs
$env:S3_ENDPOINT_URL = "http://localhost:8333"   # s3.json points at the in-network "seaweedfs" host
uv run uvicorn personal_expenses_app.api.app:app --reload   # http://localhost:8000
```

Requires `.env` (`DATABASE_URL`, see `.env.example`) and `s3.json` (copy `s3.json.example`); both are gitignored. The backend runs on the host: `docker-compose.yml` references a `Dockerfile.backend` that does not exist, so don't `docker compose up` the `backend`/`frontend` services without adding it.

Tests (pytest is not a declared dependency):

```powershell
uv run --with pytest pytest tests
uv run --with pytest pytest tests/test_rule_based_expense_categorizer.py::test_custom_categories_override_defaults
```

`tests/test_expense_db_persistence.py` is skipped unless `TEST_DATABASE_URL` points at a Postgres ≥15 where tests may create throwaway databases, e.g. `postgresql://postgres:<password>@localhost:5432/postgres` for the docker-compose one.

Frontend (`frontend/`, Next.js 15 / React 19 / Tailwind; no test suite):

```powershell
cd frontend; cp .env.local.example .env.local; npm install
npm run dev     # http://localhost:3000
npm run lint
npm run build   # standalone output, used by frontend/Dockerfile
```

Chat widget needs Ollama running locally (`ollama serve`, `ollama pull llama3.2`); configured via `OLLAMA_BASE_URL` / `OLLAMA_MODEL`.

## Architecture

**Layers** (`src/personal_expenses_app/`): `infrastructure/` (per-bank statement loaders, DB persistence, S3 wrapper) → `core/` (categorization, summarizing) → `api/app.py` (the entire FastAPI app in one file: ORM models, startup migrations, all routes). `main_noml.py` is an older CLI version of the import pipeline; `main.py` is a legacy ML (scikit-learn) path using Citi CSVs and `resources/corrections.csv`. The live import path is `POST /pipeline/run`.

**Storage is S3, not the filesystem.** Statement PDFs and receipts live in a SeaweedFS bucket accessed only through `infrastructure/s3_storage.py`. Paths like `resources/{bank}/{year}/{bank}-{month}-{year}.pdf` and `receipts/{id}_{name}` are object keys; loaders call `get_object_bytes(key)`. (The README's mentions of a local `receipts/` dir / `RECEIPTS_DIR` are outdated.)

**Import pipeline** (`POST /pipeline/run`): per selected month, each bank loader returns a DataFrame with `Date, Bank, Description, Debit, Credit` → `RuleBasedExpenseCategorizer` → `ExpenseDbPersistence.save_expenses` (upsert) → link expenses to rental properties by tenant name. Runs in a daemon thread with stdout redirected into a queue that is streamed back as `text/plain`, so pipeline code reports progress via `print`.

**Statement loaders**: `infrastructure/statement_loader.py` holds what the banks share (`StatementLoader`: fetch from S3, statement period, year rollover, building the DataFrame); each `*_file_loader.py` only implements `_parse_transactions(page_texts, period)`, a regex parser over `pdfplumber` text with bank-specific section headers and many PDF-quirk workarounds; most recent fixes land there. `parse_statement(key, page_texts)` takes plain strings, so parsers are tested without PDFs (`tests/test_statement_loaders.py`). Descriptions are part of the natural key, so a parser change that alters a description makes a re-import insert that row again. Extracting PDF text (`pdf_text.py`) is about 90% of import time; `statement_import.StatementBatch` does it in worker processes when a run covers more than four statements (`STATEMENT_IMPORT_WORKERS=1` keeps it in-process).

**Categorization**: case-sensitive substring match, first match wins in dict order, else `"Other"`. Keywords come from the `categories` DB table ordered by id; if the table is empty, the hardcoded `RULE_BASED_CATEGORIES` in `core/rule_based_expense_categorizer.py` is used (it also seeds the table via `POST /categories/seed`). Category order matters, e.g. `"Payment From <name>"` keywords decide Real State vs Transfers vs Restaurants. `PUT /categories/{id}` re-applies keywords to existing rows with case-insensitive `ILIKE`, including overridden rows.

**The `overridden` flag** protects manual edits: any PATCH/bulk-update sets it, and the pipeline upsert keeps the existing category when it is true. Category renames propagate only to non-overridden rows.

**Schema / migrations**: no Alembic. Tables are created by SQLAlchemy `create_all` plus hand-written idempotent SQL (`DO $$ ... IF NOT EXISTS ...`) in `_run_migrations`, executed at app startup (`api/app.py`) and by `ExpenseDbPersistence` the first time a process uses a database (it then skips them). The duplicate-row cleanup runs only while `uix_expense_natural_key` is missing or does not treat NULLs as equal. `_get_engine()` is cached: one engine and connection pool per process. `all_expenses` is declared twice, fully in `api/app.py` and partially in `infrastructure/expense_db_persistence.py`; keep them consistent when adding columns. The natural key `(date, bank, description, debit, credit)` is `UNIQUE NULLS NOT DISTINCT`; identical rows within one import batch get ` (2)`, ` (3)` appended to the description so both survive.

**Money semantics**: net = debit − credit (positive = expense, negative = income/refund). Raw SQL guards against both NULL and `'NaN'::numeric`. Summaries (`/expenses/summary`, `/expenses/property-summary`) group by `amortize_start_date` → `balanced_date` → `date` and spread amounts across `amortize_months` with `generate_series`; date filters apply to the post-amortization month. Debit/credit are editable only when `bank == "cash"` (manually entered expenses).

**Domain strings used as identifiers**: the category is spelled `"Real State"` and that literal drives rent-paid detection; don't correct it. Action items (`GET /expenses/action-items`) are recomputed on each request: unpaid rent per property after its `payment_day`, and ≥5% month-over-month changes per Utilities vendor (vendor list from hardcoded `RULE_BASED_CATEGORIES["Utilities"]`, not the DB).

**Frontend**: client components call only `/api/...` Next.js route handlers (`frontend/src/app/api/**/route.ts`), which proxy one-to-one to the FastAPI backend via `API_URL` (default `http://localhost:8000`). Adding a backend endpoint for the UI means adding a matching proxy route. `api/chat/route.ts` builds a context from backend summary/expense data and streams from Ollama's OpenAI-compatible `/v1/chat/completions`. Shared types are in `frontend/src/types/expense.ts`; import alias `@/*` → `frontend/src/*`.

## Data hygiene

Statements, receipts, and DB dumps contain personal financial data. `resources/`, `receipts/`, and `backups/s3/` are gitignored, but `backups/postgres/` (written by the `pg-backup` compose service) is not, so stage files explicitly rather than `git add -A`.

## Repository overview
@explain/README.md
