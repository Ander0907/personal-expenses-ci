"""Service reporting database availability."""

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.repositories.health_repository import HealthRepository

logger = logging.getLogger(__name__)


class HealthService:
    """Determines whether the database can be reached."""

    def __init__(self, repository: HealthRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to probe the database.
        """
        self._repository = repository

    def is_database_available(self) -> bool:
        """Check database connectivity.

        Only the exception class name is logged so that connection details
        and credentials never leak into the logs.

        Returns:
            True if the probe succeeds, False on a SQLAlchemy error.
        """
        try:
            self._repository.ping()
        except SQLAlchemyError as error:
            logger.warning("Database health check failed: %s", type(error).__name__)
            return False
        return True
