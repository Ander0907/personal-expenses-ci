"""Unit tests for ``app.routers.health``.

Only ``app.dependency_overrides`` is used (never patch); no database is
ever contacted.
"""

from collections.abc import Iterator
from unittest.mock import MagicMock, create_autospec

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_session
from app.dependencies import get_health_service
from app.main import create_app
from app.services.health_service import HealthService


@pytest.fixture
def application() -> Iterator[FastAPI]:
    """Provide a fresh app whose overrides are cleared afterwards.

    Yields:
        A new ``FastAPI`` instance.
    """
    app = create_app()
    yield app
    app.dependency_overrides.clear()


def override_service(application: FastAPI, *, available: bool) -> None:
    """Replace the health service with a mock reporting ``available``.

    Args:
        application: The app whose dependencies are overridden.
        available: Value returned by ``is_database_available``.
    """
    service = create_autospec(HealthService, instance=True)
    service.is_database_available.return_value = available
    application.dependency_overrides[get_health_service] = lambda: service


def test_health_returns_200_when_database_is_available(application: FastAPI) -> None:
    """GET /health returns 200 and ok/ok when the service reports available."""
    override_service(application, available=True)

    response = TestClient(application).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_503_when_database_is_unavailable(
    application: FastAPI,
) -> None:
    """GET /health returns 503 and error/unavailable when the service says so."""
    override_service(application, available=False)

    response = TestClient(application).get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}


def test_health_returns_200_through_real_layers_when_session_executes(
    application: FastAPI,
) -> None:
    """GET /health returns 200 with a mock session whose execute succeeds."""
    session = MagicMock()
    application.dependency_overrides[get_session] = lambda: session

    response = TestClient(application).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    session.execute.assert_called_once()


def test_health_returns_503_through_real_layers_when_session_fails(
    application: FastAPI,
) -> None:
    """GET /health returns 503 with a mock session whose execute raises."""
    session = MagicMock()
    session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("down"))
    application.dependency_overrides[get_session] = lambda: session

    response = TestClient(application).get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}


def test_health_route_is_documented_in_openapi(application: FastAPI) -> None:
    """The OpenAPI schema lists GET /health."""
    response = TestClient(application).get("/openapi.json")

    paths = response.json()["paths"]
    assert "/health" in paths
    assert "get" in paths["/health"]
