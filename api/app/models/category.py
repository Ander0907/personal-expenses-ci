"""Category ORM model."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Category(Base):
    """Spending category with a monthly budget.

    Attributes:
        id: Surrogate primary key.
        name: Unique category name.
        monthly_budget: Non-negative monthly budget.
        is_active: Whether new expenses may be assigned to the category.
    """

    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("monthly_budget >= 0", name="monthly_budget_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    monthly_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    is_active: Mapped[bool] = mapped_column(server_default=true())
