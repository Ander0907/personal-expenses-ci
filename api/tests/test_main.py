"""Unit tests for ``app.main``.

No ``POSTGRES_*`` variables are set anywhere in this module: building the
application must not require database configuration.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app, create_app

EXPECTED_TITLE = "Personal Expenses API"
EXPECTED_VERSION = "0.1.0"


def test_create_app_returns_a_fastapi_instance() -> None:
    """Create app returns a fastapi instance."""
    assert isinstance(create_app(), FastAPI)


def test_create_app_sets_title_and_version() -> None:
    """Create app sets title and version."""
    application = create_app()

    assert application.title == EXPECTED_TITLE
    assert application.version == EXPECTED_VERSION


def test_create_app_returns_a_new_instance_on_each_call() -> None:
    """Create app returns a new instance on each call."""
    assert create_app() is not create_app()


def test_module_level_app_is_a_fastapi_instance() -> None:
    """Module level app is a fastapi instance."""
    assert isinstance(app, FastAPI)


def test_create_app_registers_the_health_route() -> None:
    """Create app registers the /health route."""
    application = create_app()

    assert "/health" in application.openapi()["paths"]
    assert application.url_path_for("health") == "/health"


def test_create_app_registers_the_categories_route() -> None:
    """Create app registers the /categories route."""
    application = create_app()

    assert "/categories" in application.openapi()["paths"]


def test_create_app_registers_the_expenses_route() -> None:
    """Create app registers the /expenses route."""
    application = create_app()

    assert "/expenses" in application.openapi()["paths"]


def test_create_app_registers_the_monthly_report_route() -> None:
    """Create app registers the /reports/monthly route."""
    application = create_app()

    assert "/reports/monthly" in application.openapi()["paths"]


def test_openapi_schema_is_served_with_the_app_title() -> None:
    """Openapi schema is served with the app title."""
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    info = response.json()["info"]
    assert info["title"] == EXPECTED_TITLE
    assert info["version"] == EXPECTED_VERSION
