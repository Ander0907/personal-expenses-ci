"""Unit tests for ``app.routers.reports``.

Only ``app.dependency_overrides`` is used (never patch); the service is an
autospec mock, so no database is ever contacted.
"""

from collections.abc import Iterator
from decimal import Decimal
from unittest.mock import create_autospec

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dependencies import get_report_service
from app.main import create_app
from app.schemas.report import CategoryReport, MonthlyReport
from app.services.report_service import ReportService


@pytest.fixture
def application() -> Iterator[FastAPI]:
    """Provide a fresh app whose overrides are cleared afterwards.

    Yields:
        A new ``FastAPI`` instance.
    """
    app = create_app()
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def service(application: FastAPI) -> ReportService:
    """Override the report service with an autospec mock.

    Args:
        application: The app whose dependency is overridden.

    Returns:
        The mock service.
    """
    mock = create_autospec(ReportService, instance=True)
    application.dependency_overrides[get_report_service] = lambda: mock
    return mock


def make_report() -> MonthlyReport:
    """Build a report with a budgeted and a zero-budget category.

    Returns:
        A ``MonthlyReport``.
    """
    return MonthlyReport(
        year=2026,
        month=11,
        total_spent=Decimal("25.00"),
        categories=[
            CategoryReport(
                category_id=1,
                name="Food",
                monthly_budget=Decimal("150.00"),
                total_spent=Decimal("20.00"),
                percent_used=Decimal("13.33"),
                over_budget=False,
            ),
            CategoryReport(
                category_id=2,
                name="Misc",
                monthly_budget=Decimal("0.00"),
                total_spent=Decimal("5.00"),
                percent_used=None,
                over_budget=True,
            ),
        ],
    )


def test_get_monthly_report_returns_200_with_the_serialized_report(
    application: FastAPI, service: ReportService
) -> None:
    """GET /reports/monthly returns the report with string decimals."""
    service.monthly.return_value = make_report()

    response = TestClient(application).get(
        "/reports/monthly", params={"year": 2026, "month": 11}
    )

    assert response.status_code == 200
    assert response.json() == {
        "year": 2026,
        "month": 11,
        "total_spent": "25.00",
        "categories": [
            {
                "category_id": 1,
                "name": "Food",
                "monthly_budget": "150.00",
                "total_spent": "20.00",
                "percent_used": "13.33",
                "over_budget": False,
            },
            {
                "category_id": 2,
                "name": "Misc",
                "monthly_budget": "0.00",
                "total_spent": "5.00",
                "percent_used": None,
                "over_budget": True,
            },
        ],
    }


def test_get_monthly_report_passes_integer_year_and_month_to_the_service(
    application: FastAPI, service: ReportService
) -> None:
    """GET /reports/monthly calls the service once with parsed integers."""
    service.monthly.return_value = make_report()

    TestClient(application).get("/reports/monthly", params={"year": 2026, "month": 11})

    service.monthly.assert_called_once_with(year=2026, month=11)


@pytest.mark.parametrize(
    ("year", "month"),
    [(1, 1), (9998, 12)],
    ids=["lowest", "highest"],
)
def test_get_monthly_report_accepts_the_boundary_values(
    application: FastAPI, service: ReportService, year: int, month: int
) -> None:
    """GET /reports/monthly accepts the extreme valid year and month."""
    service.monthly.return_value = make_report()

    response = TestClient(application).get(
        "/reports/monthly", params={"year": year, "month": month}
    )

    assert response.status_code == 200
    service.monthly.assert_called_once_with(year=year, month=month)


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"month": 11},
        {"year": 2026},
        {"year": 2026, "month": 0},
        {"year": 2026, "month": 13},
        {"year": 0, "month": 11},
        {"year": 9999, "month": 11},
        {"year": "abc", "month": 11},
        {"year": 2026, "month": "nov"},
        {"year": "2026.5", "month": 11},
    ],
    ids=[
        "both-missing",
        "year-missing",
        "month-missing",
        "month-zero",
        "month-thirteen",
        "year-zero",
        "year-9999",
        "year-not-integer",
        "month-not-integer",
        "year-float",
    ],
)
def test_get_monthly_report_rejects_invalid_query_with_422(
    application: FastAPI, service: ReportService, params: dict[str, object]
) -> None:
    """GET /reports/monthly returns 422 and skips the service on bad input."""
    response = TestClient(application).get("/reports/monthly", params=params)

    assert response.status_code == 422
    service.monthly.assert_not_called()
