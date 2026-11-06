"""Repository used to probe database connectivity."""

from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthRepository:
    """Runs the connectivity probe against the database."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Session used to execute the probe.
        """
        self._session = session

    def ping(self) -> None:
        """Execute ``SELECT 1``.

        Raises:
            sqlalchemy.exc.SQLAlchemyError: If the database is unreachable.
        """
        self._session.execute(text("SELECT 1"))
