import contextlib
import functools
import io
import math
import json
import mimetypes
import os
import queue
import re
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text, UniqueConstraint, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.exc import IntegrityError

from personal_expenses_app.core.rule_based_expense_categorizer import RULE_BASED_CATEGORIES, RuleBasedExpenseCategorizer
from personal_expenses_app.core.summarizer import Summarizer
from personal_expenses_app.core.tenant_matching import tenant_match_tokens
from personal_expenses_app.infrastructure import s3_storage
from personal_expenses_app.infrastructure.expense_db_persistence import ExpenseDbPersistence
from personal_expenses_app.infrastructure.statement_import import LOADERS, StatementBatch, statement_key
from personal_expenses_app.infrastructure.statement_period import period_from_filename
from personal_expenses_app.infrastructure.statement_reconciliation import (
    FOLLOW_UP_TYPES,
    STATEMENT_NOT_IMPORTED,
    STATEMENT_NOT_STORED,
    FollowUp,
    statement_follow_ups,
    transaction_fingerprint,
    unreadable_statement_follow_up,
)
from personal_expenses_app.interface.user_interaction import UserInteraction

_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(_project_root / ".env")

RECEIPTS_PREFIX = "receipts/"
_ALLOWED_RECEIPT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".heif"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_migrations(_get_engine())
    s3_storage.ensure_bucket_exists()
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
            postgresql_nulls_not_distinct=True,
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
    balanced_date = Column(String(10), nullable=True)  # YYYY-MM-DD override for summary grouping
    vehicle_id = Column(Integer, nullable=True)  # FK to vehicles.id
    receipt_filename = Column(String(500), nullable=True)
    amortize_months = Column(Integer, nullable=True)  # spread this expense's amount across N months in summaries
    amortize_start_date = Column(String(10), nullable=True)  # YYYY-MM-DD start month for amortization


