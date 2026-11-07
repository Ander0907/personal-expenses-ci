"""Unit tests for ``app.schemas.report``."""

import json
from decimal import Decimal

from app.schemas.report import CategoryReport, MonthlyReport


def make_category_report(**overrides: object) -> CategoryReport:
    """Build a category report with optional overrides.

    Args:
        **overrides: Fields replacing the defaults.

    Returns:
        A ``CategoryReport``.
    """
    values: dict[str, object] = {
        "category_id": 1,
        "name": "Food",
        "monthly_budget": Decimal("150.00"),
        "total_spent": Decimal("20.00"),
        "percent_used": Decimal("13.33"),
        "over_budget": False,
    }
    values.update(overrides)
    return CategoryReport.model_validate(values)


def test_category_report_keeps_every_field() -> None:
    """Category report exposes the values it was built with."""
    report = make_category_report()

    assert report.category_id == 1
    assert report.name == "Food"
    assert report.monthly_budget == Decimal("150.00")
    assert report.total_spent == Decimal("20.00")
    assert report.percent_used == Decimal("13.33")
    assert report.over_budget is False


def test_category_report_serializes_decimals_as_strings() -> None:
    """Category report dumps Decimal fields as JSON strings."""
    data = json.loads(make_category_report().model_dump_json())

    assert data["monthly_budget"] == "150.00"
    assert data["total_spent"] == "20.00"
    assert data["percent_used"] == "13.33"
    assert data["over_budget"] is False


def test_category_report_serializes_missing_percent_as_null() -> None:
    """Category report dumps a ``None`` percent as JSON null."""
    report = make_category_report(
        monthly_budget=Decimal("0.00"), percent_used=None, over_budget=True
    )

    data = json.loads(report.model_dump_json())

    assert report.percent_used is None
    assert data["percent_used"] is None


def test_monthly_report_holds_period_total_and_categories() -> None:
    """Monthly report groups the period, the total and the categories."""
    category = make_category_report()

    report = MonthlyReport(
        year=2026, month=11, total_spent=Decimal("20.00"), categories=[category]
    )

    assert report.year == 2026
    assert report.month == 11
    assert report.total_spent == Decimal("20.00")
    assert report.categories == [category]


def test_monthly_report_serializes_nested_categories() -> None:
    """Monthly report JSON nests categories with string decimals."""
    report = MonthlyReport(
        year=2026,
        month=11,
        total_spent=Decimal("20.00"),
        categories=[make_category_report()],
    )

    data = json.loads(report.model_dump_json())

    assert data["year"] == 2026
    assert data["month"] == 11
    assert data["total_spent"] == "20.00"
    assert data["categories"][0]["name"] == "Food"
    assert data["categories"][0]["percent_used"] == "13.33"


def test_monthly_report_accepts_no_categories() -> None:
    """Monthly report allows an empty category list."""
    report = MonthlyReport(
        year=2026, month=11, total_spent=Decimal("0.00"), categories=[]
    )

    assert report.categories == []
