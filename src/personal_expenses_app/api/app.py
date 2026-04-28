import os
from decimal import Decimal
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import Column, Integer, Numeric, String, UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session

_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(_project_root / ".env")

app = FastAPI(title="Personal Expenses API", version="1.0.0")


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


def _get_engine():
    connection_string = os.environ.get("DATABASE_URL")
    if not connection_string:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return create_engine(connection_string)


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

    @field_validator("debit", "credit", mode="before")
    @classmethod
    def nan_to_none(cls, v):
        if isinstance(v, Decimal) and v.is_nan():
            return None
        return v

    model_config = {"from_attributes": True}


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
        total=total,
        limit=limit,
        offset=offset,
        items=[ExpenseResponse.model_validate(r) for r in rows],
    )


@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, session: Session = Depends(get_session)):
    """Return a single expense by its ID."""
    row = session.get(_AllExpense, expense_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found.")
    return ExpenseResponse.model_validate(row)

