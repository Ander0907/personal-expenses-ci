"""Unit tests for ``app.routers.categories``.

Only ``app.dependency_overrides`` is used (never patch); the service is an
autospec mock, so no database is ever contacted.
"""

from collections.abc import Iterator
from decimal import Decimal
from typing import Any
from unittest.mock import create_autospec

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import DuplicateCategoryError
from app.dependencies import get_category_service
from app.main import create_app
from app.models.category import Category
from app.schemas.category import CategoryCreate
from app.services.category_service import CategoryService

VALID_BODY: dict[str, Any] = {
    "name": "Food",
    "monthly_budget": "150.00",
    "is_active": True,
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
def service(application: FastAPI) -> CategoryService:
    """Override the category service with an autospec mock.

    Args:
        application: The app whose dependency is overridden.

    Returns:
        The mock service.
    """
    mock = create_autospec(CategoryService, instance=True)
    application.dependency_overrides[get_category_service] = lambda: mock
    return mock


def make_category(category_id: int = 1, name: str = "Food") -> Category:
    """Build an in-memory category as the service would return it.

    Args:
        category_id: Primary key value.
        name: Category name.

    Returns:
        A ``Category``.
    """
    return Category(
        id=category_id,
        name=name,
        monthly_budget=Decimal("150.00"),
        is_active=True,
    )


def test_post_categories_returns_201_with_the_created_category(
    application: FastAPI, service: CategoryService
) -> None:
    """POST /categories returns 201 and the serialized category."""
    service.create.return_value = make_category()  # type: ignore[attr-defined]

    response = TestClient(application).post("/categories", json=VALID_BODY)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Food",
        "monthly_budget": "150.00",
        "is_active": True,
    }


def test_post_categories_passes_a_validated_payload_to_the_service(
    application: FastAPI, service: CategoryService
) -> None:
    """POST /categories calls the service once with a ``CategoryCreate``."""
    service.create.return_value = make_category()  # type: ignore[attr-defined]

    TestClient(application).post("/categories", json=VALID_BODY)

    service.create.assert_called_once()  # type: ignore[attr-defined]
    data = service.create.call_args.args[0]  # type: ignore[attr-defined]
    assert isinstance(data, CategoryCreate)
    assert data.name == "Food"
    assert data.monthly_budget == Decimal("150.00")


def test_post_categories_returns_409_when_the_name_already_exists(
    application: FastAPI, service: CategoryService
) -> None:
    """POST /categories maps a duplicate error to 409."""
    service.create.side_effect = DuplicateCategoryError("Food")  # type: ignore[attr-defined]

    response = TestClient(application).post("/categories", json=VALID_BODY)

    assert response.status_code == 409
    assert response.json() == {"detail": "Category 'Food' already exists"}


@pytest.mark.parametrize(
    "body",
    [
        {"monthly_budget": "1"},
        {"name": "", "monthly_budget": "1"},
        {"name": "   ", "monthly_budget": "1"},
        {"name": "a" * 101, "monthly_budget": "1"},
        {"name": "Food", "monthly_budget": "-1"},
        {"name": "Food", "monthly_budget": "10.123"},
        {"id": 5, "name": "Food", "monthly_budget": "1"},
        {"name": "a\u0000b", "monthly_budget": "1"},
    ],
    ids=[
        "missing-name",
        "empty-name",
        "blank-name",
        "name-too-long",
        "negative-budget",
        "three-decimals",
        "extra-field",
        "control-character-in-name",
    ],
)
def test_post_categories_returns_422_for_invalid_bodies(
    application: FastAPI, service: CategoryService, body: dict[str, Any]
) -> None:
    """POST /categories rejects invalid payloads without calling the service."""
    response = TestClient(application).post("/categories", json=body)

    assert response.status_code == 422
    service.create.assert_not_called()  # type: ignore[attr-defined]


def test_get_categories_returns_the_list_with_default_pagination(
    application: FastAPI, service: CategoryService
) -> None:
    """GET /categories returns 200 and asks for limit 100, offset 0."""
    service.list.return_value = [  # type: ignore[attr-defined]
        make_category(1, "Food"),
        make_category(2, "Rent"),
    ]

    response = TestClient(application).get("/categories")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Food", "Rent"]
    assert response.json()[0]["monthly_budget"] == "150.00"
    service.list.assert_called_once_with(limit=100, offset=0)  # type: ignore[attr-defined]


def test_get_categories_forwards_limit_and_offset(
    application: FastAPI, service: CategoryService
) -> None:
    """GET /categories passes the query parameters to the service."""
    service.list.return_value = []  # type: ignore[attr-defined]

    response = TestClient(application).get("/categories?limit=10&offset=20")

    assert response.status_code == 200
    assert response.json() == []
    service.list.assert_called_once_with(limit=10, offset=20)  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "query",
    ["limit=0", "limit=501", "offset=-1", "offset=1000001"],
)
def test_get_categories_returns_422_for_out_of_range_pagination(
    application: FastAPI, service: CategoryService, query: str
) -> None:
    """GET /categories rejects invalid pagination without calling the service."""
    response = TestClient(application).get(f"/categories?{query}")

    assert response.status_code == 422
    service.list.assert_not_called()  # type: ignore[attr-defined]


def test_get_categories_accepts_the_maximum_offset(
    application: FastAPI, service: CategoryService
) -> None:
    """GET /categories accepts an offset of exactly 1000000."""
    service.list.return_value = []  # type: ignore[attr-defined]

    response = TestClient(application).get("/categories?offset=1000000")

    assert response.status_code == 200
    service.list.assert_called_once_with(limit=100, offset=1000000)  # type: ignore[attr-defined]


def test_categories_routes_are_documented_in_openapi(application: FastAPI) -> None:
    """The OpenAPI schema lists GET and POST /categories."""
    paths = TestClient(application).get("/openapi.json").json()["paths"]

    assert "/categories" in paths
    assert {"get", "post"} <= set(paths["/categories"])
