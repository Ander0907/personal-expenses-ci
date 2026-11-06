"""Unit tests for ``app.repositories.health_repository``.

The session is always a mock: no database is ever contacted.
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql.elements import TextClause

from app.repositories.health_repository import HealthRepository


def test_ping_executes_select_one_once() -> None:
    """Ping executes a single SELECT 1 text clause on the session."""
    session = MagicMock()

    HealthRepository(session).ping()

    session.execute.assert_called_once()
    statement = session.execute.call_args.args[0]
    assert isinstance(statement, TextClause)
    assert str(statement) == "SELECT 1"


def test_ping_returns_none() -> None:
    """Ping returns None when the query succeeds."""
    assert HealthRepository(MagicMock()).ping() is None


def test_ping_propagates_database_errors() -> None:
    """Ping lets SQLAlchemy errors raised by execute propagate."""
    session = MagicMock()
    session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("down"))

    with pytest.raises(OperationalError):
        HealthRepository(session).ping()
