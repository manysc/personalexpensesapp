import math
import json
import os
import re
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import Boolean, Column, Integer, Numeric, String, Text, UniqueConstraint, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.exc import IntegrityError

from personal_expenses_app.core.rule_based_expense_categorizer import RULE_BASED_CATEGORIES

_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(_project_root / ".env")

RECEIPTS_DIR = Path(os.environ.get("RECEIPTS_DIR", str(_project_root / "receipts")))
_ALLOWED_RECEIPT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".heif"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_migrations(_get_engine())
    yield


app = FastAPI(title="Personal Expenses API", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# DB setup (reuses the same schema as ExpenseDbPersistence)
# ---------------------------------------------------------------------------

class _Base(DeclarativeBase):
    pass


class _RentalProperty(_Base):
    __tablename__ = "rental_properties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alias = Column(String(100), nullable=False, unique=True)
    address = Column(String(500), nullable=False)
    tenant = Column(String(200), nullable=True)
    lease_renewal_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    payment_day = Column(Integer, nullable=True)  # Day of month 1-31


class _Vehicle(_Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alias = Column(String(100), nullable=False, unique=True)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    registration_due_date = Column(String(10), nullable=True)  # YYYY-MM-DD


class _VehicleService(_Base):
    __tablename__ = "vehicle_services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    description = Column(String(500), nullable=False)
    mileage = Column(Integer, nullable=True)


class _AllExpense(_Base):
    __tablename__ = "all_expenses"
    __table_args__ = (
        UniqueConstraint(
            "date", "bank", "description", "debit", "credit",
            name="uix_expense_natural_key",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(20), nullable=False)
    bank = Column(String(50), nullable=False)
    description = Column(String(500), nullable=False)
    debit = Column(Numeric(12, 2), nullable=True)
    credit = Column(Numeric(12, 2), nullable=True)
    category = Column(String(100), nullable=True)
    overridden = Column(Boolean, nullable=False, default=False, server_default="false")
    comments = Column(String(2000), nullable=True)
    property_id = Column(Integer, nullable=True)  # FK to rental_properties.id
    vehicle_id = Column(Integer, nullable=True)  # FK to vehicles.id
    receipt_filename = Column(String(500), nullable=True)


class _Category(_Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    keywords = Column(Text, nullable=False, default="[]")  # JSON array of strings


def _get_engine():
    connection_string = os.environ.get("DATABASE_URL")
    if not connection_string:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return create_engine(connection_string)


def _run_migrations(engine) -> None:
    """Apply incremental schema migrations."""
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS rental_properties ("
                "  id SERIAL PRIMARY KEY, "
                "  alias VARCHAR(100) NOT NULL UNIQUE, "
                "  address VARCHAR(500) NOT NULL, "
                "  tenant VARCHAR(200), "
                "  lease_renewal_date VARCHAR(10), "
                "  payment_day INTEGER "
                ");"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'rental_properties' AND column_name = 'lease_renewal_date' "
                "  ) THEN "
                "    ALTER TABLE rental_properties ADD COLUMN lease_renewal_date VARCHAR(10); "
                "  END IF; "
                "END $$;"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'rental_properties' AND column_name = 'payment_date' "
                "  ) THEN "
                "    ALTER TABLE rental_properties DROP COLUMN payment_date; "
                "  END IF; "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'rental_properties' AND column_name = 'payment_day' "
                "  ) THEN "
                "    ALTER TABLE rental_properties ADD COLUMN payment_day INTEGER; "
                "  END IF; "
                "END $$;"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'all_expenses' AND column_name = 'overridden' "
                "  ) THEN "
                "    ALTER TABLE all_expenses "
                "    ADD COLUMN overridden BOOLEAN NOT NULL DEFAULT FALSE; "
                "  END IF; "
                "END $$;"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'all_expenses' AND column_name = 'comments' "
                "  ) THEN "
                "    ALTER TABLE all_expenses "
                "    ADD COLUMN comments VARCHAR(2000); "
                "  END IF; "
                "END $$;"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'all_expenses' AND column_name = 'property_id' "
                "  ) THEN "
                "    ALTER TABLE all_expenses "
                "    ADD COLUMN property_id INTEGER REFERENCES rental_properties(id) ON DELETE SET NULL; "
                "  END IF; "
                "END $$;"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS categories ("
                "  id SERIAL PRIMARY KEY, "
                "  name VARCHAR(100) NOT NULL UNIQUE, "
                "  keywords TEXT NOT NULL DEFAULT '[]' "
                ");"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS vehicles ("
                "  id SERIAL PRIMARY KEY, "
                "  alias VARCHAR(100) NOT NULL UNIQUE, "
                "  make VARCHAR(100) NOT NULL, "
                "  model VARCHAR(100) NOT NULL, "
                "  year INTEGER NOT NULL, "
                "  registration_due_date VARCHAR(10) "
                ");"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'vehicles' AND column_name = 'alias' "
                "  ) THEN "
                "    ALTER TABLE vehicles ADD COLUMN alias VARCHAR(100) NOT NULL DEFAULT ''; "
                "    UPDATE vehicles SET alias = make || ' ' || model || ' ' || year || ' #' || id "
                "    WHERE alias = ''; "
                "    CREATE UNIQUE INDEX IF NOT EXISTS uix_vehicles_alias ON vehicles(alias); "
                "    ALTER TABLE vehicles ALTER COLUMN alias DROP DEFAULT; "
                "  END IF; "
                "END $$;"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS vehicle_services ("
                "  id SERIAL PRIMARY KEY, "
                "  vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE, "
                "  date VARCHAR(10) NOT NULL, "
                "  description VARCHAR(500) NOT NULL, "
                "  mileage INTEGER "
                ");"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'all_expenses' AND column_name = 'vehicle_id' "
                "  ) THEN "
                "    ALTER TABLE all_expenses "
                "    ADD COLUMN vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE SET NULL; "
                "  END IF; "
                "END $$;"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'all_expenses' AND column_name = 'receipt_filename' "
                "  ) THEN "
                "    ALTER TABLE all_expenses "
                "    ADD COLUMN receipt_filename VARCHAR(500); "
                "  END IF; "
                "END $$;"
            )
        )
        conn.commit()


def get_session():
    engine = _get_engine()
    with Session(engine) as session:
        yield session


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ExpenseResponse(BaseModel):
    id: int
    date: str
    bank: str
    description: str
    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None
    category: Optional[str] = None
    overridden: bool = False
    comments: Optional[str] = None
    property_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    receipt_filename: Optional[str] = None

    @field_validator("debit", "credit", mode="before")
    @classmethod
    def nan_to_none(cls, v):
        if isinstance(v, Decimal) and v.is_nan():
            return None
        return v

    model_config = {"from_attributes": True}


class CategoryOverrideRequest(BaseModel):
    category: str


class ExpenseUpdateRequest(BaseModel):
    """Partial-update request for manual expense fields.

    Only fields present in the JSON body are updated; missing fields are left
    unchanged.  Any provided field marks the expense as overridden.
    """
    category: Optional[str] = None
    comments: Optional[str] = None
    property_id: Optional[int] = None
    vehicle_id: Optional[int] = None


class ExpenseListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ExpenseResponse]


class ExpenseCreateRequest(BaseModel):
    date: str
    bank: str
    description: str
    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None
    category: Optional[str] = None
    comments: Optional[str] = None
    property_id: Optional[int] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    keywords: list[str]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_row(cls, row: "_Category") -> "CategoryResponse":
        return cls(  # type: ignore[call-arg]
            id=row.id,
            name=row.name,
            keywords=json.loads(row.keywords or "[]"),  # type: ignore[arg-type]
        )


class CategoryRequest(BaseModel):
    name: str
    keywords: list[str] = []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(
    body: ExpenseCreateRequest,
    session: Session = Depends(get_session),
):
    """Create a new expense manually."""
    if body.property_id is not None:
        prop = session.get(_RentalProperty, body.property_id)
        if prop is None:
            raise HTTPException(status_code=404, detail=f"Rental property {body.property_id} not found.")
    row = _AllExpense(
        date=body.date,
        bank=body.bank,
        description=body.description,
        debit=body.debit,
        credit=body.credit,
        category=body.category,
        overridden=True,
        comments=body.comments,
        property_id=body.property_id,
    )
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="An expense with this date, bank, description, debit, and credit already exists.",
        )
    session.refresh(row)
    return ExpenseResponse.model_validate(row)


@app.get("/expenses", response_model=ExpenseListResponse)
def list_expenses(
    bank: Optional[str] = Query(default=None, description="Filter by bank name"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    date_from: Optional[str] = Query(default=None, description="Include expenses on or after this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(default=None, description="Include expenses on or before this date (YYYY-MM-DD)"),
    description: Optional[str] = Query(default=None, description="Filter by description substring (case-insensitive)"),
    comments: Optional[str] = Query(default=None, description="Filter by comments substring (case-insensitive)"),
    property_id: Optional[int] = Query(default=None, description="Filter by rental property ID"),
    vehicle_id: Optional[int] = Query(default=None, description="Filter by vehicle ID"),
    overridden_only: bool = Query(default=False, description="If true, return only manually overridden expenses"),

    limit: int = Query(default=100, ge=1, le=1000, description="Max number of results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    session: Session = Depends(get_session),
):
    """Return a paginated list of expenses with optional filters."""
    stmt = select(_AllExpense)

    if bank is not None:
        stmt = stmt.where(_AllExpense.bank == bank)
    if category is not None:
        stmt = stmt.where(_AllExpense.category == category)
    if date_from is not None:
        stmt = stmt.where(_AllExpense.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(_AllExpense.date <= date_to)
    if description is not None:
        stmt = stmt.where(_AllExpense.description.ilike(f"%{description}%"))
    if comments is not None:
        stmt = stmt.where(_AllExpense.comments.ilike(f"%{comments}%"))
    if property_id is not None:
        stmt = stmt.where(_AllExpense.property_id == property_id)
    if vehicle_id is not None:
        stmt = stmt.where(_AllExpense.vehicle_id == vehicle_id)
    if overridden_only:
        stmt = stmt.where(_AllExpense.overridden.is_(True))

    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.scalar(count_stmt)

    rows = session.execute(
        stmt.order_by(_AllExpense.date.desc(), _AllExpense.id.desc())
            .limit(limit)
            .offset(offset)
    ).scalars().all()

    return ExpenseListResponse(
        total=total or 0,
        limit=limit,
        offset=offset,
        items=[ExpenseResponse.model_validate(r) for r in rows],
    )


class SummaryItem(BaseModel):
    month: str
    category: str
    total: float


class CommentedExpense(BaseModel):
    id: int
    date: str
    description: str
    category: Optional[str]
    comments: str
    debit: Optional[float] = None
    credit: Optional[float] = None


@app.get("/expenses/comments", response_model=list[CommentedExpense])
def expenses_comments(
    date_from: Optional[str] = Query(default=None, description="Include expenses on or after this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(default=None, description="Include expenses on or before this date (YYYY-MM-DD)"),
    session: Session = Depends(get_session),
):
    """Return all expenses that have a non-empty comment, optionally filtered by date range."""
    stmt = (
        select(_AllExpense)
        .where(_AllExpense.comments.isnot(None))
        .where(_AllExpense.comments != "")
    )
    if date_from is not None:
        stmt = stmt.where(_AllExpense.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(_AllExpense.date <= date_to)
    stmt = stmt.order_by(_AllExpense.date.asc(), _AllExpense.id.asc())
    rows = session.execute(stmt).scalars().all()
    def _safe(v) -> Optional[float]:
        if v is None:
            return None
        f = float(v)
        return f if math.isfinite(f) else None

    return [
        CommentedExpense(
            id=r.id,
            date=r.date,
            description=r.description,
            category=r.category,
            comments=r.comments,
            debit=_safe(r.debit),
            credit=_safe(r.credit),
        )
        for r in rows
    ]


@app.get("/expenses/summary")
def expenses_summary(
    date_from: Optional[str] = Query(default=None, description="Include expenses on or after this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(default=None, description="Include expenses on or before this date (YYYY-MM-DD)"),
    session: Session = Depends(get_session),
):
    """Return total net expenses (debit - credit) grouped by month (YYYY-MM) and category."""
    conditions = ["category IS NOT NULL"]
    params: dict = {}

    if date_from is not None:
        conditions.append("date >= :date_from")
        params["date_from"] = date_from
    if date_to is not None:
        conditions.append("date <= :date_to")
        params["date_to"] = date_to

    where_clause = " AND ".join(conditions)
    sql = text(f"""
        SELECT
            substring(date, 1, 7) AS month,
            category,
            SUM(CASE WHEN debit IS NULL OR debit = 'NaN'::numeric THEN 0 ELSE debit END)::float  AS debit_total,
            SUM(CASE WHEN credit IS NULL OR credit = 'NaN'::numeric THEN 0 ELSE credit END)::float AS credit_total
        FROM all_expenses
        WHERE {where_clause}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)

    rows = session.execute(sql, params).fetchall()

    def safe_float(v) -> float:
        if v is None:
            return 0.0
        f = float(v)
        return f if math.isfinite(f) else 0.0

    result = [
        {
            "month": r[0],
            "category": r[1],
            "total": safe_float(r[2]) - safe_float(r[3]),
        }
        for r in rows
    ]
    return JSONResponse(content=result)


@app.get("/expenses/property-summary")
def expenses_property_summary(
    date_from: Optional[str] = Query(default=None, description="Include expenses on or after this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(default=None, description="Include expenses on or before this date (YYYY-MM-DD)"),
    session: Session = Depends(get_session),
):
    """Return net expenses (debit - credit) grouped by month and rental property alias."""
    conditions = ["e.property_id IS NOT NULL"]
    params: dict = {}

    if date_from is not None:
        conditions.append("e.date >= :date_from")
        params["date_from"] = date_from
    if date_to is not None:
        conditions.append("e.date <= :date_to")
        params["date_to"] = date_to

    where_clause = " AND ".join(conditions)
    sql = text(f"""
        SELECT
            substring(e.date, 1, 7) AS month,
            p.alias AS property,
            SUM(CASE WHEN e.debit IS NULL OR e.debit = 'NaN'::numeric THEN 0 ELSE e.debit END)::float  AS debit_total,
            SUM(CASE WHEN e.credit IS NULL OR e.credit = 'NaN'::numeric THEN 0 ELSE e.credit END)::float AS credit_total
        FROM all_expenses e
        JOIN rental_properties p ON e.property_id = p.id
        WHERE {where_clause}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)

    rows = session.execute(sql, params).fetchall()

    def safe_float(v) -> float:
        if v is None:
            return 0.0
        f = float(v)
        return f if math.isfinite(f) else 0.0

    result = [
        {
            "month": r[0],
            "property": r[1],
            "total": safe_float(r[2]) - safe_float(r[3]),
        }
        for r in rows
    ]
    return JSONResponse(content=result)


@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, session: Session = Depends(get_session)):
    """Return a single expense by its ID."""
    row = session.get(_AllExpense, expense_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found.")
    return ExpenseResponse.model_validate(row)


@app.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    body: ExpenseUpdateRequest,
    session: Session = Depends(get_session),
):
    """Partially update an expense's manual fields and mark it as overridden.

    Only fields present in the request body are updated.  Any provided field
    marks the expense as overridden so that bulk re-imports won't revert the
    manual changes.
    """
    row = session.get(_AllExpense, expense_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found.")

    updated = False
    if "category" in body.model_fields_set:
        row.category = body.category
        updated = True
    if "comments" in body.model_fields_set:
        row.comments = body.comments
        updated = True
    if "property_id" in body.model_fields_set:
        if body.property_id is not None:
            prop = session.get(_RentalProperty, body.property_id)
            if prop is None:
                raise HTTPException(status_code=404, detail=f"Rental property {body.property_id} not found.")
        row.property_id = body.property_id
        updated = True
    if "vehicle_id" in body.model_fields_set:
        if body.vehicle_id is not None:
            veh = session.get(_Vehicle, body.vehicle_id)
            if veh is None:
                raise HTTPException(status_code=404, detail=f"Vehicle {body.vehicle_id} not found.")
        row.vehicle_id = body.vehicle_id
        updated = True

    if updated:
        row.overridden = True
        session.commit()
    session.refresh(row)
    return ExpenseResponse.model_validate(row)


class BulkUpdateRequest(BaseModel):
    ids: list[int]
    category: Optional[str] = None
    comments: Optional[str] = None
    property_id: Optional[int] = None
    vehicle_id: Optional[int] = None


@app.post("/expenses/bulk-update", response_model=list[int])
def bulk_update_expenses(
    body: BulkUpdateRequest,
    session: Session = Depends(get_session),
):
    """Apply the same field update to multiple expenses at once.

    Only fields present in the request body are modified; others are left
    unchanged.  All updated expenses are marked as overridden.
    Returns the list of IDs that were successfully updated.
    """
    if not body.ids:
        return []

    fields_set = body.model_fields_set - {"ids"}
    if not fields_set:
        raise HTTPException(status_code=422, detail="At least one field to update must be provided.")

    updated_ids: list[int] = []
    for expense_id in body.ids:
        row = session.get(_AllExpense, expense_id)
        if row is None:
            continue
        if "category" in fields_set:
            row.category = body.category
        if "comments" in fields_set:
            row.comments = body.comments
        if "property_id" in fields_set:
            if body.property_id is not None:
                prop = session.get(_RentalProperty, body.property_id)
                if prop is None:
                    raise HTTPException(status_code=404, detail=f"Rental property {body.property_id} not found.")
            row.property_id = body.property_id
        if "vehicle_id" in fields_set:
            if body.vehicle_id is not None:
                veh = session.get(_Vehicle, body.vehicle_id)
                if veh is None:
                    raise HTTPException(status_code=404, detail=f"Vehicle {body.vehicle_id} not found.")
            row.vehicle_id = body.vehicle_id
        row.overridden = True
        updated_ids.append(expense_id)

    session.commit()
    return updated_ids


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, session: Session = Depends(get_session)):
    """Delete an expense by its ID."""
    row = session.get(_AllExpense, expense_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found.")
    session.delete(row)
    session.commit()


# ---------------------------------------------------------------------------
# Receipt upload / download / delete
# ---------------------------------------------------------------------------

@app.post("/expenses/{expense_id}/receipt", response_model=ExpenseResponse)
async def upload_receipt(
    expense_id: int,
    receipt: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Upload (or replace) a receipt file for an expense."""
    row = session.get(_AllExpense, expense_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found.")

    original_name = receipt.filename or "receipt"
    safe_name = re.sub(r"[^\w\-.]", "_", original_name)
    ext = Path(safe_name).suffix.lower()
    if ext not in _ALLOWED_RECEIPT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' is not allowed. Accepted: {', '.join(sorted(_ALLOWED_RECEIPT_EXTENSIONS))}",
        )

    stored_name = f"{expense_id}_{safe_name}"

    # Remove old receipt file if present
    if row.receipt_filename:
        old_path = RECEIPTS_DIR / row.receipt_filename
        if old_path.exists():
            old_path.unlink()

    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = (RECEIPTS_DIR / stored_name).resolve()
    if not str(dest).startswith(str(RECEIPTS_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    contents = await receipt.read()
    dest.write_bytes(contents)

    row.receipt_filename = stored_name
    session.commit()
    session.refresh(row)
    return ExpenseResponse.model_validate(row)


@app.get("/expenses/{expense_id}/receipt")
def get_receipt(
    expense_id: int,
    inline: bool = Query(default=False, description="If true, set Content-Disposition to inline (view in browser)"),
    session: Session = Depends(get_session),
):
    """Download or view the receipt attached to an expense."""
    row = session.get(_AllExpense, expense_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found.")
    if not row.receipt_filename:
        raise HTTPException(status_code=404, detail="No receipt attached to this expense.")

    file_path = (RECEIPTS_DIR / row.receipt_filename).resolve()
    if not str(file_path).startswith(str(RECEIPTS_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid receipt path.")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Receipt file not found on disk.")

    # Strip the leading "{expense_id}_" prefix for a clean download name
    prefix = f"{expense_id}_"
    display_name = row.receipt_filename[len(prefix):] if row.receipt_filename.startswith(prefix) else row.receipt_filename

    return FileResponse(
        path=str(file_path),
        filename=display_name,
        content_disposition_type="inline" if inline else "attachment",
    )


@app.delete("/expenses/{expense_id}/receipt", status_code=204)
def delete_receipt(
    expense_id: int,
    session: Session = Depends(get_session),
):
    """Remove the receipt attached to an expense."""
    row = session.get(_AllExpense, expense_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found.")
    if not row.receipt_filename:
        raise HTTPException(status_code=404, detail="No receipt attached to this expense.")

    file_path = (RECEIPTS_DIR / row.receipt_filename).resolve()
    if str(file_path).startswith(str(RECEIPTS_DIR.resolve())) and file_path.exists():
        file_path.unlink()

    row.receipt_filename = None
    session.commit()


@app.patch("/expenses/{expense_id}/category", response_model=ExpenseResponse)
def override_category(
    expense_id: int,
    body: CategoryOverrideRequest,
    session: Session = Depends(get_session),
):
    """Override the category of an expense and mark it as manually overridden."""
    row = session.get(_AllExpense, expense_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found.")
    row.category = body.category
    row.overridden = True
    session.commit()
    session.refresh(row)
    return ExpenseResponse.model_validate(row)


@app.get("/categories", response_model=list[CategoryResponse])
def list_categories(session: Session = Depends(get_session)):
    """Return all categories sorted by name."""
    rows = session.execute(
        select(_Category).order_by(_Category.name)
    ).scalars().all()
    return [CategoryResponse.from_orm_row(r) for r in rows]


@app.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(body: CategoryRequest, session: Session = Depends(get_session)):
    """Create a new category."""
    row = _Category(name=body.name.strip(), keywords=json.dumps(body.keywords))
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Category '{body.name}' already exists.")
    session.refresh(row)
    return CategoryResponse.from_orm_row(row)


@app.get("/banks", response_model=list[str])
def list_banks(session: Session = Depends(get_session)):
    """Return all distinct bank names sorted alphabetically."""
    rows = session.execute(
        select(_AllExpense.bank)
        .where(_AllExpense.bank.isnot(None))
        .distinct()
        .order_by(_AllExpense.bank)
    ).scalars().all()
    return rows


@app.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    body: CategoryRequest,
    session: Session = Depends(get_session),
):
    """Update an existing category."""
    row = session.get(_Category, category_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found.")
    row.name = body.name.strip()
    row.keywords = json.dumps(body.keywords)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Category '{body.name}' already exists.")
    session.refresh(row)
    return CategoryResponse.from_orm_row(row)


@app.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, session: Session = Depends(get_session)):
    """Delete a category."""
    row = session.get(_Category, category_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found.")
    session.delete(row)
    session.commit()


@app.post("/categories/seed", status_code=200)
def seed_categories(session: Session = Depends(get_session)):
    """Seed the categories table from the rule-based categorizer definitions.

    Existing categories are left unchanged; only missing ones are inserted.
    Returns counts of inserted and skipped categories.
    """
    inserted = 0
    skipped = 0
    for name, keywords in RULE_BASED_CATEGORIES.items():
        existing = session.execute(
            select(_Category).where(_Category.name == name)
        ).scalar_one_or_none()
        if existing is None:
            session.add(_Category(name=name, keywords=json.dumps(keywords)))
            inserted += 1
        else:
            skipped += 1
    session.commit()
    return {"inserted": inserted, "skipped": skipped}


# ---------------------------------------------------------------------------
# Rental properties models and routes
# ---------------------------------------------------------------------------

class RentalPropertyResponse(BaseModel):
    id: int
    alias: str
    address: str
    tenant: Optional[str] = None
    lease_renewal_date: Optional[str] = None
    payment_day: Optional[int] = None

    model_config = {"from_attributes": True}


class RentalPropertyRequest(BaseModel):
    alias: str
    address: str
    tenant: Optional[str] = None
    lease_renewal_date: Optional[str] = None
    payment_day: Optional[int] = None


@app.get("/rental-properties", response_model=list[RentalPropertyResponse])
def list_rental_properties(session: Session = Depends(get_session)):
    """Return all rental properties sorted by alias."""
    rows = session.execute(
        select(_RentalProperty).order_by(_RentalProperty.alias)
    ).scalars().all()
    return [RentalPropertyResponse.model_validate(r) for r in rows]


@app.post("/rental-properties", response_model=RentalPropertyResponse, status_code=201)
def create_rental_property(
    body: RentalPropertyRequest,
    session: Session = Depends(get_session),
):
    """Create a new rental property."""
    row = _RentalProperty(
        alias=body.alias,
        address=body.address,
        tenant=body.tenant,
        lease_renewal_date=body.lease_renewal_date,
        payment_day=body.payment_day,
    )
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"A property with alias '{body.alias}' already exists.")
    session.refresh(row)
    return RentalPropertyResponse.model_validate(row)


@app.put("/rental-properties/{property_id}", response_model=RentalPropertyResponse)
def update_rental_property(
    property_id: int,
    body: RentalPropertyRequest,
    session: Session = Depends(get_session),
):
    """Update an existing rental property."""
    row = session.get(_RentalProperty, property_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Rental property {property_id} not found.")
    row.alias = body.alias
    row.address = body.address
    row.tenant = body.tenant
    row.lease_renewal_date = body.lease_renewal_date
    row.payment_day = body.payment_day
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"A property with alias '{body.alias}' already exists.")
    session.refresh(row)
    return RentalPropertyResponse.model_validate(row)


@app.delete("/rental-properties/{property_id}", status_code=204)
def delete_rental_property(
    property_id: int,
    session: Session = Depends(get_session),
):
    """Delete a rental property."""
    row = session.get(_RentalProperty, property_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Rental property {property_id} not found.")
    session.delete(row)
    session.commit()


# ---------------------------------------------------------------------------
# Vehicle models and routes
# ---------------------------------------------------------------------------

class VehicleResponse(BaseModel):
    id: int
    alias: str
    make: str
    model: str
    year: int
    registration_due_date: Optional[str] = None

    model_config = {"from_attributes": True}


class VehicleRequest(BaseModel):
    alias: str
    make: str
    model: str
    year: int
    registration_due_date: Optional[str] = None


class VehicleServiceResponse(BaseModel):
    id: int
    vehicle_id: int
    date: str
    description: str
    mileage: Optional[int] = None

    model_config = {"from_attributes": True}


class VehicleServiceRequest(BaseModel):
    date: str
    description: str
    mileage: Optional[int] = None


@app.get("/vehicles", response_model=list[VehicleResponse])
def list_vehicles(session: Session = Depends(get_session)):
    """Return all vehicles sorted by year descending, then make/model."""
    rows = session.execute(
        select(_Vehicle).order_by(_Vehicle.year.desc(), _Vehicle.make, _Vehicle.model)
    ).scalars().all()
    return [VehicleResponse.model_validate(r) for r in rows]


@app.post("/vehicles", response_model=VehicleResponse, status_code=201)
def create_vehicle(body: VehicleRequest, session: Session = Depends(get_session)):
    """Create a new vehicle."""
    row = _Vehicle(
        alias=body.alias.strip(),
        make=body.make.strip(),
        model=body.model.strip(),
        year=body.year,
        registration_due_date=body.registration_due_date,
    )
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"A vehicle with alias '{body.alias}' already exists.")
    session.refresh(row)
    return VehicleResponse.model_validate(row)


@app.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int, session: Session = Depends(get_session)):
    """Return a single vehicle by ID."""
    row = session.get(_Vehicle, vehicle_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found.")
    return VehicleResponse.model_validate(row)


@app.put("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    body: VehicleRequest,
    session: Session = Depends(get_session),
):
    """Update an existing vehicle."""
    row = session.get(_Vehicle, vehicle_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found.")
    row.alias = body.alias.strip()
    row.make = body.make.strip()
    row.model = body.model.strip()
    row.year = body.year
    row.registration_due_date = body.registration_due_date
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"A vehicle with alias '{body.alias}' already exists.")
    session.refresh(row)
    return VehicleResponse.model_validate(row)


@app.delete("/vehicles/{vehicle_id}", status_code=204)
def delete_vehicle(vehicle_id: int, session: Session = Depends(get_session)):
    """Delete a vehicle and its associated services."""
    row = session.get(_Vehicle, vehicle_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found.")
    session.delete(row)
    session.commit()


@app.get("/vehicles/{vehicle_id}/services", response_model=list[VehicleServiceResponse])
def list_vehicle_services(vehicle_id: int, session: Session = Depends(get_session)):
    """Return all maintenance services for a vehicle, sorted by date descending."""
    vehicle = session.get(_Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found.")
    rows = session.execute(
        select(_VehicleService)
        .where(_VehicleService.vehicle_id == vehicle_id)
        .order_by(_VehicleService.date.desc(), _VehicleService.id.desc())
    ).scalars().all()
    return [VehicleServiceResponse.model_validate(r) for r in rows]


@app.post("/vehicles/{vehicle_id}/services", response_model=VehicleServiceResponse, status_code=201)
def create_vehicle_service(
    vehicle_id: int,
    body: VehicleServiceRequest,
    session: Session = Depends(get_session),
):
    """Add a maintenance service record to a vehicle."""
    vehicle = session.get(_Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found.")
    row = _VehicleService(
        vehicle_id=vehicle_id,
        date=body.date,
        description=body.description.strip(),
        mileage=body.mileage,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return VehicleServiceResponse.model_validate(row)


@app.put("/vehicles/{vehicle_id}/services/{service_id}", response_model=VehicleServiceResponse)
def update_vehicle_service(
    vehicle_id: int,
    service_id: int,
    body: VehicleServiceRequest,
    session: Session = Depends(get_session),
):
    """Update a maintenance service record."""
    row = session.get(_VehicleService, service_id)
    if row is None or row.vehicle_id != vehicle_id:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found for vehicle {vehicle_id}.")
    row.date = body.date
    row.description = body.description.strip()
    row.mileage = body.mileage
    session.commit()
    session.refresh(row)
    return VehicleServiceResponse.model_validate(row)


@app.delete("/vehicles/{vehicle_id}/services/{service_id}", status_code=204)
def delete_vehicle_service(
    vehicle_id: int,
    service_id: int,
    session: Session = Depends(get_session),
):
    """Delete a maintenance service record."""
    row = session.get(_VehicleService, service_id)
    if row is None or row.vehicle_id != vehicle_id:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found for vehicle {vehicle_id}.")
    session.delete(row)
    session.commit()

