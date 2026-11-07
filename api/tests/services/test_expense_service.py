"""Unit tests for ``app.services.expense_service``.

Repositories are autospec mocks and the clock is a fake fixed at 2026-11-06:
no session, no database, no real time.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import create_autospec

import pytest

from app.core.exceptions import (
    CategoryNotFoundError,
    ExpenseNotFoundError,
    FutureDateError,
    InactiveCategoryError,
    InvalidMonthError,
)
from app.models.category import Category
from app.models.expense import Expense
from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.expense import ExpenseCreate
from app.services.expense_service import CreatedExpense, ExpenseService

TODAY = date(2026, 11, 6)


class FakeClock:
    """Clock frozen at ``TODAY``."""

    def today(self) -> date:
        """Return the frozen date.

        Returns:
            ``TODAY``.
        """
        return TODAY


@pytest.fixture
def expenses() -> ExpenseRepository:
    """Provide an autospec expense repository whose ``add`` echoes its input.

    Returns:
        A mock ``ExpenseRepository``.
    """
    mock = create_autospec(ExpenseRepository, instance=True)
    mock.add.side_effect = lambda expense: expense
    mock.monthly_total.return_value = Decimal("0")
    return mock


@pytest.fixture
def categories() -> CategoryRepository:
    """Provide an autospec category repository with an active 100.00 category.

    Returns:
        A mock ``CategoryRepository``.
    """
    mock = create_autospec(CategoryRepository, instance=True)
    mock.get.return_value = make_category()
    return mock


@pytest.fixture
def service(
    expenses: ExpenseRepository, categories: CategoryRepository
) -> ExpenseService:
    """Build the service under test with mocked collaborators.

    Args:
        expenses: Mock expense repository.
        categories: Mock category repository.

    Returns:
        An ``ExpenseService`` using ``FakeClock``.
    """
    return ExpenseService(expenses, categories, FakeClock())


def make_category(budget: str = "100.00", is_active: bool = True) -> Category:
    """Build an in-memory category.

    Args:
        budget: Monthly budget.
        is_active: Whether the category accepts expenses.

    Returns:
        A ``Category``.
    """
    return Category(
        id=3, name="Food", monthly_budget=Decimal(budget), is_active=is_active
    )


def make_data(spent_at: date = date(2026, 11, 5)) -> ExpenseCreate:
    """Build a valid creation payload.

    Args:
        spent_at: Expense date.

    Returns:
        An ``ExpenseCreate``.
    """
    return ExpenseCreate(
        category_id=3,
        amount=Decimal("25.50"),
        description="Lunch",
        spent_at=spent_at,
    )


def test_create_adds_an_expense_built_from_the_input(
    service: ExpenseService, expenses: ExpenseRepository
) -> None:
    """Create persists an expense mirroring the payload."""
    result = service.create(make_data())

    expenses.add.assert_called_once()
    added = expenses.add.call_args.args[0]
    assert isinstance(added, Expense)
    assert added.category_id == 3
    assert added.amount == Decimal("25.50")
    assert added.description == "Lunch"
    assert added.spent_at == date(2026, 11, 5)
    assert isinstance(result, CreatedExpense)
    assert result.expense is added
    assert result.over_budget is False


def test_create_allows_an_expense_dated_today(service: ExpenseService) -> None:
    """Create accepts a ``spent_at`` equal to today."""
    result = service.create(make_data(TODAY))

    assert result.expense.spent_at == TODAY


def test_create_looks_up_the_category_by_id(
    service: ExpenseService, categories: CategoryRepository
) -> None:
    """Create asks the category repository for the payload category."""
    service.create(make_data())

    categories.get.assert_called_once_with(3)


def test_create_rejects_a_future_date_before_touching_repositories(
    service: ExpenseService,
    expenses: ExpenseRepository,
    categories: CategoryRepository,
) -> None:
    """Create raises a future-date error and uses no repository."""
    with pytest.raises(FutureDateError) as raised:
        service.create(make_data(date(2026, 11, 7)))

    assert raised.value.spent_at == date(2026, 11, 7)
    categories.get.assert_not_called()
    expenses.add.assert_not_called()


def test_create_rejects_a_missing_category(
    service: ExpenseService,
    expenses: ExpenseRepository,
    categories: CategoryRepository,
) -> None:
    """Create raises not-found when the category does not exist."""
    categories.get.return_value = None

    with pytest.raises(CategoryNotFoundError) as raised:
        service.create(make_data())

    assert raised.value.category_id == 3
    expenses.add.assert_not_called()


def test_create_rejects_an_inactive_category(
    service: ExpenseService,
    expenses: ExpenseRepository,
    categories: CategoryRepository,
) -> None:
    """Create raises an inactive error and never adds."""
    categories.get.return_value = make_category(is_active=False)

    with pytest.raises(InactiveCategoryError) as raised:
        service.create(make_data())

    assert raised.value.category_id == 3
    expenses.add.assert_not_called()


def test_create_checks_the_date_before_the_category_rules(
    service: ExpenseService, categories: CategoryRepository
) -> None:
    """A future date wins over a missing category."""
    categories.get.return_value = None

    with pytest.raises(FutureDateError):
        service.create(make_data(date(2026, 12, 1)))


def test_create_computes_the_month_total_after_adding(
    service: ExpenseService, expenses: ExpenseRepository
) -> None:
    """Create sums the category total over the month of ``spent_at``."""
    service.create(make_data(date(2026, 10, 31)))

    expenses.monthly_total.assert_called_once_with(
        3, date(2026, 10, 1), date(2026, 11, 1)
    )
    assert [call[0] for call in expenses.mock_calls] == ["add", "monthly_total"]


@pytest.mark.parametrize(
    ("budget", "total", "expected"),
    [
        ("100.00", "99.99", False),
        ("100.00", "100.00", False),
        ("100.00", "100.01", True),
        ("0.00", "0.01", True),
        ("0.00", "0", False),
    ],
    ids=["below", "exactly-reached", "exceeded", "zero-budget-any-spend", "zero-zero"],
)
def test_create_flags_over_budget_only_when_the_total_exceeds_it(
    service: ExpenseService,
    expenses: ExpenseRepository,
    categories: CategoryRepository,
    budget: str,
    total: str,
    expected: bool,
) -> None:
    """Over budget is true only for a total strictly above the budget."""
    categories.get.return_value = make_category(budget)
    expenses.monthly_total.return_value = Decimal(total)

    assert service.create(make_data()).over_budget is expected


def test_list_without_month_passes_no_period(
    service: ExpenseService, expenses: ExpenseRepository
) -> None:
    """List asks for every month when ``month`` is None."""
    found = [Expense(id=1)]
    expenses.list.return_value = found

    result = service.list(category_id=None, month=None, limit=100, offset=0)

    assert result is found
    expenses.list.assert_called_once_with(
        category_id=None, start=None, end=None, limit=100, offset=0
    )


def test_list_converts_the_month_into_a_half_open_period(
    service: ExpenseService, expenses: ExpenseRepository
) -> None:
    """List maps ``YYYY-MM`` to its first day and the next month's first day."""
    expenses.list.return_value = []

    service.list(category_id=3, month="2026-11", limit=10, offset=5)

    expenses.list.assert_called_once_with(
        category_id=3,
        start=date(2026, 11, 1),
        end=date(2026, 12, 1),
        limit=10,
        offset=5,
    )


def test_list_rejects_an_unsupported_month(
    service: ExpenseService, expenses: ExpenseRepository
) -> None:
    """List raises invalid-month for year 0000 and never queries."""
    with pytest.raises(InvalidMonthError) as raised:
        service.list(category_id=None, month="0000-05", limit=100, offset=0)

    assert raised.value.value == "0000-05"
    expenses.list.assert_not_called()


def test_delete_removes_the_found_expense(
    service: ExpenseService, expenses: ExpenseRepository
) -> None:
    """Delete passes the loaded expense to the repository."""
    expense = Expense(id=7)
    expenses.get.return_value = expense

    service.delete(7)

    expenses.get.assert_called_once_with(7)
    expenses.delete.assert_called_once_with(expense)


def test_delete_rejects_a_missing_expense(
    service: ExpenseService, expenses: ExpenseRepository
) -> None:
    """Delete raises not-found and never deletes when the id is unknown."""
    expenses.get.return_value = None

    with pytest.raises(ExpenseNotFoundError) as raised:
        service.delete(9)

    assert raised.value.expense_id == 9
    expenses.delete.assert_not_called()
