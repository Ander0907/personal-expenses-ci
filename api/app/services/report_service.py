"""Business rules for the monthly report."""

from decimal import ROUND_HALF_UP, Decimal

from app.core.dates import month_bounds
from app.repositories.expense_repository import CategoryTotal, ExpenseRepository
from app.schemas.report import CategoryReport, MonthlyReport

_CENT = Decimal("0.01")
_HUNDRED = Decimal(100)


def _build_category_report(row: CategoryTotal) -> CategoryReport:
    """Turn a repository row into a category report.

    Args:
        row: Category budget and month total.

    Returns:
        The report with percent used (None for a zero budget) and the flag.
    """
    total = row.total.quantize(_CENT)
    percent = None
    if row.monthly_budget != 0:
        percent = (total / row.monthly_budget * _HUNDRED).quantize(_CENT, ROUND_HALF_UP)
    return CategoryReport(
        category_id=row.category_id,
        name=row.name,
        monthly_budget=row.monthly_budget,
        total_spent=total,
        percent_used=percent,
        over_budget=total > row.monthly_budget,
    )


class ReportService:
    """Builds spending reports."""

    def __init__(self, expenses: ExpenseRepository) -> None:
        """Initialize the service.

        Args:
            expenses: Expense repository providing aggregated totals.
        """
        self._expenses = expenses

    def monthly(self, year: int, month: int) -> MonthlyReport:
        """Build the report for a calendar month.

        Args:
            year: Calendar year.
            month: Month number (1-12).

        Returns:
            Per-category totals, budgets, percentages and the month total.
        """
        start, end = month_bounds(year, month)
        categories = [
            _build_category_report(row)
            for row in self._expenses.totals_by_category(start, end)
        ]
        total = sum((c.total_spent for c in categories), Decimal(0)).quantize(_CENT)
        return MonthlyReport(
            year=year, month=month, total_spent=total, categories=categories
        )
