"""FastAPI dependency providers wiring repositories and services."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock, SystemClock
from app.db.session import get_session
from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.health_repository import HealthRepository
from app.services.category_service import CategoryService
from app.services.expense_service import ExpenseService
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


def get_category_repository(
    session: Annotated[Session, Depends(get_session)],
) -> CategoryRepository:
    """Provide a category repository bound to the request session.

    Args:
        session: Database session for the current request.

    Returns:
        A ``CategoryRepository``.
    """
    return CategoryRepository(session)


def get_category_service(
    repository: Annotated[CategoryRepository, Depends(get_category_repository)],
) -> CategoryService:
    """Provide a category service backed by the given repository.

    Args:
        repository: Repository used by the service.

    Returns:
        A ``CategoryService``.
    """
    return CategoryService(repository)


def get_clock() -> Clock:
    """Provide the real clock.

    Returns:
        A ``SystemClock``.
    """
    return SystemClock()


def get_expense_repository(
    session: Annotated[Session, Depends(get_session)],
) -> ExpenseRepository:
    """Provide an expense repository bound to the request session.

    Args:
        session: Database session for the current request.

    Returns:
        An ``ExpenseRepository``.
    """
    return ExpenseRepository(session)


def get_expense_service(
    expenses: Annotated[ExpenseRepository, Depends(get_expense_repository)],
    categories: Annotated[CategoryRepository, Depends(get_category_repository)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> ExpenseService:
    """Provide an expense service with its collaborators.

    Args:
        expenses: Expense repository.
        categories: Category repository.
        clock: Clock used for the future-date rule.

    Returns:
        An ``ExpenseService``.
    """
    return ExpenseService(expenses, categories, clock)
