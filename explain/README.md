# personalexpensesapp

Personal finance app. Bank-statement PDFs (Citi, Wells Fargo, Chase, Banamex) stored in SeaweedFS S3 go through a keyword categorizer into Postgres, served by FastAPI (`:8000`) and a Next.js 15 dashboard (`:3000`) with an Ollama chat widget.

## Purpose

Imports monthly statements, categorizes transactions, and tracks expenses, receipts, rental properties (tenants, rent due), vehicles (services) and generated action items. `CLAUDE.md` already explains the import pipeline, categorization order, the `overridden` flag, startup migrations and money semantics. This file is the module and interface index.

## Main modules (path → role)

**Backend: `src/personal_expenses_app/`**
- `api/app.py` (~1.9k lines) → the whole FastAPI app: ORM models, `_run_migrations`, `lifespan`, all routes, and the pipeline thread.
- `infrastructure/{citi,wellsfargo,chase,banamex}_file_loader.py` → pdfplumber and regex statement parsers. Each returns a DataFrame with `Date, Bank, Description, Debit, Credit`. They share `statement_loader.py` (base class: S3 fetch, statement period, DataFrame), `statement_reconciliation.py` (`StatementTotals`, `Reconciliation`: read vs printed totals), `pdf_text.py` (PDF → page text) and `statement_import.py` (loader registry and `StatementBatch`, which the pipeline uses to extract text in worker processes).
- `infrastructure/expense_db_persistence.py` → `ExpenseDbPersistence` upsert. It declares `all_expenses` a second time, partially.
- `infrastructure/s3_storage.py` → the only module that talks to boto3/SeaweedFS: `get_object_bytes`, `put_object_bytes`, `object_exists`, `delete_object`, `list_keys`, `ensure_bucket_exists`.
- `infrastructure/citi_csv_file_loader.py`, `infrastructure/file_persistence.py`, `core/ml_based_expense_categorizer.py`, `core/corrections.py` → the legacy scikit-learn path, used by `main.py` with `resources/corrections.csv`.
- `core/rule_based_expense_categorizer.py` → `RuleBasedExpenseCategorizer` and the hardcoded `RULE_BASED_CATEGORIES`.
- `core/summarizer.py`, `interface/user_interaction.py` → helpers for the CLI scripts.
- `main_noml.py` → the older CLI import pipeline.
- `main.py` → the legacy ML CLI.

**Frontend: `frontend/src/`**
- `app/*/page.tsx` → pages: `/` (Dashboard), `/expenses`, `/expenses/[id]`, `/categories`, `/charts`, `/import`, `/rentals`, `/vehicles`.
- `app/api/**/route.ts` → server-side proxies to FastAPI through `API_URL`.
- `app/api/chat/route.ts` → builds context from backend data and streams the reply from Ollama.
- `components/*` → `ExpensesTable`, `FilterBar`, `BulkEditBar`, `CategoryEditor`, `ChatWidget`, `ActionList`, `RentalPropertyEditor`, `AddExpenseModal`, and others.
- `types/expense.ts` → shared TypeScript types.

**Ops**
- `docker-compose.yml`
- `Dockerfile.backup` with `scripts/backup_s3_bucket.py`
- `Dockerfile.pg-backup` with `scripts/backup_postgres_db.sh`
- `seaweedfs/identities.json` (S3 identities, mounted read-only into SeaweedFS)
- `frontend/Dockerfile`

## Interfaces

**HTTP (FastAPI, title "Personal Expenses API", all routes in `api/app.py`)**

| Area | Routes |
|---|---|
| Expenses | `GET`, `POST /expenses` (409 on a duplicate)<br>`GET`, `PATCH`, `DELETE /expenses/{expense_id}`<br>`PATCH /expenses/{expense_id}/category`<br>`POST /expenses/bulk-update`<br>`GET /expenses/comments`, `/expenses/summary`, `/expenses/property-summary` |
| Receipts | `POST`, `GET` (`?inline=`), `DELETE /expenses/{expense_id}/receipt` |
| Action items | `GET /expenses/action-items` (`?include_resolved=`)<br>`POST /expenses/action-items/{item_id}/resolve`<br>`POST /expenses/action-items/{item_id}/load` (statement "not in app" items) |
| Categories | `GET`, `POST /categories`<br>`PUT`, `DELETE /categories/{category_id}`<br>`POST /categories/seed`<br>`GET /banks` |
| Rentals | `GET`, `POST /rental-properties`<br>`PUT`, `DELETE /rental-properties/{property_id}`<br>`POST /rental-properties/{property_id}/sync-expenses` |
| Vehicles | `GET`, `POST /vehicles`<br>`GET`, `PUT`, `DELETE /vehicles/{vehicle_id}`<br>`GET`, `POST /vehicles/{vehicle_id}/services`<br>`PUT`, `DELETE /vehicles/{vehicle_id}/services/{service_id}` |
| Import | `POST /pipeline/run`. Body `PipelineRunRequest`: `year`, `citi_months`, `wellsfargo_months`, `chase_months`, `banamex_months`, with months as `jan`…`dec`. Streams `text/plain`. |
| Reconciliation | `GET /reconciliation/{year}?bank=&month=`. Read-only. `POST` runs the same check and files Action Items. Per uploaded statement: totals read vs totals printed on the statement (`adds_up`), transactions not in the database (`missing`), and `complete`. |
| Statements | `GET /statements/{bank}/{year}`<br>`POST`, `GET /statements/{bank}/{year}/{month}`<br>`bank` must be in `_VALID_BANKS` = `citi`, `wellsfargo`, `chase`, `banamex`. |

