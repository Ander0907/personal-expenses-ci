"""FastAPI dependency providers wiring repositories and services."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.health_repository import HealthRepository
from app.services.health_service import HealthService


def get_health_repository(
    session: Annotated[Session, Depends(get_session)],
) -> HealthRepository:
    """Provide a health repository bound to the request session.

    Args:
        session: Database session for the current request.

    Returns:
        A ``HealthRepository``.
    """
    return HealthRepository(session)


def get_health_service(
    repository: Annotated[HealthRepository, Depends(get_health_repository)],
) -> HealthService:
    """Provide a health service backed by the given repository.

    Args:
        repository: Repository used by the service.

    Returns:
        A ``HealthService``.
    """
    return HealthService(repository)
