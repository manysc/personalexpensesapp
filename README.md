# personalexpensesapp

Load and analyze personal expenses from bank accounts.

The app parses monthly bank statement PDFs (Citi, Wells Fargo, Chase, Banamex), categorizes each transaction by keyword rules, stores them in Postgres, and shows them in a web dashboard with expenses, categories, rental properties, vehicles, statement import and an AI chat assistant.

- **Backend:** FastAPI (Python 3.11+, managed with uv), in `src/personal_expenses_app/`
- **Frontend:** Next.js 15 / React 19 / Tailwind, in `frontend/`
- **Database:** Postgres (Docker)
- **File storage:** SeaweedFS, an S3-compatible store (Docker), for statement PDFs and receipts
- **Chat assistant:** Ollama running locally

Commands below are for PowerShell on Windows, run from the project root unless noted.

## Run Backend

The backend is a FastAPI app served by uvicorn on the host (not in Docker). Commands below are for PowerShell, run from the project root.

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (manages Python 3.11+ and the `.venv`)
- Docker Desktop (for Postgres and SeaweedFS)

### 1. Configure

```powershell
cp .env.example .env          # set DATABASE_URL
cp s3.json.example s3.json    # set access_key / secret_key
cp seaweedfs/identities.json.example seaweedfs/identities.json   # same keys as s3.json
```

All three are gitignored. In `.env`, choose `POSTGRES_PASSWORD` and `PGADMIN_DEFAULT_PASSWORD` (Docker Compose reads them from there) and use the same Postgres password in
`DATABASE_URL=postgresql://postgres:<POSTGRES_PASSWORD>@localhost:5432/expensesassistant`.
The keys in `s3.json` and `seaweedfs/identities.json` must match.

### 2. Start Postgres and SeaweedFS

```powershell
docker compose up -d postgres seaweedfs
```

The backend creates and migrates its tables on startup; there is no separate migration step. Don't run `docker compose up` for the `backend` service: its `Dockerfile.backend` doesn't exist.

### 3. Install dependencies

```powershell
uv sync
```

Packages come from public PyPI (set in `pyproject.toml`). If `uv sync` instead tries to download from a company mirror (e.g. a 403 error from an Artifactory URL), a user-wide uv setting is overriding the project. Point uv at PyPI for the current window and retry:

```powershell
$env:UV_DEFAULT_INDEX = "https://pypi.org/simple"
uv sync
```

### 4. Run

```powershell
$env:S3_ENDPOINT_URL = "http://localhost:8333"   # s3.json uses the Docker-only host "seaweedfs"
uv run uvicorn personal_expenses_app.api.app:app --reload
```

Instead of setting `S3_ENDPOINT_URL` each time, you can uncomment it in `.env`.

The API is at http://localhost:8000 (interactive docs at http://localhost:8000/docs).

### Tests

```powershell
uv run --with pytest pytest tests
```

## Run Frontend

### Development

