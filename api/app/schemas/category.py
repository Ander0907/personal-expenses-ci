"""Pydantic schemas for categories."""

import unicodedata
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


def ensure_no_control_characters(value: str, field: str) -> str:
    """Reject text containing control characters.

    Args:
        value: Text to check.
        field: Field name used in the error message.

    Returns:
        The unchanged text.

    Raises:
        ValueError: If any character is in Unicode category ``Cc``.
    """
    if any(unicodedata.category(char) == "Cc" for char in value):
        raise ValueError(f"{field} must not contain control characters")
    return value


Money = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


class CategoryCreate(BaseModel):
    """Payload to create a category.

    Attributes:
        name: Unique category name (1-100 characters, whitespace stripped).
        monthly_budget: Non-negative budget with at most two decimals.
        is_active: Whether expenses may be assigned to the category.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: Annotated[str, Field(min_length=1, max_length=100)]
    monthly_budget: Money
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        """Reject names containing control characters.

        Args:
            value: Name after whitespace stripping.

        Returns:
            The unchanged name.

        Raises:
            ValueError: If any character is in Unicode category ``Cc``.
        """
        return ensure_no_control_characters(value, "name")


class CategoryRead(BaseModel):
    """Category as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    monthly_budget: Decimal
    is_active: bool
