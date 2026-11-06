"""Unit tests for ``app.dependencies``.

The providers are called directly with mocks: no container, no database.
"""

from unittest.mock import MagicMock, create_autospec

from app.dependencies import get_health_repository, get_health_service
from app.repositories.health_repository import HealthRepository
from app.services.health_service import HealthService


def test_get_health_repository_binds_the_given_session() -> None:
    """Get health repository returns a repository bound to the session."""
    session = MagicMock()

    repository = get_health_repository(session)

    assert isinstance(repository, HealthRepository)
    repository.ping()
    session.execute.assert_called_once()


def test_get_health_service_uses_the_given_repository() -> None:
    """Get health service returns a service backed by the repository."""
    repository = create_autospec(HealthRepository, instance=True)

    service = get_health_service(repository)

    assert isinstance(service, HealthService)
    assert service.is_database_available() is True
    repository.ping.assert_called_once_with()