class _Category(_Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    keywords = Column(Text, nullable=False, default="[]")  # JSON array of strings


class _ActionItem(_Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_key = Column(String(200), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    property_id = Column(Integer, nullable=True)  # FK to rental_properties.id
    month = Column(String(7), nullable=False)  # YYYY-MM
    message = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, default="open", server_default="open")
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    resolved_at = Column(DateTime, nullable=True)


@functools.cache
def _get_engine():
    """Return the process-wide engine, so every request shares one connection pool."""
    connection_string = os.environ.get("DATABASE_URL")
    if not connection_string:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return create_engine(connection_string, pool_pre_ping=True)


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
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'all_expenses' AND column_name = 'balanced_date' "
                "  ) THEN "
                "    ALTER TABLE all_expenses "
                "    ADD COLUMN balanced_date VARCHAR(10); "
                "  END IF; "
                "END $$;"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'all_expenses' AND column_name = 'amortize_months' "
                "  ) THEN "
                "    ALTER TABLE all_expenses "
                "    ADD COLUMN amortize_months INTEGER; "
                "  END IF; "
                "END $$;"
            )
        )
        conn.execute(
            text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS ( "
                "    SELECT 1 FROM information_schema.columns "
                "    WHERE table_name = 'all_expenses' AND column_name = 'amortize_start_date' "
                "  ) THEN "
                "    ALTER TABLE all_expenses "
                "    ADD COLUMN amortize_start_date VARCHAR(10); "
                "  END IF; "
                "END $$;"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS action_items ("
                "  id SERIAL PRIMARY KEY, "
                "  action_key VARCHAR(200) NOT NULL UNIQUE, "
                "  type VARCHAR(50) NOT NULL, "
                "  property_id INTEGER REFERENCES rental_properties(id) ON DELETE SET NULL, "
                "  month VARCHAR(7) NOT NULL, "
                "  message VARCHAR(500) NOT NULL, "
                "  status VARCHAR(20) NOT NULL DEFAULT 'open', "
                "  created_at TIMESTAMP NOT NULL DEFAULT now(), "
                "  resolved_at TIMESTAMP "
                ");"
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
    balanced_date: Optional[str] = None
    amortize_months: Optional[int] = None
    amortize_start_date: Optional[str] = None

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
    balanced_date: Optional[str] = None
    amortize_months: Optional[int] = Field(default=None, ge=1, le=36)
    amortize_start_date: Optional[str] = None
    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None


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
    balanced_date: Optional[str] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    keywords: list[str]
    updated_expenses: Optional[int] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_row(cls, row: "_Category", updated_expenses: Optional[int] = None) -> "CategoryResponse":
        return cls(  # type: ignore[call-arg]
            id=row.id,
            name=row.name,
            keywords=json.loads(row.keywords or "[]"),  # type: ignore[arg-type]
            updated_expenses=updated_expenses,
        )


class CategoryRequest(BaseModel):
    name: str
    keywords: list[str] = []


class ActionItemResponse(BaseModel):
    id: int
    action_key: str
    type: str
    property_id: Optional[int] = None
    month: str
    message: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


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
        balanced_date=body.balanced_date,
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

    limit: int = Query(default=100, ge=1, le=10000, description="Max number of results to return"),
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
        next_day = (datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        stmt = stmt.where(_AllExpense.date < next_day)
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
    property: Optional[str] = None
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
        next_day = (datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        stmt = stmt.where(_AllExpense.date < next_day)
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
    """Return total net expenses (debit - credit) grouped by month (YYYY-MM), category, and rental property.

    Expenses with `amortize_months` > 1 are spread evenly across that many
    months starting at `amortize_start_date` (falling back to `balanced_date`,
    then `date`), so a single transaction can contribute a fraction of its
    total to several consecutive months. Date filters are applied against the
    resulting (post-amortization) month, not the original transaction date.
    `property` is the linked rental property's alias, or null when the expense
    isn't linked to one; summing `total` across `property` for a given
    month/category reproduces the previous property-agnostic totals.
    """
    conditions = []
    params: dict = {}

    if date_from is not None:
        conditions.append("month_date >= CAST(:date_from AS date)")
        params["date_from"] = date_from
    if date_to is not None:
        next_day = (datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        conditions.append("month_date < CAST(:date_to_exclusive AS date)")
        params["date_to_exclusive"] = next_day

    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    sql = text(f"""
        WITH amort AS (
            SELECT
                category,
                property_id,
                (
                    CASE WHEN debit IS NULL OR debit = 'NaN'::numeric THEN 0 ELSE debit END
                    - CASE WHEN credit IS NULL OR credit = 'NaN'::numeric THEN 0 ELSE credit END
                ) AS net,
                GREATEST(COALESCE(amortize_months, 1), 1) AS months,
                COALESCE(amortize_start_date, balanced_date, date)::date AS start_date
            FROM all_expenses
            WHERE category IS NOT NULL
        ),
        expanded AS (
            SELECT
                a.category,
                a.property_id,
                date_trunc('month', a.start_date) + (gs.n || ' month')::interval AS month_date,
                CASE
                    WHEN gs.n < a.months - 1 THEN round(a.net / a.months, 2)
                    ELSE a.net - round(a.net / a.months, 2) * (a.months - 1)
                END AS amount
            FROM amort a
            CROSS JOIN LATERAL generate_series(0, a.months - 1) AS gs(n)
        )
        SELECT
            to_char(expanded.month_date, 'YYYY-MM') AS month,
            expanded.category,
            p.alias AS property,
            SUM(expanded.amount)::float AS total
        FROM expanded
        LEFT JOIN rental_properties p ON expanded.property_id = p.id
        WHERE {where_clause}
        GROUP BY 1, 2, 3
        ORDER BY 1, 2, 3
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
            "property": r[2],
            "total": safe_float(r[3]),
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
    """Return net expenses (debit - credit) grouped by month and rental property alias.

    Expenses with `amortize_months` > 1 are spread evenly across that many
    months, same as `/expenses/summary`.
    """
    conditions = []
    params: dict = {}

    if date_from is not None:
        conditions.append("month_date >= CAST(:date_from AS date)")
        params["date_from"] = date_from
    if date_to is not None:
        next_day = (datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        conditions.append("month_date < CAST(:date_to_exclusive AS date)")
        params["date_to_exclusive"] = next_day

    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    sql = text(f"""
        WITH amort AS (
            SELECT
                e.property_id,
                (
                    CASE WHEN e.debit IS NULL OR e.debit = 'NaN'::numeric THEN 0 ELSE e.debit END
                    - CASE WHEN e.credit IS NULL OR e.credit = 'NaN'::numeric THEN 0 ELSE e.credit END
                ) AS net,
                GREATEST(COALESCE(e.amortize_months, 1), 1) AS months,
                COALESCE(e.amortize_start_date, e.balanced_date, e.date)::date AS start_date
            FROM all_expenses e
            WHERE e.property_id IS NOT NULL
        ),
        expanded AS (
            SELECT
                a.property_id,
                date_trunc('month', a.start_date) + (gs.n || ' month')::interval AS month_date,
                CASE
                    WHEN gs.n < a.months - 1 THEN round(a.net / a.months, 2)
                    ELSE a.net - round(a.net / a.months, 2) * (a.months - 1)
                END AS amount
            FROM amort a
            CROSS JOIN LATERAL generate_series(0, a.months - 1) AS gs(n)
        )
        SELECT
            to_char(expanded.month_date, 'YYYY-MM') AS month,
            p.alias AS property,
            SUM(expanded.amount)::float AS total
        FROM expanded
        JOIN rental_properties p ON expanded.property_id = p.id
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
            "total": safe_float(r[2]),
        }
        for r in rows
    ]
    return JSONResponse(content=result)


# ---------------------------------------------------------------------------
# Action items (dashboard notifications)
# ---------------------------------------------------------------------------

UTILITY_CHANGE_THRESHOLD = 0.05  # 5% month-over-month change triggers an alert


def _upsert_action_item(
    session: Session,
    action_key: str,
    type_: str,
    property_id: Optional[int],
    month: str,
    message: str,
) -> None:
    """Insert a newly-detected action item, leaving existing ones (and their
    resolved status) untouched."""
    session.execute(
        text(
            "INSERT INTO action_items (action_key, type, property_id, month, message) "
            "VALUES (:action_key, :type, :property_id, :month, :message) "
            "ON CONFLICT (action_key) DO NOTHING"
        ),
        {
            "action_key": action_key,
            "type": type_,
            "property_id": property_id,
            "month": month,
            "message": message,
        },
    )


def _match_utility_vendor(description: str, keywords: list[str]) -> Optional[str]:
    """Return the first Utilities keyword found (case-insensitive) in the description."""
    desc_upper = description.upper()
    for kw in keywords:
        if kw.upper() in desc_upper:
            return kw
    return None


def _previous_calendar_month(month: str) -> str:
    """Given 'YYYY-MM', return the immediately preceding calendar month in the same format."""
    year, mon = (int(part) for part in month.split("-"))
    if mon == 1:
        return f"{year - 1}-12"
    return f"{year}-{mon - 1:02d}"

def _resolve_action_item(
    session: Session,
    key: str,
    resolution_message: str,
) -> None:
    session.execute(
        text(
            """
            UPDATE action_items
            SET status = 'resolved',
                resolved_at = COALESCE(resolved_at, CURRENT_TIMESTAMP)
            WHERE action_key = :key
              AND status <> 'resolved'
            """
        ),
        {
            "key": key
        },
    )


def _detect_action_items(session: Session) -> None:
    """Detect unpaid rent and utility-payment changes, persisting any newly
    found issues. Already-persisted items (open or resolved) are left as-is."""
    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    today_day = now.day

    # 1) Rent unpaid: current month only, no grace period.
    properties = session.execute(
        text("SELECT id, alias, payment_day FROM rental_properties WHERE payment_day IS NOT NULL")
    ).fetchall()
    for prop_id, alias, payment_day in properties:
        key = f"rent_unpaid:{prop_id}:{current_month}"
        if today_day < payment_day:
            continue
        paid = session.execute(
            text(
                "SELECT 1 FROM all_expenses "
                "WHERE category = 'Real State' AND property_id = :pid "
                "AND CASE WHEN credit IS NULL OR credit = 'NaN'::numeric THEN 0 ELSE credit END > 0 "
                "AND to_char(COALESCE(balanced_date, date)::date, 'YYYY-MM') = :month "
                "LIMIT 1"
            ),
            {"pid": prop_id, "month": current_month},
        ).fetchone()

        if paid is not None:
            _resolve_action_item(
                session,
                key,
                f"Rent for {alias} was paid for {current_month}.",
            )
            continue

        # Do not create an action before the due date.
        if today_day < payment_day:
            continue

        message = f"Rent for {alias} hasn't been paid for {current_month}."
        _upsert_action_item(
            session,
            key,
            "rent_unpaid",
            prop_id,
            current_month,
            message,
        )

    # 2) Utility payment changed: >=5% month-over-month change for the same
    # vendor (derived from the Utilities category keyword list) and property.
    rows = session.execute(
        text(
            "SELECT property_id, description, "
            "(CASE WHEN debit IS NULL OR debit = 'NaN'::numeric THEN 0 ELSE debit END) "
            "- (CASE WHEN credit IS NULL OR credit = 'NaN'::numeric THEN 0 ELSE credit END) AS net, "
            "to_char(COALESCE(balanced_date, date)::date, 'YYYY-MM') AS month "
            "FROM all_expenses WHERE category = 'Utilities'"
        )
    ).fetchall()

    utility_keywords = RULE_BASED_CATEGORIES.get("Utilities", [])
    totals: dict[tuple[Optional[int], str], dict[str, float]] = {}
    for property_id, description, net, month in rows:
        vendor = _match_utility_vendor(description, utility_keywords)
        if vendor is None:
            continue
        month_totals = totals.setdefault((property_id, vendor), {})
        month_totals[month] = month_totals.get(month, 0.0) + float(net)

    property_alias_by_id = {
        r[0]: r[1] for r in session.execute(text("SELECT id, alias FROM rental_properties")).fetchall()
    }

    for (property_id, vendor), month_totals in totals.items():
        months_sorted = sorted(month_totals.keys())
        latest_month = months_sorted[-1]
        prior_month = _previous_calendar_month(latest_month)
        if prior_month not in month_totals:
            continue
        prior_amount = month_totals[prior_month]
        latest_amount = month_totals[latest_month]
        if prior_amount == 0:
            continue
        pct_change = abs(latest_amount - prior_amount) / abs(prior_amount)
        if pct_change < UTILITY_CHANGE_THRESHOLD:
            continue
        prop_label = f" for {property_alias_by_id[property_id]}" if property_id in property_alias_by_id else ""
        key = f"utility_changed:{property_id or 'none'}:{vendor}:{latest_month}"
        message = (
            f"{vendor} payment{prop_label} changed from ${prior_amount:,.2f} to "
            f"${latest_amount:,.2f} in {latest_month}."
        )
        _upsert_action_item(session, key, "utility_changed", property_id, latest_month, message)

    session.commit()


def _record_statement_follow_ups(follow_ups_by_statement: dict[str, list[FollowUp]]) -> str:
    """Make the statements' open action items match their latest check; return a one-line verdict.

    A problem found for the first time opens an item. An open item whose problem is gone
    is deleted. A resolved item is left alone: resolving one is how a person says "seen,
    nothing to do" (e.g. a row deleted on purpose), so the same problem does not reopen
    it; a different problem with the statement opens a new item.
    """
    with Session(_get_engine()) as session:
        for statement, follow_ups in follow_ups_by_statement.items():
            current = {f"{f.type}:{statement}:{f.fingerprint}": f for f in follow_ups}
            for type_ in FOLLOW_UP_TYPES:
                prefix = f"{type_}:{statement}:"
                session.execute(
                    text(
                        "DELETE FROM action_items WHERE status = 'open' "
                        "AND left(action_key, :length) = :prefix AND NOT (action_key = ANY(:current))"
                    ),
                    {"length": len(prefix), "prefix": prefix, "current": list(current)},
                )
            filed = period_from_filename(statement)
            month = f"{filed[0]}-{filed[1]:02d}" if filed else "0000-00"
            for action_key, follow_up in current.items():
                _upsert_action_item(session, action_key, follow_up.type, None, month, follow_up.message)
        session.commit()

    needing = [s.rsplit("/", 1)[-1] for s, follow_ups in follow_ups_by_statement.items() if follow_ups]
    if not needing:
        return (
            f"All {len(follow_ups_by_statement)} statement(s) add up to their printed totals "
            f"and are fully stored."
        )
    return (
        f"WARNING: {len(needing)} of {len(follow_ups_by_statement)} statement(s) need follow-up: "
        f"{', '.join(needing)}. See Action Items on the dashboard."
    )


def _rows_where(df: pd.DataFrame, flags: list[bool]) -> pd.DataFrame:
    return df[pd.Series(flags, index=df.index, dtype=bool)]


def _split_kept_out(statement: str, transactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a statement's transactions into those to store and those a person keeps out.

    Keeping one out is resolving its "not in app" action item ("Keep out" in the UI): it
    was removed from the app on purpose, so imports must not bring it back.
    """
    prefix = f"{STATEMENT_NOT_STORED}:{statement}:"
    with Session(_get_engine()) as session:
        keys = session.execute(
            text(
                "SELECT action_key FROM action_items "
                "WHERE status = 'resolved' AND left(action_key, :length) = :prefix"
            ),
            {"length": len(prefix), "prefix": prefix},
        ).scalars()
        kept_out = {key[len(prefix):] for key in keys}
    if not kept_out:
        return transactions, transactions.iloc[0:0]

    transactions = ExpenseDbPersistence.with_stored_descriptions(transactions)
    is_kept_out = [transaction_fingerprint(row) in kept_out for row in transactions.itertuples()]
    return (
        _rows_where(transactions, [not flag for flag in is_kept_out]),
        _rows_where(transactions, is_kept_out),
    )


class LoadMissingResponse(BaseModel):
    loaded: int


@app.post("/expenses/action-items/{item_id}/load", response_model=LoadMissingResponse)
def load_missing_transactions(item_id: int):
    """Load what an open "not in app" action item is about: one transaction, or all for the statement."""
    with Session(_get_engine()) as session:
        item = session.get(_ActionItem, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"Action item {item_id} not found.")
        item_type, action_key, status = item.type, item.action_key, item.status
    if item_type not in (STATEMENT_NOT_STORED, STATEMENT_NOT_IMPORTED) or status != "open":
        raise HTTPException(status_code=400, detail="Only open 'not in app' action items can be loaded.")

    statement, fingerprint = action_key[len(item_type) + 1:].rsplit(":", 1)
    bank = statement.split("/")[1]
    db = ExpenseDbPersistence(engine=_get_engine())
    with StatementBatch([statement]) as batch:
        transactions, reconciliation = batch.read(bank, statement)
    to_store, _ = _split_kept_out(statement, transactions)

    missing = db.find_missing(to_store)
    if item_type == STATEMENT_NOT_STORED:
        missing = _rows_where(missing, [transaction_fingerprint(row) == fingerprint for row in missing.itertuples()])
    if not missing.empty:
        categorizer = RuleBasedExpenseCategorizer(_load_category_keywords())
        db.save_expenses(categorizer.categorize_expenses(missing.copy()))
        _link_properties_by_tenant()

    _record_statement_follow_ups({statement: statement_follow_ups(reconciliation, db.find_missing(to_store))})
    return LoadMissingResponse(loaded=len(missing))


@app.get("/expenses/action-items", response_model=list[ActionItemResponse])
def list_action_items(
    include_resolved: bool = Query(default=False, description="Include already-resolved items"),
    session: Session = Depends(get_session),
):
    """Detect (and persist) new action items, then return open ones (or all, if requested)."""
    _detect_action_items(session)
    stmt = select(_ActionItem)
    if not include_resolved:
        stmt = stmt.where(_ActionItem.status == "open")
    stmt = stmt.order_by(_ActionItem.created_at.desc())
    rows = session.execute(stmt).scalars().all()
    return [ActionItemResponse.model_validate(r) for r in rows]


@app.post("/expenses/action-items/{item_id}/resolve", response_model=ActionItemResponse)
def resolve_action_item(item_id: int, session: Session = Depends(get_session)):
    """Mark an action item as resolved, hiding it from the default action list."""
    row = session.get(_ActionItem, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Action item {item_id} not found.")
    row.status = "resolved"
    row.resolved_at = datetime.now()
    session.commit()
    session.refresh(row)
    return ActionItemResponse.model_validate(row)


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
    if "balanced_date" in body.model_fields_set:
        row.balanced_date = body.balanced_date
        updated = True
    if "amortize_months" in body.model_fields_set:
        row.amortize_months = body.amortize_months
        updated = True
    if "amortize_start_date" in body.model_fields_set:
        row.amortize_start_date = body.amortize_start_date
        updated = True
    if "debit" in body.model_fields_set or "credit" in body.model_fields_set:
        if row.bank != "cash":
            raise HTTPException(
                status_code=400,
                detail="Debit/credit can only be edited for cash expenses.",
            )
        if "debit" in body.model_fields_set:
            row.debit = body.debit
        if "credit" in body.model_fields_set:
            row.credit = body.credit
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

    # Remove old receipt object if present
    if row.receipt_filename:
        s3_storage.delete_object(f"{RECEIPTS_PREFIX}{row.receipt_filename}")

    contents = await receipt.read()
    s3_storage.put_object_bytes(f"{RECEIPTS_PREFIX}{stored_name}", contents)

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

    try:
        contents = s3_storage.get_object_bytes(f"{RECEIPTS_PREFIX}{row.receipt_filename}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Receipt file not found in storage.")

    # Strip the leading "{expense_id}_" prefix for a clean download name
    prefix = f"{expense_id}_"
    display_name = row.receipt_filename[len(prefix):] if row.receipt_filename.startswith(prefix) else row.receipt_filename

    media_type = mimetypes.guess_type(display_name)[0] or "application/octet-stream"
    disposition = "inline" if inline else "attachment"
    return Response(
        content=contents,
        media_type=media_type,
        headers={"Content-Disposition": f'{disposition}; filename="{display_name}"'},
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

    s3_storage.delete_object(f"{RECEIPTS_PREFIX}{row.receipt_filename}")

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
    """Update an existing category and re-categorize matching expenses.

    Renaming propagates to non-overridden expenses only. Keyword re-apply
    updates any expense (including overridden ones) whose current category
    doesn't already match this category's name.
    """
    row = session.get(_Category, category_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found.")
    old_name = str(row.name)  # type: ignore[arg-type]
    new_name = body.name.strip()
    row.name = new_name
    row.keywords = json.dumps(body.keywords)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Category '{body.name}' already exists.")
    session.refresh(row)

    total_updated = 0

    # If renamed, propagate new name to non-overridden expenses that had the old name
    if old_name != new_name:
        result = session.execute(
            text("UPDATE all_expenses SET category = :new WHERE category = :old AND overridden = false"),
            {"new": new_name, "old": old_name},
        )
        total_updated += result.rowcount  # type: ignore[attr-defined]

    # Re-apply keywords: update expenses matching any keyword whose category is
    # not already this one. This includes overridden expenses whose category is
    # stale/wrong relative to the keyword match; the overridden flag itself is
    # left unchanged.
    if body.keywords:
        conditions = " OR ".join(f"description ILIKE :kw{i}" for i in range(len(body.keywords)))
        params: dict = {"cat": new_name}
        params.update({f"kw{i}": f"%{kw}%" for i, kw in enumerate(body.keywords)})
        result = session.execute(
            text(f"UPDATE all_expenses SET category = :cat WHERE category IS DISTINCT FROM :cat AND ({conditions})"),
            params,
        )
        total_updated += result.rowcount  # type: ignore[attr-defined]

    session.commit()
    return CategoryResponse.from_orm_row(row, updated_expenses=total_updated)


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


class SyncExpensesResponse(BaseModel):
    updated: int


def _sync_property_by_tenant(session: Session, prop: "_RentalProperty") -> int:
    """Assign prop to expenses whose description contains keywords from its tenant name.

    The tenant string is split on whitespace and '&' into name tokens (2+ characters),
    matched case-insensitively against the expense description. Tokens that also appear
    in another property's tenant name (e.g. a shared first name) are ignored because they
    can't tell the properties apart; any one of the remaining tokens is enough. So with
    tenants "Jose Tellez & Veronica Flores" and "Jose Soto & ...", a payment from
    "Veronica Flores" links to the first property and one from just "Jose" links to
    neither. If every token is shared, all of them must match.
    See core/tenant_matching.py.

    Only expenses with no property yet are touched, so a manual assignment is
    never overwritten. Returns the number of expenses updated.
    """
    if not prop.tenant:
        return 0

    from sqlalchemy import and_, func, or_, update as sa_update

    property_id = prop.id

    other_tenants = [
        other.tenant
        for other in session.execute(
            select(_RentalProperty).where(_RentalProperty.id != property_id)
        ).scalars()
        if other.tenant
    ]
    keywords, require_all = tenant_match_tokens(prop.tenant, other_tenants)
    if not keywords:
        return 0

    conditions = [
        func.lower(_AllExpense.description).contains(kw)
        for kw in keywords
    ]
    match_condition = and_(*conditions) if require_all else or_(*conditions)

    stmt = (
        sa_update(_AllExpense)
        .where(match_condition, _AllExpense.property_id.is_(None))
        .values(property_id=property_id)
        .execution_options(synchronize_session="fetch")
    )
    result = session.execute(stmt)
    session.commit()
    return result.rowcount  # type: ignore[attr-defined]


@app.post("/rental-properties/{property_id}/sync-expenses", response_model=SyncExpensesResponse)
def sync_expenses_by_tenant(
    property_id: int,
    session: Session = Depends(get_session),
):
    """Link unassigned expenses to this property based on its tenant name (see _sync_property_by_tenant)."""
    prop = session.get(_RentalProperty, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail=f"Rental property {property_id} not found.")
    return SyncExpensesResponse(updated=_sync_property_by_tenant(session, prop))


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


# ---------------------------------------------------------------------------
# Pipeline endpoint
# ---------------------------------------------------------------------------

_PIPELINE_MONTH_ORDER = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
]


class PipelineRunRequest(BaseModel):
    year: str
    citi_months: list[str] = []
    wellsfargo_months: list[str] = []
    chase_months: list[str] = []
    banamex_months: list[str] = []


def _load_category_keywords() -> Optional[dict[str, list[str]]]:
    """Return {category: keywords} from the categories table, in id order (first match wins).

    Returns None when the table is empty so the categorizer falls back to the
    hardcoded RULE_BASED_CATEGORIES.
    """
    with Session(_get_engine()) as session:
        rows = session.execute(select(_Category).order_by(_Category.id)).scalars().all()
        return {str(r.name): json.loads(r.keywords or "[]") for r in rows} or None  # type: ignore[arg-type]


def _link_properties_by_tenant() -> int:
    """Link unassigned expenses to every rental property that has a tenant."""
    total = 0
    with Session(_get_engine()) as session:
        for prop in session.execute(select(_RentalProperty)).scalars().all():
            total += _sync_property_by_tenant(session, prop)
    return total


@app.post("/pipeline/run")
def run_pipeline(body: PipelineRunRequest):
    q: queue.Queue = queue.Queue()

    class _QueueWriter(io.TextIOBase):
        def write(self, s: str) -> int:
            if s:
                q.put(s)
            return len(s)

        def flush(self) -> None:
            pass

    def _execute() -> None:
        year = body.year
        selected_months = {
            "citi": set(body.citi_months),
            "wellsfargo": set(body.wellsfargo_months),
            "chase": set(body.chase_months),
            "banamex": set(body.banamex_months),
        }
        categorizer = RuleBasedExpenseCategorizer(_load_category_keywords())
        db = ExpenseDbPersistence(engine=_get_engine())
        summarizer = Summarizer()
        user = UserInteraction()

        statements_by_month = {
            month: [
                (bank, statement_key(bank, year, month))
                for bank in LOADERS
                if month in selected_months[bank]
            ]
            for month in _PIPELINE_MONTH_ORDER
        }
        statement_keys = [key for statements in statements_by_month.values() for _, key in statements]
        all_labeled: list = []
        read_statements: list = []  # (reconciliation, transactions), checked once all are saved.
        follow_ups: dict[str, list[FollowUp]] = {}

        started = time.perf_counter()
        with StatementBatch(statement_keys) as batch:
            for month, statements in statements_by_month.items():
                if not statements:
                    continue
                print(f"\nProcessing {month} {year}...")
                dfs = []
                for bank, key in statements:
                    try:
                        df, reconciliation = batch.read(bank, key)
                    except ValueError as exc:  # Not understood; the other statements still load.
                        print(f"ERROR: {exc}")
                        follow_ups[key] = [unreadable_statement_follow_up(key, exc)]
                        continue
                    print(reconciliation.describe())
                    df, kept_out = _split_kept_out(key, df)
                    if not kept_out.empty:
                        print(
                            f"Left out {len(kept_out)} transaction(s) of {key.rsplit('/', 1)[-1]} "
                            f"that were kept out on purpose (resolved in Action Items)."
                        )
                    read_statements.append((reconciliation, df))
                    if not df.empty:
                        dfs.append(df)
                if not dfs:
                    print(f"No data loaded for {month} {year}")
                    continue

                combined = pd.concat(dfs, ignore_index=True)
                labeled = categorizer.categorize_expenses(combined)
                db.save_expenses(labeled)
                all_labeled.append(labeled)

        if statement_keys:
            elapsed = time.perf_counter() - started
            workers = batch.worker_processes
            reading = f", reading PDFs in {workers} worker processes" if workers else ""
            print(f"\nImported {len(statement_keys)} statement(s) in {elapsed:.1f}s{reading}.")
            for reconciliation, df in read_statements:
                follow_ups[reconciliation.statement] = statement_follow_ups(reconciliation, db.find_missing(df))
            print(_record_statement_follow_ups({key: follow_ups[key] for key in statement_keys if key in follow_ups}))

        if all_labeled:
            linked = _link_properties_by_tenant()
            print(f"Linked {linked} expense(s) to rental properties by tenant.")
            combined_all = pd.concat(all_labeled, ignore_index=True).drop_duplicates()
            for (year_val, month_val), group in combined_all.groupby(
                [combined_all["Date"].dt.year, combined_all["Date"].dt.month]
            ):
                summary = summarizer.summarize_by_category(group)
                summary["Month"] = pd.Timestamp(
                    year=int(year_val), month=int(month_val), day=1
                ).strftime("%b")
                summary["Year"] = str(year_val)
                user.print_summary(summary)
                user.print_total(summary)
        else:
            print("No expenses loaded. Check that the selected PDF files exist.")

    def _run() -> None:
        try:
            writer = _QueueWriter()
            with contextlib.redirect_stdout(writer):
                _execute()
        except Exception as exc:
            q.put(f"\nERROR: {exc}\n")
        finally:
            q.put(None)

    threading.Thread(target=_run, daemon=True).start()

    def _generate():
        while True:
            item = q.get()
            if item is None:
                break
            yield item

    return StreamingResponse(_generate(), media_type="text/plain; charset=utf-8")


# ---------------------------------------------------------------------------
# Statements endpoints (list / upload / download)
# ---------------------------------------------------------------------------

_VALID_BANKS: set[str] = {"citi", "wellsfargo", "chase", "banamex"}
_VALID_MONTHS_SET: set[str] = set(_PIPELINE_MONTH_ORDER)


@app.get("/statements/{bank}/{year}", response_model=list[str])
def list_statements(bank: str, year: str):
    """Return the months that have a statement PDF for the given bank and year."""
    if bank not in _VALID_BANKS:
        raise HTTPException(status_code=400, detail=f"Unknown bank: {bank}")
    existing_keys = set(s3_storage.list_keys(prefix=f"resources/{bank}/{year}/"))
    return [
        month for month in _PIPELINE_MONTH_ORDER
        if f"resources/{bank}/{year}/{bank}-{month}-{year}.pdf" in existing_keys
    ]


@app.post("/statements/{bank}/{year}/{month}", status_code=200)
async def upload_statement(bank: str, year: str, month: str, file: UploadFile = File(...)):
    """Upload a statement PDF for the given bank, year, and month."""
    if bank not in _VALID_BANKS:
        raise HTTPException(status_code=400, detail=f"Unknown bank: {bank}")
    if month not in _VALID_MONTHS_SET:
        raise HTTPException(status_code=400, detail=f"Unknown month: {month}")
    if not re.match(r"^\d{4}$", year):
        raise HTTPException(status_code=400, detail=f"Invalid year: {year}")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    content = await file.read()
    s3_storage.put_object_bytes(f"resources/{bank}/{year}/{bank}-{month}-{year}.pdf", content)
    return {"uploaded": True}


class MissingExpense(BaseModel):
    date: str
    description: str
    debit: Optional[float] = None
    credit: Optional[float] = None


class StatementReconciliationResponse(BaseModel):
    """One statement compared with its own printed totals and with the stored expenses."""
    bank: str
    month: str
    statement: str
    currency: str = "USD"  # Of the statement's totals; stored amounts are always US dollars.
    transactions: int = 0
    read_debits: float = 0
    read_credits: float = 0
    statement_debits: Optional[float] = None
    statement_credits: Optional[float] = None
    adds_up: Optional[bool] = None  # None: no totals were found on the statement.
    missing: list[MissingExpense] = []  # Read from the statement but not stored.
    kept_out: list[MissingExpense] = []  # Not stored on purpose ("Keep out" in Action Items).
    complete: bool = False  # The statement adds up and every transaction is stored.
    summary: str = ""


def _missing_expenses(transactions: pd.DataFrame) -> list[MissingExpense]:
    return [
        MissingExpense(
            date=str(row.Date),
            description=row.Description,
            debit=None if pd.isna(row.Debit) else row.Debit,
            credit=None if pd.isna(row.Credit) else row.Credit,
        )
        for row in transactions.itertuples()
    ]


def _reconcile_statement(
    batch: StatementBatch, db: ExpenseDbPersistence, bank: str, month: str, key: str
) -> tuple[StatementReconciliationResponse, list[FollowUp]]:
    result = StatementReconciliationResponse(bank=bank, month=month, statement=key)
    try:
        df, reconciliation = batch.read(bank, key)
    except ValueError as exc:
        result.summary = f"ERROR: {exc}"
        return result, [unreadable_statement_follow_up(key, exc)]

    to_store, kept_out = _split_kept_out(key, df)
    not_stored = db.find_missing(to_store)
    result.currency = reconciliation.currency
    result.transactions = len(df)
    result.read_debits = reconciliation.read.debits
    result.read_credits = reconciliation.read.credits
    if reconciliation.printed is not None:
        result.statement_debits = reconciliation.printed.debits
        result.statement_credits = reconciliation.printed.credits
    result.adds_up = reconciliation.matches
    result.missing = _missing_expenses(not_stored)
    result.kept_out = _missing_expenses(kept_out)
    result.complete = bool(reconciliation.matches) and not result.missing
    stored = (
        f"all {len(to_store)} are stored" if not result.missing
        else f"{len(result.missing)} of {len(to_store)} are NOT stored (see Action Items)"
    )
    if result.kept_out:
        stored += f", {len(result.kept_out)} kept out on purpose"
    result.summary = f"{reconciliation.describe()} In the database: {stored}."
    return result, statement_follow_ups(reconciliation, not_stored)


@app.get("/reconciliation/{year}", response_model=list[StatementReconciliationResponse])
def reconcile_statements(
    year: str,
    bank: Optional[str] = Query(default=None, description="Only this bank"),
    month: Optional[str] = Query(default=None, description="Only this month (jan..dec)"),
):
    """Check the uploaded statements of a year against their printed totals and the stored expenses.

    Read-only: each statement is parsed again, compared with the totals it prints, and
    its transactions are looked up in the database.
    """
    return [result for result, _ in _check_statements(year, bank, month)]


@app.post("/reconciliation/{year}", response_model=list[StatementReconciliationResponse])
def reconcile_statements_and_notify(
    year: str,
    bank: Optional[str] = Query(default=None, description="Only this bank"),
    month: Optional[str] = Query(default=None, description="Only this month (jan..dec)"),
):
    """Like GET, and also update the dashboard's action items with what needs follow-up.

    Transactions kept out on purpose are not reported as missing again.
    """
    checked = _check_statements(year, bank, month)
    _record_statement_follow_ups({result.statement: follow_ups for result, follow_ups in checked})
    return [result for result, _ in checked]


def _check_statements(
    year: str, bank: Optional[str], month: Optional[str]
) -> list[tuple[StatementReconciliationResponse, list[FollowUp]]]:
    """Re-read the year's uploaded statements (optionally one bank and/or month) and check each."""
    if bank is not None and bank not in _VALID_BANKS:
        raise HTTPException(status_code=400, detail=f"Unknown bank: {bank}")
    if month is not None and month not in _VALID_MONTHS_SET:
        raise HTTPException(status_code=400, detail=f"Unknown month: {month}")
    if not re.match(r"^\d{4}$", year):
        raise HTTPException(status_code=400, detail=f"Invalid year: {year}")

    statements = []
    for statement_bank in LOADERS:
        if bank not in (None, statement_bank):
            continue
        uploaded = set(s3_storage.list_keys(prefix=f"resources/{statement_bank}/{year}/"))
        for statement_month in _PIPELINE_MONTH_ORDER:
            key = statement_key(statement_bank, year, statement_month)
            if key in uploaded and month in (None, statement_month):
                statements.append((statement_bank, statement_month, key))

    db = ExpenseDbPersistence(engine=_get_engine())
    with StatementBatch([key for _, _, key in statements]) as batch:
        return [_reconcile_statement(batch, db, *statement) for statement in statements]


@app.get("/statements/{bank}/{year}/{month}")
def download_statement(bank: str, year: str, month: str):
    """Download a statement PDF for the given bank, year, and month."""
    if bank not in _VALID_BANKS:
        raise HTTPException(status_code=400, detail=f"Unknown bank: {bank}")
    if month not in _VALID_MONTHS_SET:
        raise HTTPException(status_code=400, detail=f"Unknown month: {month}")
    filename = f"{bank}-{month}-{year}.pdf"
    try:
        content = s3_storage.get_object_bytes(f"resources/{bank}/{year}/{filename}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Statement not found")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
    