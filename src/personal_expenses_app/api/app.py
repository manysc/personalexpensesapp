import math
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import Boolean, Column, Integer, Numeric, String, UniqueConstraint, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.exc import IntegrityError

_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(_project_root / ".env")

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


class ExpenseListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ExpenseResponse]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/expenses", response_model=ExpenseListResponse)
def list_expenses(
    bank: Optional[str] = Query(default=None, description="Filter by bank name"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    date_from: Optional[str] = Query(default=None, description="Include expenses on or after this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(default=None, description="Include expenses on or before this date (YYYY-MM-DD)"),
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

    if updated:
        row.overridden = True
        session.commit()
    session.refresh(row)
    return ExpenseResponse.model_validate(row)


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


@app.get("/categories", response_model=list[str])
def list_categories(session: Session = Depends(get_session)):
    """Return all distinct non-null categories sorted alphabetically."""
    rows = session.execute(
        select(_AllExpense.category)
        .where(_AllExpense.category.isnot(None))
        .distinct()
        .order_by(_AllExpense.category)
    ).scalars().all()
    return rows


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

