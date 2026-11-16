# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "mcp>=2.3,<3",
#     "httpx>=0.27",
# ]
# ///
"""MCP server for the Personal Expenses app.

Exposes the FastAPI backend (default http://localhost:8000) as MCP tools so
Claude (or any MCP client) can read and update expenses, categories, rental
properties, vehicles and action items.

Run (stdio transport):
    uv run --script mcp_server/expenses_mcp_server.py

Environment:
    EXPENSES_API_URL      Backend base URL (default http://localhost:8000)
    EXPENSES_API_TIMEOUT  Request timeout in seconds (default 30)
"""

from __future__ import annotations

import logging
import mimetypes
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Literal

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

API_URL = os.environ.get("EXPENSES_API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = float(os.environ.get("EXPENSES_API_TIMEOUT", "30"))

# httpx logs every request at INFO; keep the MCP server's stderr quiet.
logging.getLogger("httpx").setLevel(logging.WARNING)

INSTRUCTIONS = """\
Tools for the user's Personal Expenses app (bank-statement transactions stored in Postgres).

Money semantics: each expense has `debit` and `credit`; net = debit - credit, so a positive
net is spending and a negative net is income/refund. Summaries already return net totals.

Domain notes:
- The real-estate category is spelled "Real State" on purpose (it drives rent detection); never "fix" it.
- Rental properties are referenced by `property_id`; use list_rental_properties to map ids to aliases
  (e.g. Kostka, Franklin, Stonefield, Escalante).
- Any manual edit (update_expense, bulk_update_expenses, set_expense_category) marks the expense as
  `overridden`, which protects it from being re-categorized by future imports.
- debit/credit can only be edited on manually entered expenses (bank == "cash").
- Category names must match an existing category (list_categories) to show up correctly in reports.

For yearly or category totals prefer get_spending_summary (aggregated server-side) over paging
through list_expenses. Confirm with the user before deleting anything.
"""

mcp = MCPServer("expenses", instructions=INSTRUCTIONS)

READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
UPDATE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False)
DELETE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=False)


class ExpensesApiError(ToolError):
    """Raised for backend failures; its message is shown to the client."""


