"""Pydantic schemas for expenses."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.limits import MAX_DB_INT
from app.schemas.category import ensure_no_control_characters


class ExpenseCreate(BaseModel):
    """Payload to create an expense.

    Attributes:
        category_id: Target category id.
        amount: Strictly positive amount with at most two decimals.
        description: Optional text (max 255); blank becomes None.
        spent_at: Day the money was spent.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category_id: Annotated[int, Field(ge=1, le=MAX_DB_INT)]
    amount: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
    description: Annotated[str | None, Field(max_length=255)] = None
    spent_at: date

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        """Turn blank descriptions into None and reject control characters.

        Args:
            value: Description after whitespace stripping.

        Returns:
            The description, or None when blank.

        Raises:
            ValueError: If the text contains control characters.
        """
        if not value:
            return None
        return ensure_no_control_characters(value, "description")


class ExpenseRead(BaseModel):
    """Expense as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    amount: Decimal
    description: str | None
    spent_at: date
    created_at: datetime


class ExpenseCreated(ExpenseRead):
    """Newly created expense with the budget flag.

    Attributes:
        over_budget: True when the month total exceeds the category budget.
    """

    over_budget: bool
