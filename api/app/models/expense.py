"""Expense ORM model."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Expense(Base):
    """A single expense assigned to a category.

    Attributes:
        id: Surrogate primary key.
        category_id: Owning category (deletion restricted).
        amount: Strictly positive amount.
        description: Optional free text.
        spent_at: Day the money was spent.
        created_at: Server-side creation timestamp (timezone-aware).
    """

    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_expenses_category_id_spent_at", "category_id", "spent_at"),
        Index("ix_expenses_spent_at", "spent_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str | None] = mapped_column(String(255))
    spent_at: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