def _clean(d: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is None so they are not sent to the API."""
    return {k: v for k, v in d.items() if v is not None}


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: Any = None,
    files: dict[str, Any] | None = None,
    timeout: float | None = None,
) -> Any:
    url = f"{API_URL}{path}"
    try:
        with httpx.Client(timeout=timeout or TIMEOUT) as client:
            resp = client.request(method, url, params=_clean(params or {}), json=json, files=files)
    except httpx.ConnectError as e:
        raise ExpensesApiError(
            f"Cannot reach the expenses backend at {API_URL}. Start it with "
            "`uv run uvicorn personal_expenses_app.api.app:app --reload` (and `docker compose up -d "
            f"postgres seaweedfs`). Details: {e}"
        ) from e
    except httpx.TimeoutException as e:
        raise ExpensesApiError(f"Request to {url} timed out after {timeout or TIMEOUT}s") from e

    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise ExpensesApiError(f"{method} {path} failed with HTTP {resp.status_code}: {detail}")

    if resp.status_code == 204 or not resp.content:
        return {"ok": True}
    ctype = resp.headers.get("content-type", "")
    if "application/json" in ctype:
        data = resp.json()
        # Return lists as one object so clients get a single JSON result.
        return {"count": len(data), "items": data} if isinstance(data, list) else data
    return resp.text


# --------------------------------------------------------------------------- reads


@mcp.tool(annotations=READ)
def list_expenses(
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    description: str | None = None,
    comments: str | None = None,
    bank: str | None = None,
    property_id: int | None = None,
    vehicle_id: int | None = None,
    overridden_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """List individual expense transactions with optional filters.

    Dates are YYYY-MM-DD (inclusive). `description` and `comments` are case-insensitive substring
    filters. Returns {total, limit, offset, items}; page with `offset` when total > limit (max limit 10000).
    """
    return _request(
        "GET",
        "/expenses",
        params=dict(
            date_from=date_from,
            date_to=date_to,
            category=category,
            description=description,
            comments=comments,
            bank=bank,
            property_id=property_id,
            vehicle_id=vehicle_id,
            overridden_only=overridden_only,
            limit=limit,
            offset=offset,
        ),
    )


@mcp.tool(annotations=READ)
def get_expense(expense_id: int) -> dict[str, Any]:
    """Get a single expense by id."""
    return _request("GET", f"/expenses/{expense_id}")


@mcp.tool(annotations=READ)
def get_spending_summary(
    date_from: str | None = None,
    date_to: str | None = None,
    group_by: list[Literal["month", "category", "property"]] | None = None,
    exclude_categories: list[str] | None = None,
) -> dict[str, Any]:
    """Net totals (debit - credit) aggregated server-side.

    The backend groups by month, category and rental property, spreading amortized expenses across
    months. `group_by` re-aggregates to the dimensions you need, e.g. ["category"] for yearly totals
    per category or ["month"] for a monthly trend; default is all three. `exclude_categories` drops
    rows such as ["Income", "Transfers"]. Rows are sorted by total, largest first, and
    `grand_total` is the net sum of the returned rows.
    Dates are YYYY-MM-DD and filter on the (post-amortization) month.
    """
    rows = _request("GET", "/expenses/summary", params=dict(date_from=date_from, date_to=date_to))["items"]
    keys = group_by or ["month", "category", "property"]
    excluded = set(exclude_categories or [])
    totals: dict[tuple, float] = defaultdict(float)
    for r in rows:
        if r.get("category") in excluded:
            continue
        totals[tuple(r.get(k) for k in keys)] += float(r.get("total") or 0)
    out = [dict(zip(keys, k), total=round(v, 2)) for k, v in totals.items()]
    out.sort(key=lambda x: x["total"], reverse=True)
    return {"group_by": keys, "grand_total": round(sum(totals.values()), 2), "rows": out}


@mcp.tool(annotations=READ)
def get_property_summary(date_from: str | None = None, date_to: str | None = None) -> Any:
    """Net totals (debit - credit) by month and rental property alias. Negative = net income (rent)."""
    return _request("GET", "/expenses/property-summary", params=dict(date_from=date_from, date_to=date_to))


@mcp.tool(annotations=READ)
def list_commented_expenses(date_from: str | None = None, date_to: str | None = None) -> Any:
    """Expenses that have a non-empty comment (the user's annotations), optionally by date range."""
    return _request("GET", "/expenses/comments", params=dict(date_from=date_from, date_to=date_to))


@mcp.tool(annotations=READ)
def list_action_items(include_resolved: bool = False) -> Any:
    """Open action items: unpaid rent per property, >=5% month-over-month utility changes, and
    statement follow-ups (statement_unverified: a statement does not add up to its printed totals;
    statement_not_stored / statement_not_imported: transactions on a statement are not in the app)."""
    return _request("GET", "/expenses/action-items", params=dict(include_resolved=include_resolved))


@mcp.tool(annotations=READ)
def list_categories() -> Any:
    """All categories with their matching keywords."""
    return _request("GET", "/categories")


@mcp.tool(annotations=READ)
def list_banks() -> Any:
    """Distinct bank names present in the expenses table."""
    return _request("GET", "/banks")


@mcp.tool(annotations=READ)
def list_rental_properties() -> Any:
    """Rental properties (id, alias, address, tenant, lease renewal date, rent payment day)."""
    return _request("GET", "/rental-properties")


@mcp.tool(annotations=READ)
def list_vehicles() -> Any:
    """Vehicles (id, alias, make, model, year, registration due date)."""
    return _request("GET", "/vehicles")


@mcp.tool(annotations=READ)
def list_vehicle_services(vehicle_id: int) -> Any:
    """Maintenance service records for a vehicle, newest first."""
    return _request("GET", f"/vehicles/{vehicle_id}/services")


@mcp.tool(annotations=READ)
def list_statement_months(bank: str, year: str) -> Any:
    """Months (jan..dec) that have an uploaded statement PDF for a bank (citi, wellsfargo, chase, banamex) and year."""
    return _request("GET", f"/statements/{bank}/{year}")


# --------------------------------------------------------------------------- expense writes


@mcp.tool(annotations=WRITE)
def create_expense(
    date: str,
    description: str,
    debit: float | None = None,
    credit: float | None = None,
    bank: str = "cash",
    category: str | None = None,
    comments: str | None = None,
    property_id: int | None = None,
    balanced_date: str | None = None,
) -> Any:
    """Manually add an expense (e.g. a cash payment). Use `debit` for money spent, `credit` for money received.

    `date`/`balanced_date` are YYYY-MM-DD; `balanced_date` books the amount in a different month.
    """
    return _request(
        "POST",
        "/expenses",
        json=_clean(
            dict(
                date=date,
                bank=bank,
                description=description,
                debit=debit,
                credit=credit,
                category=category,
                comments=comments,
                property_id=property_id,
                balanced_date=balanced_date,
            )
        ),
    )


@mcp.tool(annotations=UPDATE)
def update_expense(
    expense_id: int,
    category: str | None = None,
    comments: str | None = None,
    property_id: int | None = None,
    vehicle_id: int | None = None,
    balanced_date: str | None = None,
    amortize_months: int | None = None,
    amortize_start_date: str | None = None,
    debit: float | None = None,
    credit: float | None = None,
) -> Any:
    """Update fields of one expense; only the fields you pass change. Marks the expense as overridden.

    `amortize_months` > 1 spreads the amount evenly over that many months from `amortize_start_date`.
    debit/credit are only editable on bank == "cash" expenses.
    """
    body = _clean(
        dict(
            category=category,
            comments=comments,
            property_id=property_id,
            vehicle_id=vehicle_id,
            balanced_date=balanced_date,
            amortize_months=amortize_months,
            amortize_start_date=amortize_start_date,
            debit=debit,
            credit=credit,
        )
    )
    if not body:
        raise ExpensesApiError("Pass at least one field to update.")
    return _request("PATCH", f"/expenses/{expense_id}", json=body)


@mcp.tool(annotations=UPDATE)
def set_expense_category(expense_id: int, category: str) -> Any:
    """Change one expense's category (marks it overridden so future imports keep it)."""
    return _request("PATCH", f"/expenses/{expense_id}/category", json={"category": category})


@mcp.tool(annotations=UPDATE)
def bulk_update_expenses(
    ids: list[int],
    category: str | None = None,
    comments: str | None = None,
    property_id: int | None = None,
    vehicle_id: int | None = None,
) -> Any:
    """Apply the same category/comments/property/vehicle to many expenses. Returns the updated ids."""
    body = _clean(dict(category=category, comments=comments, property_id=property_id, vehicle_id=vehicle_id))
    if not body:
        raise ExpensesApiError("Pass at least one field to update.")
    return _request("POST", "/expenses/bulk-update", json={"ids": ids, **body})


@mcp.tool(annotations=DELETE)
def delete_expense(expense_id: int) -> Any:
    """Permanently delete an expense. Confirm with the user first."""
    return _request("DELETE", f"/expenses/{expense_id}")


@mcp.tool(annotations=WRITE)
def attach_receipt(expense_id: int, file_path: str) -> Any:
    """Upload (or replace) a receipt for an expense from a file on this computer (PDF or image)."""
    p = Path(file_path).expanduser()
    if not p.is_file():
        raise ExpensesApiError(f"File not found: {p}")
    ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    with p.open("rb") as fh:
        return _request("POST", f"/expenses/{expense_id}/receipt", files={"receipt": (p.name, fh, ctype)})


@mcp.tool(annotations=DELETE)
def delete_receipt(expense_id: int) -> Any:
    """Remove the receipt attached to an expense."""
    return _request("DELETE", f"/expenses/{expense_id}/receipt")


@mcp.tool(annotations=UPDATE)
def resolve_action_item(item_id: int) -> Any:
    """Mark an action item (e.g. unpaid rent alert) as resolved.

    For a statement_not_stored item this means "keep that transaction out": later imports skip it.
    Confirm with the user before resolving one of those.
    """
    return _request("POST", f"/expenses/action-items/{item_id}/resolve")


# --------------------------------------------------------------------------- categories


@mcp.tool(annotations=WRITE)
def create_category(name: str, keywords: list[str] | None = None) -> Any:
    """Create a category. Keywords are case-sensitive substrings matched against transaction descriptions."""
    return _request("POST", "/categories", json={"name": name, "keywords": keywords or []})


@mcp.tool(annotations=UPDATE)
def update_category(category_id: int, name: str, keywords: list[str]) -> Any:
    """Rename a category and/or replace its keywords, then re-categorize matching expenses.

    Renames propagate to non-overridden expenses; keywords are re-applied to all matching expenses,
    including overridden ones. Pass the full keyword list (it replaces the existing one).
    """
    return _request("PUT", f"/categories/{category_id}", json={"name": name, "keywords": keywords})


@mcp.tool(annotations=DELETE)
def delete_category(category_id: int) -> Any:
    """Delete a category. Confirm with the user first."""
    return _request("DELETE", f"/categories/{category_id}")


# --------------------------------------------------------------------------- rental properties


@mcp.tool(annotations=WRITE)
def create_rental_property(
    alias: str,
    address: str,
    tenant: str | None = None,
    lease_renewal_date: str | None = None,
    payment_day: int | None = None,
) -> Any:
    """Add a rental property. `payment_day` is the day of month rent is due (drives unpaid-rent alerts)."""
    return _request(
        "POST",
        "/rental-properties",
        json=_clean(
            dict(alias=alias, address=address, tenant=tenant, lease_renewal_date=lease_renewal_date, payment_day=payment_day)
        ),
    )


@mcp.tool(annotations=UPDATE)
def update_rental_property(
    property_id: int,
    alias: str,
    address: str,
    tenant: str | None = None,
    lease_renewal_date: str | None = None,
    payment_day: int | None = None,
) -> Any:
    """Replace a rental property's details (alias and address are required; omitted optional fields are cleared)."""
    return _request(
        "PUT",
        f"/rental-properties/{property_id}",
        json=dict(alias=alias, address=address, tenant=tenant, lease_renewal_date=lease_renewal_date, payment_day=payment_day),
    )


@mcp.tool(annotations=UPDATE)
def sync_property_expenses(property_id: int) -> Any:
    """Link unassigned expenses to a property by matching its tenant name in descriptions."""
    return _request("POST", f"/rental-properties/{property_id}/sync-expenses")


@mcp.tool(annotations=DELETE)
def delete_rental_property(property_id: int) -> Any:
    """Delete a rental property. Confirm with the user first."""
    return _request("DELETE", f"/rental-properties/{property_id}")


# --------------------------------------------------------------------------- vehicles


@mcp.tool(annotations=WRITE)
def create_vehicle(alias: str, make: str, model: str, year: int, registration_due_date: str | None = None) -> Any:
    """Add a vehicle."""
    return _request(
        "POST",
        "/vehicles",
        json=_clean(dict(alias=alias, make=make, model=model, year=year, registration_due_date=registration_due_date)),
    )


@mcp.tool(annotations=UPDATE)
def update_vehicle(
    vehicle_id: int, alias: str, make: str, model: str, year: int, registration_due_date: str | None = None
) -> Any:
    """Replace a vehicle's details."""
    return _request(
        "PUT",
        f"/vehicles/{vehicle_id}",
        json=dict(alias=alias, make=make, model=model, year=year, registration_due_date=registration_due_date),
    )


@mcp.tool(annotations=DELETE)
def delete_vehicle(vehicle_id: int) -> Any:
    """Delete a vehicle and all its service records. Confirm with the user first."""
    return _request("DELETE", f"/vehicles/{vehicle_id}")


@mcp.tool(annotations=WRITE)
def add_vehicle_service(vehicle_id: int, date: str, description: str, mileage: int | None = None) -> Any:
    """Add a maintenance record (date YYYY-MM-DD) to a vehicle."""
    return _request(
        "POST", f"/vehicles/{vehicle_id}/services", json=_clean(dict(date=date, description=description, mileage=mileage))
    )


@mcp.tool(annotations=UPDATE)
def update_vehicle_service(
    vehicle_id: int, service_id: int, date: str, description: str, mileage: int | None = None
) -> Any:
    """Replace a vehicle maintenance record."""
    return _request(
        "PUT",
        f"/vehicles/{vehicle_id}/services/{service_id}",
        json=dict(date=date, description=description, mileage=mileage),
    )


@mcp.tool(annotations=DELETE)
def delete_vehicle_service(vehicle_id: int, service_id: int) -> Any:
    """Delete a vehicle maintenance record."""
    return _request("DELETE", f"/vehicles/{vehicle_id}/services/{service_id}")


# --------------------------------------------------------------------------- imports


@mcp.tool(annotations=WRITE)
def upload_statement(bank: str, year: str, month: str, file_path: str) -> Any:
    """Upload a bank statement PDF from this computer.

    bank: citi, wellsfargo, chase or banamex. year: YYYY. month: three-letter lowercase name
    (jan, feb, ..., dec). Replaces any statement already stored for that bank/month. After
    uploading, call run_import_pipeline to load its transactions into the database.
    """
    p = Path(file_path).expanduser()
    if not p.is_file():
        raise ExpensesApiError(f"File not found: {p}")
    with p.open("rb") as fh:
        return _request("POST", f"/statements/{bank}/{year}/{month}", files={"file": (p.name, fh, "application/pdf")})


@mcp.tool(annotations=READ)
def reconcile_statements(year: str, bank: str | None = None, month: str | None = None) -> Any:
    """Check uploaded statements against their own printed totals and the stored expenses.

    For each statement of the year (optionally one bank and/or one month, jan..dec): the totals
    read by the parser, the totals printed on the statement, whether they agree (`adds_up`), and
    any transactions on the statement that are not in the database (`missing`). `complete` is true
    when the statement adds up and every transaction is stored. Read-only; to load missing rows,
    run_import_pipeline for that bank and month.
    """
    return _request(
        "GET",
        f"/reconciliation/{year}",
        params=dict(bank=bank, month=month),
        timeout=max(TIMEOUT, 300),
    )


@mcp.tool(annotations=WRITE)
def run_import_pipeline(
    year: str,
    citi_months: list[str] | None = None,
    wellsfargo_months: list[str] | None = None,
    chase_months: list[str] | None = None,
    banamex_months: list[str] | None = None,
) -> Any:
    """Import uploaded statement PDFs into the database (parse, categorize, upsert).

    Months are three-letter lowercase names, e.g. citi_months=["sep", "oct"]. Re-importing a month
    is safe: rows are upserted on (date, bank, description, debit, credit).

    Overridden expenses keep their manual category. Returns the pipeline's progress log.
    """
    return _request(
        "POST",
        "/pipeline/run",
        json=dict(
            year=year,
            citi_months=citi_months or [],
            wellsfargo_months=wellsfargo_months or [],
            chase_months=chase_months or [],
            banamex_months=banamex_months or [],
        ),
        timeout=max(TIMEOUT, 600),
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
