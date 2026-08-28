# personalexpensesapp
Load and analyze personal expenses from bank accounts

Run Backend
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:\Users\salas\VSCodeProjects\github\personalexpensesapp\.venv\Scripts\Activate.ps1)
$env:S3_ENDPOINT_URL = "http://localhost:8333"
uvicorn personal_expenses_app.api.app:app --reload

Deploy and Run FrontEnd
docker stop expenses-frontend
docker rm expenses-frontend
docker build -t expenses-frontend:latest C:\Users\salas\VSCodeProjects\github\personalexpensesapp\frontend
docker run -d --name expenses-frontend -p 3000:3000 -e API_URL=http://host.docker.internal:8000 expenses-frontend:latest
docker logs expenses-frontend
http://localhost:3000

Deploy Node.JS
1. https://nodejs.org/en/download
2. cd frontend
	cp .env.local.example .env.local   # adjust API_URL if backend isn't on :8000
3. npm install
4. npm run dev

Install Ollama v0.24.0 locally
$env:LOCALAPPDATA\Programs\Ollama\ollama.exe
whitelist registry.ollama.ai in Zscaler
ollama serve          # start Ollama daemon
ollama pull llama3.2  # download the model (one-time)

SeaweedFS
Admin UI is live at http://localhost:23646 with a login page (default admin/admin)

Backup Postgres DB on Docker Image
docker exec -t postgres pg_dump -U postgres expenses > expenses_051026-1242.sql

POST /expenses — creates a new expense manually (marks it as overridden=true), returns 409 on duplicate
DELETE /expenses/{id} — deletes an expense, returns 204
GET /categories now returns [[{id, name, keywords[]}]](http://vscodecontentref/22) from the categories table
POST /categories — create a category
PUT /categories/{id} — update a category
DELETE /categories/{id} — delete a category
POST /categories/seed — seeds the DB from RULE_BASED_CATEGORIES, inserting only missing ones, returns {inserted, skipped}
Backend (rule_based_expense_categorizer.py):
POST /expenses/bulk-update endpoint — accepts { ids, category?, property_id?, comments? } and applies whichever fields are present to all listed expense IDs, marking each as overridden=True. Returns the list of updated IDs.
GET/POST /vehicles
GET/PUT/DELETE /vehicles/{id}
GET/POST /vehicles/{id}/services
PUT/DELETE /vehicles/{id}/services/{serviceId}
GET /expenses/property-summary — JOINs all_expenses with rental_properties on property_id, groups by month + property alias, returns { month, property, total } (net debit − credit, NaN-safe).
POST /expenses/{id}/receipt — multipart upload, validates extension (pdf/images), stores file to receipts/ dir as {id}_{sanitized_name}, path-traversal safe
	- Default path: <project_root>/receipts/ — controlled by the RECEIPTS_DIR environment variable (falls back to receipts at the project root if not set)
	- Filename format: {expense_id}_{original_filename} (e.g., 42_scan.pdf)
GET /expenses/{id}/receipt?inline=true|false — serves file inline (view) or as download attachment
DELETE /expenses/{id}/receipt — removes file and clears DB column
POST /pipeline/run endpoint — runs the pipeline in a daemon thread, captures stdout via a queue-backed writer, and streams chunks back as text/plain
GET /statements/{bank}/{year} — returns the list of months that have a PDF file on disk for that bank/year
POST /statements/{bank}/{year}/{month} — uploads a PDF, saving it as resources/{bank}/{year}/{bank}-{month}-{year}.pdf (creates directories if needed); validates bank, month, year, and file extension
GET /statements/{bank}/{year}/{month} — downloads the PDF via FileResponse
POST /rental-properties/{id}/sync-expenses — looks up the property's tenant field, then does a case-insensitive ILIKE %tenant% search across all all_expenses.description rows and sets their property_id. Returns { "updated": N }
GET /expenses/action-items — runs detection, returns open items (?include_resolved=true for all).
POST /expenses/action-items/{item_id}/resolve — marks an item resolved.

