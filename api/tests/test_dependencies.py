"""Unit tests for ``app.dependencies``.

The providers are called directly with mocks: no container, no database.
"""

from unittest.mock import MagicMock, create_autospec

from app.dependencies import (
    get_category_repository,
    get_category_service,
    get_health_repository,
    get_health_service,
)
from app.repositories.category_repository import CategoryRepository
from app.repositories.health_repository import HealthRepository
from app.services.category_service import CategoryService
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


def test_get_category_repository_binds_the_given_session() -> None:
    """Get category repository returns a repository bound to the session."""
    session = MagicMock()

    repository = get_category_repository(session)

    assert isinstance(repository, CategoryRepository)
    repository.get_by_name_case_insensitive("Food")
    session.scalar.assert_called_once()


def test_get_category_service_uses_the_given_repository() -> None:
    """Get category service returns a service backed by the repository."""
    repository = create_autospec(CategoryRepository, instance=True)
    repository.list.return_value = []

    service = get_category_service(repository)

    assert isinstance(service, CategoryService)
    assert service.list(limit=1, offset=0) == []
    repository.list.assert_called_once_with(limit=1, offset=0)
