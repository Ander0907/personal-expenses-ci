"""Unit tests for ``app.schemas.health``."""

import pytest
from pydantic import ValidationError

from app.schemas.health import HealthResponse


@pytest.mark.parametrize(
    ("status", "database"),
    [("ok", "ok"), ("error", "unavailable"), ("ok", "unavailable"), ("error", "ok")],
)
def test_health_response_accepts_allowed_values(status: str, database: str) -> None:
    """Health response accepts every allowed status/database value."""
    response = HealthResponse(status=status, database=database)

    assert response.status == status
    assert response.database == database


def test_health_response_serializes_to_expected_dict() -> None:
    """Health response dumps to a plain two-key dict."""
    response = HealthResponse(status="ok", database="ok")

    assert response.model_dump() == {"status": "ok", "database": "ok"}


@pytest.mark.parametrize("status", ["up", "OK", ""])
def test_health_response_rejects_invalid_status(status: str) -> None:
    """Health response rejects a status outside ok/error."""
    with pytest.raises(ValidationError):
        HealthResponse(status=status, database="ok")


@pytest.mark.parametrize("database", ["down", "error", ""])
def test_health_response_rejects_invalid_database(database: str) -> None:
    """Health response rejects a database value outside ok/unavailable."""
    with pytest.raises(ValidationError):
        HealthResponse(status="ok", database=database)
