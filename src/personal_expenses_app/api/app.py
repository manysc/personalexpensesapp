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

    @field_validator("debit", "credit", mode="before")
    @classmethod
    def nan_to_none(cls, v):
        if isinstance(v, Decimal) and v.is_nan():
            return None
        return v

    model_config = {"from_attributes": True}


class CategoryOverrideRequest(BaseModel):
    category: str


class CommentsUpdateRequest(BaseModel):
    comments: str


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


@app.patch("/expenses/{expense_id}/comments", response_model=ExpenseResponse)
def update_comments(
    expense_id: int,
    body: CommentsUpdateRequest,
    session: Session = Depends(get_session),
):
    """Update the free-text comments of an expense."""
    row = session.get(_AllExpense, expense_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found.")
    row.comments = body.comments
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

