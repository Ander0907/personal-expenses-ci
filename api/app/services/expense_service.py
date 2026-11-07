"""Business rules for expenses."""

from dataclasses import dataclass

from app.core.clock import Clock
from app.core.dates import month_bounds, parse_year_month
from app.core.exceptions import (
    CategoryNotFoundError,
    ExpenseNotFoundError,
    FutureDateError,
    InactiveCategoryError,
    InvalidMonthError,
)
from app.models.expense import Expense
from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.expense import ExpenseCreate


@dataclass(frozen=True)
class CreatedExpense:
    """Result of creating an expense.

    Attributes:
        expense: The stored expense.
        over_budget: True when the month total exceeds the category budget.
    """

    expense: Expense
    over_budget: bool


class ExpenseService:
    """Creates, lists and deletes expenses."""

    def __init__(
        self,
        expenses: ExpenseRepository,
        categories: CategoryRepository,
        clock: Clock,
    ) -> None:
        """Initialize the service.

        Args:
            expenses: Expense repository.
            categories: Category repository.
            clock: Clock used for the future-date rule.
        """
        self._expenses = expenses
        self._categories = categories
        self._clock = clock

    def create(self, data: ExpenseCreate) -> CreatedExpense:
        """Create an expense and report whether it exceeds the budget.

        Notes:
            The expense is committed before the month total is computed. If
            the SUM query fails, the expense remains stored (accepted risk).
            Concurrent creates may both report ``over_budget``. The future-date
            rule uses the API clock (UTC in the container).

        Args:
            data: Validated creation payload.

        Returns:
            The stored expense and the over-budget flag.

        Raises:
            FutureDateError: If ``spent_at`` is after today.
            CategoryNotFoundError: If the category does not exist.
            InactiveCategoryError: If the category is inactive.
        """
        if data.spent_at > self._clock.today():
            raise FutureDateError(data.spent_at)
        category = self._categories.get(data.category_id)
        if category is None:
            raise CategoryNotFoundError(data.category_id)
        if not category.is_active:
            raise InactiveCategoryError(category.id)
        expense = self._expenses.add(
            Expense(
                category_id=data.category_id,
                amount=data.amount,
                description=data.description,
                spent_at=data.spent_at,
            )
        )
        start, end = month_bounds(data.spent_at.year, data.spent_at.month)
        total = self._expenses.monthly_total(data.category_id, start, end)
        return CreatedExpense(
            expense=expense, over_budget=total > category.monthly_budget
        )

    def list(
        self, category_id: int | None, month: str | None, limit: int, offset: int
    ) -> list[Expense]:
        """List expenses with optional category and month filters.

        Args:
            category_id: Restrict to this category when not None.
            month: ``YYYY-MM`` month filter, or None.
            limit: Maximum number of expenses.
            offset: Number of expenses to skip.

        Returns:
            The requested page of expenses.

        Raises:
            InvalidMonthError: If ``month`` is malformed or its year is
                outside 1-9998.
        """
        start = end = None
        if month is not None:
            try:
                start, end = month_bounds(*parse_year_month(month))
            except ValueError as error:
                raise InvalidMonthError(month) from error
        return self._expenses.list(
            category_id=category_id, start=start, end=end, limit=limit, offset=offset
        )

    def delete(self, expense_id: int) -> None:
        """Delete an expense.

        Args:
            expense_id: Id of the expense to remove.

        Raises:
            ExpenseNotFoundError: If the expense does not exist.
        """
        expense = self._expenses.get(expense_id)
        if expense is None:
            raise ExpenseNotFoundError(expense_id)
        self._expenses.delete(expense)
