"""Unit tests for ``app.routers.expenses``.

Only ``app.dependency_overrides`` is used (never patch); the service is an
autospec mock, so no database is ever contacted.
"""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import create_autospec

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import (
    CategoryNotFoundError,
    ExpenseNotFoundError,
    FutureDateError,
    InactiveCategoryError,
    InvalidMonthError,
)
from app.core.limits import DEFAULT_LIMIT, MAX_DB_INT, MAX_LIMIT, MAX_OFFSET
from app.dependencies import get_expense_service
from app.main import create_app
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate
from app.services.expense_service import CreatedExpense, ExpenseService

VALID_BODY: dict[str, Any] = {
    "category_id": 1,
    "amount": "25.50",
    "description": "Lunch",
    "spent_at": "2026-11-05",
}


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
def service(application: FastAPI) -> ExpenseService:
    """Override the expense service with an autospec mock.

    Args:
        application: The app whose dependency is overridden.

    Returns:
        The mock service.
    """
    mock = create_autospec(ExpenseService, instance=True)
    application.dependency_overrides[get_expense_service] = lambda: mock
    return mock


def make_expense(expense_id: int = 7) -> Expense:
    """Build an in-memory expense as the service would return it.

    Args:
        expense_id: Primary key value.

    Returns:
        An ``Expense`` with every field set.
    """
    return Expense(
        id=expense_id,
        category_id=1,
        amount=Decimal("25.50"),
        description="Lunch",
        spent_at=date(2026, 11, 5),
        created_at=datetime(2026, 11, 5, 12, 0, tzinfo=UTC),
    )


def test_post_expenses_returns_201_with_the_created_expense(
    application: FastAPI, service: ExpenseService
) -> None:
    """POST /expenses returns 201, the expense and the over-budget flag."""
    service.create.return_value = CreatedExpense(
        expense=make_expense(), over_budget=True
    )

    response = TestClient(application).post("/expenses", json=VALID_BODY)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 7
    assert body["category_id"] == 1
    assert body["amount"] == "25.50"
    assert body["description"] == "Lunch"
    assert body["spent_at"] == "2026-11-05"
    assert datetime.fromisoformat(body["created_at"]) == datetime(
        2026, 11, 5, 12, 0, tzinfo=UTC
    )
    assert body["over_budget"] is True


def test_post_expenses_passes_a_validated_payload_to_the_service(
    application: FastAPI, service: ExpenseService
) -> None:
    """POST /expenses calls the service once with an ``ExpenseCreate``."""
    service.create.return_value = CreatedExpense(
        expense=make_expense(), over_budget=False
    )

    TestClient(application).post("/expenses", json=VALID_BODY)

    service.create.assert_called_once()
    data = service.create.call_args.args[0]
    assert isinstance(data, ExpenseCreate)
    assert data.category_id == 1
    assert data.amount == Decimal("25.50")
    assert data.spent_at == date(2026, 11, 5)


@pytest.mark.parametrize(
    ("error", "status", "detail"),
    [
        (
            FutureDateError(date(2026, 12, 1)),
            422,
            "Expense date 2026-12-01 is in the future",
        ),
        (CategoryNotFoundError(1), 404, "Category 1 not found"),
        (InactiveCategoryError(1), 422, "Category 1 is inactive"),
    ],
    ids=["future-date", "category-not-found", "inactive-category"],
)
def test_post_expenses_maps_domain_errors_to_their_status(
    application: FastAPI,
    service: ExpenseService,
    error: Exception,
    status: int,
    detail: str,
) -> None:
    """POST /expenses turns service domain errors into HTTP errors."""
    service.create.side_effect = error

    response = TestClient(application).post("/expenses", json=VALID_BODY)

    assert response.status_code == status
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount": "0"},
        {"amount": "-1"},
        {"amount": "10.123"},
        {"category_id": 0},
        {"spent_at": None},
        {"spent_at": "not-a-date"},
        {"id": 5},
        {"description": "a" * 256},
    ],
    ids=[
        "amount-zero",
        "amount-negative",
        "three-decimals",
        "category-zero",
        "missing-spent-at",
        "bad-date",
        "extra-field",
        "description-too-long",
    ],
)
def test_post_expenses_returns_422_for_invalid_bodies(
    application: FastAPI, service: ExpenseService, overrides: dict[str, Any]
) -> None:
    """POST /expenses rejects invalid payloads without calling the service."""
    body = {**VALID_BODY, **overrides}
    body = {key: value for key, value in body.items() if value is not None}

    response = TestClient(application).post("/expenses", json=body)

    assert response.status_code == 422
    service.create.assert_not_called()


def test_get_expenses_returns_the_list_with_default_filters(
    application: FastAPI, service: ExpenseService
) -> None:
    """GET /expenses returns 200 and asks for the default page."""
    service.list.return_value = [make_expense(1), make_expense(2)]

    response = TestClient(application).get("/expenses")

    assert response.status_code == 200
    items = response.json()
    assert [item["id"] for item in items] == [1, 2]
    assert items[0]["amount"] == "25.50"
    assert "over_budget" not in items[0]
    service.list.assert_called_once_with(
        category_id=None, month=None, limit=100, offset=0
    )


