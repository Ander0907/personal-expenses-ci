"""Unit tests for ``app.services.health_service``.

The repository is an autospecced mock: no database is ever contacted.
"""

from unittest.mock import create_autospec

import pytest
from sqlalchemy.exc import InterfaceError, OperationalError, SQLAlchemyError

from app.repositories.health_repository import HealthRepository
from app.services.health_service import HealthService


def make_repository() -> HealthRepository:
    """Build an autospecced repository mock.

    Returns:
        A mock honouring the ``HealthRepository`` interface.
    """
    return create_autospec(HealthRepository, instance=True)


def test_is_database_available_returns_true_when_ping_succeeds() -> None:
    """Is database available returns True when ping succeeds."""
    repository = make_repository()

    assert HealthService(repository).is_database_available() is True
    repository.ping.assert_called_once_with()


@pytest.mark.parametrize(
    "error",
    [
        OperationalError("SELECT 1", {}, Exception("down")),
        InterfaceError("SELECT 1", {}, Exception("closed")),
    ],
    ids=["operational", "interface"],
)
def test_is_database_available_returns_false_on_sqlalchemy_errors(
    error: SQLAlchemyError,
) -> None:
    """Is database available returns False when ping raises a SQLAlchemyError."""
    repository = make_repository()
    repository.ping.side_effect = error

    assert HealthService(repository).is_database_available() is False


def test_is_database_available_propagates_unexpected_errors() -> None:
    """Is database available does not swallow non-SQLAlchemy exceptions."""
    repository = make_repository()
    repository.ping.side_effect = RuntimeError("bug")

    with pytest.raises(RuntimeError, match="bug"):
        HealthService(repository).is_database_available()
