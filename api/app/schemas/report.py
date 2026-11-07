"""Schemas for the monthly report."""

from decimal import Decimal

from pydantic import BaseModel


class CategoryReport(BaseModel):
    """Spending of one category over a month.

    Attributes:
        category_id: Category primary key.
        name: Category name.
        monthly_budget: Monthly budget of the category.
        total_spent: Amount spent in the month.
        percent_used: Share of the budget consumed, or None for a zero budget.
        over_budget: Whether spending exceeds the budget.
    """

    category_id: int
    name: str
    monthly_budget: Decimal
    total_spent: Decimal
    percent_used: Decimal | None
    over_budget: bool


class MonthlyReport(BaseModel):
    """Spending report for a calendar month.

    Attributes:
        year: Calendar year.
        month: Month number (1-12).
        total_spent: Amount spent across all categories.
        categories: Per-category breakdown.
    """

    year: int
    month: int
    total_spent: Decimal
    categories: list[CategoryReport]