def test_get_expenses_forwards_filters_and_pagination(
    application: FastAPI, service: ExpenseService
) -> None:
    """GET /expenses passes every query parameter to the service."""
    service.list.return_value = []

    response = TestClient(application).get(
        "/expenses?category_id=3&month=2026-11&limit=10&offset=5"
    )

    assert response.status_code == 200
    assert response.json() == []
    service.list.assert_called_once_with(
        category_id=3, month="2026-11", limit=10, offset=5
    )


@pytest.mark.parametrize(
    "query",
    [
        "month=2026-13",
        "month=2026/11",
        "month=2026-1",
        "category_id=0",
        "limit=0",
        "limit=501",
        "offset=-1",
        "offset=1000001",
    ],
)
def test_get_expenses_returns_422_for_invalid_query(
    application: FastAPI, service: ExpenseService, query: str
) -> None:
    """GET /expenses rejects invalid filters without calling the service."""
    response = TestClient(application).get(f"/expenses?{query}")

    assert response.status_code == 422
    service.list.assert_not_called()


def test_delete_expense_returns_204_with_an_empty_body(
    application: FastAPI, service: ExpenseService
) -> None:
    """DELETE /expenses/{id} returns 204 and delegates to the service."""
    response = TestClient(application).delete("/expenses/7")

    assert response.status_code == 204
    assert response.content == b""
    service.delete.assert_called_once_with(7)


def test_delete_expense_returns_404_when_it_does_not_exist(
    application: FastAPI, service: ExpenseService
) -> None:
    """DELETE /expenses/{id} maps a not-found error to 404."""
    service.delete.side_effect = ExpenseNotFoundError(9)

    response = TestClient(application).delete("/expenses/9")

    assert response.status_code == 404
    assert response.json() == {"detail": "Expense 9 not found"}


def test_delete_expense_returns_422_for_a_non_positive_id(
    application: FastAPI, service: ExpenseService
) -> None:
    """DELETE /expenses/0 is rejected without calling the service."""
    response = TestClient(application).delete("/expenses/0")

    assert response.status_code == 422
    service.delete.assert_not_called()


def test_post_expenses_rejects_a_category_id_above_int4(
    application: FastAPI, service: ExpenseService
) -> None:
    """POST /expenses returns 422 for a category id overflowing ``integer``."""
    body = {**VALID_BODY, "category_id": MAX_DB_INT + 1}

    response = TestClient(application).post("/expenses", json=body)

    assert response.status_code == 422
    service.create.assert_not_called()


def test_get_expenses_rejects_non_ascii_digits_in_month(
    application: FastAPI, service: ExpenseService
) -> None:
    """GET /expenses rejects Arabic-Indic digits without calling the service."""
    response = TestClient(application).get("/expenses?month=٢٠٢٦-11")

    assert response.status_code == 422
    service.list.assert_not_called()


def test_get_expenses_maps_an_invalid_month_error_to_422(
    application: FastAPI, service: ExpenseService
) -> None:
    """GET /expenses turns the service's invalid-month error into a 422."""
    service.list.side_effect = InvalidMonthError("0000-05")

    response = TestClient(application).get("/expenses?month=0000-05")

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid month '0000-05': expected YYYY-MM with year 0001-9998"
    }


def test_get_expenses_rejects_a_category_id_above_int4(
    application: FastAPI, service: ExpenseService
) -> None:
    """GET /expenses returns 422 for a category filter above int4."""
    response = TestClient(application).get(f"/expenses?category_id={MAX_DB_INT + 1}")

    assert response.status_code == 422
    service.list.assert_not_called()


def test_get_expenses_accepts_the_maximum_category_id(
    application: FastAPI, service: ExpenseService
) -> None:
    """GET /expenses passes the int4 maximum category filter through."""
    service.list.return_value = []

    response = TestClient(application).get(f"/expenses?category_id={MAX_DB_INT}")

    assert response.status_code == 200
    service.list.assert_called_once_with(
        category_id=MAX_DB_INT, month=None, limit=100, offset=0
    )


def test_delete_expense_rejects_an_id_above_int4(
    application: FastAPI, service: ExpenseService
) -> None:
    """DELETE /expenses/{id} returns 422 for an id overflowing ``integer``."""
    response = TestClient(application).delete(f"/expenses/{MAX_DB_INT + 1}")

    assert response.status_code == 422
    service.delete.assert_not_called()


def test_delete_expense_accepts_the_maximum_id(
    application: FastAPI, service: ExpenseService
) -> None:
    """DELETE /expenses/{id} accepts the int4 maximum."""
    response = TestClient(application).delete(f"/expenses/{MAX_DB_INT}")

    assert response.status_code == 204
    service.delete.assert_called_once_with(MAX_DB_INT)


def test_get_expenses_pagination_uses_the_shared_limits(
    application: FastAPI,
) -> None:
    """The OpenAPI limit and offset parameters mirror ``app.core.limits``."""
    parameters = application.openapi()["paths"]["/expenses"]["get"]["parameters"]
    schemas = {item["name"]: item["schema"] for item in parameters}

    assert schemas["limit"]["maximum"] == MAX_LIMIT
    assert schemas["limit"]["default"] == DEFAULT_LIMIT
    assert schemas["offset"]["maximum"] == MAX_OFFSET


def test_expenses_routes_are_documented_in_openapi(application: FastAPI) -> None:
    """The OpenAPI schema lists POST/GET /expenses and DELETE by id."""
    paths = TestClient(application).get("/openapi.json").json()["paths"]

    assert {"get", "post"} <= set(paths["/expenses"])
    assert "delete" in paths["/expenses/{expense_id}"]