**Frontend proxies:** each backend path has its own route file, with one exception: `api/expenses/[id]/comments` and `api/expenses/[id]/property` both forward to `PATCH /expenses/{id}`.

**Database** (Postgres; compose creates DB `expensesassistant`; models at the top of `api/app.py`):
- `all_expenses` → unique constraint `uix_expense_natural_key` on (date, bank, description, debit, credit). Other columns: `category`, `overridden`, `comments`, `property_id`, `vehicle_id`, `balanced_date`, `receipt_filename`, `amortize_months`, `amortize_start_date`.
- `categories` → `name` unique; `keywords` is a JSON array stored as text.
- `rental_properties` → `alias`, `address`, `tenant`, `lease_renewal_date`, `payment_day`.
- `vehicles`, `vehicle_services`.
- `action_items` → `action_key` unique; `status` is `open` or `resolved`.
- Dates are stored as strings (`YYYY-MM-DD`). There is no Alembic.

**External services**
- SeaweedFS S3, bucket `expenses-documents` (from `s3.json.example`). Statements live at `resources/{bank}/{year}/...`, receipts under `RECEIPTS_PREFIX = "receipts/"`.
- Ollama's OpenAI-compatible `/v1/chat/completions` (default model `llama3.2`).

**Env vars (names only)**
- Backend: `DATABASE_URL` (required), `S3_CONFIG_PATH`, `S3_ENDPOINT_URL`.
- Frontend: `API_URL`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`.
- Backups: `S3_BACKUP_DIR`, `S3_BACKUP_INTERVAL_DAYS`, `POSTGRES_BACKUP_DIR`, `POSTGRES_BACKUP_INTERVAL_DAYS`, `PGHOST`/`PGPORT`/`PGUSER`/`PGDATABASE`/`PGPASSWORD`.
- Compose: `SEAWEEDFS_ADMIN_USER`, `SEAWEEDFS_ADMIN_PASSWORD`.
- `s3.json` keys: `endpoint_url`, `region`, `bucket`, `access_key`, `secret_key`.

## Known inconsistencies

- The `pyproject.toml` script `personal-expenses-app = personal_expenses_app.personal_expenses_app:main` points to a module that does not exist.
- The compose `backend` service builds from `Dockerfile.backend`, which does not exist. Run uvicorn on the host instead.
- `README.md` describes receipts and statements in local dirs (`RECEIPTS_DIR`, `resources/`), but the code uses S3 keys. Its `pg_dump` example also uses DB `expenses`, while compose creates `expensesassistant`.
- pytest is not a declared dependency.

## Related repos in this workspace

- `second-brain`: same stack pattern (FastAPI, Postgres, SeaweedFS, pgAdmin, backup sidecars). Its `scripts/backup_s3_bucket.py` is a copy of this repo's; its docstring still names `personal_expenses_app`. Both `docker-compose.yml` files publish host ports 5432, 5050, 8333 and 23646, so the two stacks cannot run at the same time. This repo's container names (`postgres`, `pgadmin`) are also unprefixed.
- `logseq-mcp-client`: no references either way.

## Build, run & test

- `uv sync`
- `docker compose up -d postgres seaweedfs`
- `$env:S3_ENDPOINT_URL="http://localhost:8333"; uv run python -m personal_expenses_app.serve` (uvicorn with `--reload`, plus backups when it stops)
- `uv run --with pytest pytest tests` (only file: `tests/test_rule_based_expense_categorizer.py`)
- `cd frontend; npm install; npm run dev`, plus `npm run lint` and `npm run build`. The frontend has no test suite.

## Where to look

- `src/personal_expenses_app/api/app.py`: routes, models, `_run_migrations`, `run_pipeline`, the action-item detection and the summary SQL.
- `src/personal_expenses_app/infrastructure/*_file_loader.py`: where most parsing fixes land.
- `src/personal_expenses_app/core/rule_based_expense_categorizer.py`: default categories. Order matters, and `"Real State"` is spelled that way on purpose.
- `frontend/src/app/api/chat/route.ts`, `frontend/src/app/import/page.tsx`, `frontend/src/types/expense.ts`.
- Do not stage `backups/postgres/`: it holds financial data and is not gitignored.