Requires [Node.js](https://nodejs.org/en/download).

```powershell
cd frontend
cp .env.local.example .env.local   # adjust API_URL if the backend isn't on http://localhost:8000
npm install
npm run dev
```

Open http://localhost:3000. The frontend only calls its own `/api/...` routes, which forward requests to the backend at `API_URL`.

Other commands: `npm run lint`, `npm run build`.

### Docker

Build and run the production image, pointing it at a backend running on the host:

```powershell
docker stop expenses-frontend; docker rm expenses-frontend
docker build -t expenses-frontend:latest ./frontend
docker run -d --name expenses-frontend -p 3000:3000 `
  -e API_URL=http://host.docker.internal:8000 `
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 `
  expenses-frontend:latest
docker logs expenses-frontend
```

Open http://localhost:3000.

## Chat Assistant (Ollama)

The chat widget needs Ollama running locally.

1. Install Ollama (tested with v0.24.0). On Windows it installs to `$env:LOCALAPPDATA\Programs\Ollama\ollama.exe`.
2. Start it and download the model once:

   ```powershell
   ollama serve          # start the Ollama service
   ollama pull llama3.2  # one-time model download
   ```

On a network with Zscaler, `registry.ollama.ai` must be allowlisted for `ollama pull` to work.

The frontend uses `OLLAMA_BASE_URL` (default `http://localhost:11434`) and `OLLAMA_MODEL` (default `llama3.2`).

## Claude Connection (MCP Server)

`mcp_server/expenses_mcp_server.py` is an MCP server that lets Claude read and update your data through the backend API. It needs the backend running on port 8000 and [uv](https://docs.astral.sh/uv/). It declares its own dependencies (`mcp`, `httpx`), so it does not touch the app's `.venv`.

Add it to the Claude desktop app (**Settings → Developer → Edit Config**, file `%APPDATA%\Claude\claude_desktop_config.json`), inside `"mcpServers"`:

```json
"expenses": {
  "command": "uv",
  "args": ["run", "--script", "C:\\Users\\T-SALAS\\GitHub\\personalexpensesapp\\mcp_server\\expenses_mcp_server.py"],
  "env": { "EXPENSES_API_URL": "http://localhost:8000" }
}
```

Then fully quit and reopen the Claude desktop app. If it can't find `uv`, use its full path as `command` (run `(Get-Command uv).Source` in PowerShell to get it).

Tools:

- **Read:** `list_expenses`, `get_expense`, `get_spending_summary` (totals by month/category/property), `get_property_summary`, `list_commented_expenses`, `list_action_items`, `list_categories`, `list_banks`, `list_rental_properties`, `list_vehicles`, `list_vehicle_services`, `list_statement_months`
- **Write:** `create_expense`, `update_expense`, `set_expense_category`, `bulk_update_expenses`, `attach_receipt`, `resolve_action_item`, `create_category`, `update_category`, `create_rental_property`, `update_rental_property`, `sync_property_expenses`, `create_vehicle`, `update_vehicle`, `add_vehicle_service`, `update_vehicle_service`, `upload_statement`, `run_import_pipeline`
- **Delete** (marked destructive): `delete_expense`, `delete_receipt`, `delete_category`, `delete_rental_property`, `delete_vehicle`, `delete_vehicle_service`

Test it without Claude: `npx @modelcontextprotocol/inspector uv run --script mcp_server/expenses_mcp_server.py`.

## Admin Tools

| Tool | URL | Login |
|---|---|---|
| SeaweedFS Admin UI (browse stored PDFs and receipts) | http://localhost:23646 | `admin` / `admin` by default; change with `SEAWEEDFS_ADMIN_USER` / `SEAWEEDFS_ADMIN_PASSWORD` |
| pgAdmin (Postgres) | http://localhost:5050 | `admin@example.com` / `PGADMIN_DEFAULT_PASSWORD` from `.env` (used when pgAdmin is first set up) |

Start them with `docker compose up -d seaweedfs-admin pg_admin`.

## Backups

Two Docker services make backups automatically. Each runs once at startup and then every 30 days:

- `pg-backup`: dumps the `expensesassistant` database to `backups/postgres/` as gzipped SQL. Change the interval with `POSTGRES_BACKUP_INTERVAL_DAYS` in `.env`.
- `s3-backup`: archives the `expenses-documents` bucket to `backups/s3/`. Change the interval with `S3_BACKUP_INTERVAL_DAYS` in `.env`.

```powershell
docker compose up -d pg-backup s3-backup
```

Manual database dump:

```powershell
docker exec -t postgres pg_dump -U postgres expensesassistant > expensesassistant_$(Get-Date -Format yyyyMMdd-HHmmss).sql
```

Backups contain personal financial data. `backups/s3/` is gitignored but `backups/postgres/` is not, so don't commit with `git add -A`.

## How It Works

### Importing statements

1. Upload a statement PDF for a bank and month (the Import page, or `POST /statements/{bank}/{year}/{month}`). It is stored in SeaweedFS as `resources/{bank}/{year}/{bank}-{month}-{year}.pdf`.
2. Run the import (`POST /pipeline/run`). For each selected month, the bank's loader reads the PDF, the categorizer assigns categories, and the rows are saved to Postgres. Progress is streamed back as plain text.
3. Expenses are linked to rental properties whose tenant name appears in the description.

### Categories

Each category has a list of keywords. A transaction gets the first category whose keyword appears in its description (case-sensitive), or `Other` if none match, so category order matters. Categories live in the `categories` table; `POST /categories/seed` fills it from the built-in defaults.

Editing an expense's category by hand marks it as overridden, and later imports keep your choice.

### Amounts

Net amount = debit − credit: positive is an expense, negative is income or a refund. Summaries can spread an expense over several months (amortization).

## API Reference

Interactive docs with request and response details: http://localhost:8000/docs

### Expenses

| Method | Path | Description |
|---|---|---|
| GET | `/expenses` | List expenses. Filters: `bank`, `category`, `date_from`, `date_to`, `description`, `comments`, `property_id` |
| POST | `/expenses` | Create an expense manually (marked overridden). 409 on duplicate |
| GET | `/expenses/{id}` | Get one expense |
| PATCH | `/expenses/{id}` | Update an expense (marks it overridden) |
| PATCH | `/expenses/{id}/category` | Change an expense's category (marks it overridden) |
| POST | `/expenses/bulk-update` | Body `{ ids, category?, property_id?, comments? }`. Applies the given fields to every listed expense and marks them overridden. Returns the updated IDs |
| DELETE | `/expenses/{id}` | Delete an expense. Returns 204 |
| GET | `/expenses/comments` | Expenses that have a comment, optionally filtered by `date_from` / `date_to` |
| GET | `/expenses/summary` | Net totals by month, category and rental property |
| GET | `/expenses/property-summary` | Net totals by month and rental property: `{ month, property, total }` |
| GET | `/expenses/action-items` | Open action items: unpaid rent and large utility bill changes. Add `?include_resolved=true` for all |
| POST | `/expenses/action-items/{item_id}/resolve` | Mark an action item resolved |
| GET | `/banks` | Distinct bank names |

### Receipts

| Method | Path | Description |
|---|---|---|
| POST | `/expenses/{id}/receipt` | Upload or replace a receipt (PDF or image). Stored in SeaweedFS as `receipts/{id}_{filename}` |
| GET | `/expenses/{id}/receipt` | Get the receipt. `?inline=true` to view, `false` to download |
| DELETE | `/expenses/{id}/receipt` | Delete the receipt. Returns 204 |

### Categories

| Method | Path | Description |
|---|---|---|
| GET | `/categories` | List categories: `{ id, name, keywords[] }` |
| POST | `/categories` | Create a category |
| PUT | `/categories/{id}` | Update a category and re-apply its keywords to existing expenses |
| DELETE | `/categories/{id}` | Delete a category |
| POST | `/categories/seed` | Add any missing built-in categories. Returns `{ inserted, skipped }` |

### Rental properties

| Method | Path | Description |
|---|---|---|
| GET | `/rental-properties` | List properties |
| POST | `/rental-properties` | Create a property |
| PUT | `/rental-properties/{id}` | Update a property |
| DELETE | `/rental-properties/{id}` | Delete a property |
| POST | `/rental-properties/{id}/sync-expenses` | Link every expense whose description contains the property's tenant name (case-insensitive). Returns `{ updated }` |

### Vehicles

| Method | Path | Description |
|---|---|---|
| GET, POST | `/vehicles` | List or create vehicles |
| GET, PUT, DELETE | `/vehicles/{id}` | Get, update or delete a vehicle |
| GET, POST | `/vehicles/{id}/services` | List or add service records |
| PUT, DELETE | `/vehicles/{id}/services/{service_id}` | Update or delete a service record |

### Statements and import

| Method | Path | Description |
|---|---|---|
| GET | `/statements/{bank}/{year}` | Months that have a statement PDF for that bank and year |
| POST | `/statements/{bank}/{year}/{month}` | Upload a statement PDF |
| GET | `/statements/{bank}/{year}/{month}` | Download a statement PDF |
| POST | `/pipeline/run` | Import the selected statements. Streams progress as plain text |
