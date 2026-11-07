"""Unit tests for ``app.services.report_service``.

The expense repository is an autospec mock: no session, no database.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import create_autospec

import pytest

from app.repositories.expense_repository import CategoryTotal, ExpenseRepository
from app.services.report_service import ReportService


def make_total(
    budget: str, total: str, category_id: int = 1, name: str = "Food"
) -> CategoryTotal:
    """Build a repository row.

    Args:
        budget: Monthly budget as text.
        total: Month total as text.
        category_id: Category primary key.
        name: Category name.

    Returns:
        A ``CategoryTotal``.
    """
    return CategoryTotal(
        category_id=category_id,
        name=name,
        monthly_budget=Decimal(budget),
        total=Decimal(total),
    )


def build_service(
    rows: list[CategoryTotal],
) -> tuple[ReportService, ExpenseRepository]:
    """Create a service over a mocked repository returning ``rows``.

    Args:
        rows: Rows returned by ``totals_by_category``.

    Returns:
        The service and its mock repository.
    """
    expenses = create_autospec(ExpenseRepository, instance=True)
    expenses.totals_by_category.return_value = rows
    return ReportService(expenses), expenses


def test_monthly_queries_the_repository_once_with_the_month_bounds() -> None:
    """Monthly asks for one month's totals using a half-open range."""
    service, expenses = build_service([])

    service.monthly(2026, 11)

    expenses.totals_by_category.assert_called_once_with(
        date(2026, 11, 1), date(2026, 12, 1)
    )


def test_monthly_rolls_december_over_to_january_of_the_next_year() -> None:
    """Monthly uses January 1st of the next year as December's end bound."""
    service, expenses = build_service([])

    service.monthly(2026, 12)

    expenses.totals_by_category.assert_called_once_with(
        date(2026, 12, 1), date(2027, 1, 1)
    )


def test_monthly_echoes_the_requested_year_and_month() -> None:
    """Monthly returns the requested period."""
    service, _ = build_service([])

    report = service.monthly(2026, 11)

    assert (report.year, report.month) == (2026, 11)


def test_monthly_without_categories_returns_zero_total_and_empty_list() -> None:
    """Monthly with no categories yields a zero total and no entries."""
    service, _ = build_service([])

    report = service.monthly(2026, 11)

    assert str(report.total_spent) == "0.00"
    assert report.categories == []


@pytest.mark.parametrize(
    ("budget", "total", "percent", "over_budget"),
    [
        ("150.00", "20.00", "13.33", False),
        ("150.00", "200.00", "133.33", True),
        ("3.00", "1.00", "33.33", False),
        ("8.00", "1.00", "12.50", False),
        ("200.00", "0.01", "0.01", False),
        ("150.00", "150.00", "100.00", False),
        ("150.00", "150.01", "100.01", True),
        ("150.00", "0.00", "0.00", False),
    ],
    ids=[
        "partial",
        "exceeded",
        "repeating-decimal",
        "exact-half",
        "half-up-rounding",
        "exactly-reached",
        "just-exceeded",
        "nothing-spent",
    ],
)
def test_monthly_computes_percent_used_and_over_budget(
    budget: str, total: str, percent: str, over_budget: bool
) -> None:
    """Monthly rounds percent half-up and flags only spending above budget."""
    service, _ = build_service([make_total(budget, total)])

    category = service.monthly(2026, 11).categories[0]

    assert str(category.percent_used) == percent
    assert category.over_budget is over_budget
    assert category.monthly_budget == Decimal(budget)


@pytest.mark.parametrize(
    ("total", "over_budget"),
    [("0.00", False), ("5.00", True)],
    ids=["zero-budget-nothing-spent", "zero-budget-with-spending"],
)
def test_monthly_with_zero_budget_has_no_percent(total: str, over_budget: bool) -> None:
    """Monthly returns a null percent for a zero budget without dividing."""
    service, _ = build_service([make_total("0.00", total)])

    category = service.monthly(2026, 11).categories[0]

    assert category.percent_used is None
    assert category.over_budget is over_budget


def test_monthly_quantizes_category_totals_to_two_decimals() -> None:
    """Monthly reports each category total with two decimal places."""
    service, _ = build_service([make_total("150.00", "20")])

    category = service.monthly(2026, 11).categories[0]

    assert str(category.total_spent) == "20.00"


def test_monthly_sums_category_totals_and_preserves_repository_order() -> None:
    """Monthly totals all categories and keeps the repository ordering."""
    rows = [
        make_total("150.00", "20.00", category_id=2, name="Bills"),
        make_total("0.00", "0.00", category_id=1, name="Food"),
        make_total("50.00", "30.50", category_id=3, name="Travel"),
    ]
    service, _ = build_service(rows)

    report = service.monthly(2026, 11)

    assert [c.category_id for c in report.categories] == [2, 1, 3]
    assert [c.name for c in report.categories] == ["Bills", "Food", "Travel"]
    assert str(report.total_spent) == "50.50"
