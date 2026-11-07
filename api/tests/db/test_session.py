"""Unit tests for ``app.db.session``.

No engine is ever connected: ``create_engine`` and settings are patched.
"""

import importlib
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import sessionmaker

from app.db import session as session_module
from app.db.session import (
    create_db_engine,
    get_engine,
    get_session,
    get_session_factory,
)


@pytest.fixture(autouse=True)
def clean_caches() -> Iterator[None]:
    """Clear the engine and session factory caches around every test.

    Yields:
        None, once the caches are empty.
    """
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    yield
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def test_create_db_engine_enables_pool_pre_ping_and_connect_timeout() -> None:
    """Create db engine sets pool_pre_ping and a bounded connect timeout."""
    with patch("app.db.session.create_engine") as fake_create:
        result = create_db_engine("postgresql+psycopg://u:p@h:5432/d")

    fake_create.assert_called_once_with(
        "postgresql+psycopg://u:p@h:5432/d",
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )
    assert result is fake_create.return_value


def test_get_engine_builds_engine_from_settings_url_once() -> None:
    """Get engine builds the engine from the settings url and caches it."""
    with (
        patch("app.db.session.get_settings") as fake_settings,
        patch("app.db.session.create_db_engine") as fake_create,
    ):
        fake_settings.return_value.database_url = "postgresql+psycopg://x"
        first = get_engine()
        second = get_engine()

    fake_create.assert_called_once_with("postgresql+psycopg://x")
    assert first is second is fake_create.return_value


def test_get_session_factory_is_bound_with_expected_options() -> None:
    """Get session factory returns a sessionmaker bound to the engine."""
    engine = MagicMock()
    with patch("app.db.session.get_engine", return_value=engine):
        factory = get_session_factory()

    assert isinstance(factory, sessionmaker)
    assert factory.kw["bind"] is engine
    assert factory.kw["expire_on_commit"] is False
    assert factory.kw["autoflush"] is False


def test_get_session_factory_is_cached() -> None:
    """Get session factory builds the factory only once."""
    with patch("app.db.session.get_engine", return_value=MagicMock()) as fake_engine:
        assert get_session_factory() is get_session_factory()

    fake_engine.assert_called_once_with()


def test_get_session_yields_session_and_closes_it() -> None:
    """Get session yields the factory session and closes it on exhaustion."""
    session = MagicMock()
    factory = MagicMock(return_value=session)
    with patch("app.db.session.get_session_factory", return_value=factory):
        gen = get_session()
        yielded = next(gen)
        session.close.assert_not_called()
        with pytest.raises(StopIteration):
            next(gen)

    assert yielded is session
    session.close.assert_called_once_with()


def test_get_session_closes_session_when_an_exception_is_thrown() -> None:
    """Get session closes the session when an exception is thrown in."""
    session = MagicMock()
    factory = MagicMock(return_value=session)
    with patch("app.db.session.get_session_factory", return_value=factory):
        gen = get_session()
        next(gen)
        with pytest.raises(RuntimeError, match="boom"):
            gen.throw(RuntimeError("boom"))

    session.close.assert_called_once_with()


def test_importing_session_module_does_not_create_an_engine() -> None:
    """Reloading the module never calls create_engine (no module-level engine)."""
    try:
        with (
            patch("sqlalchemy.create_engine") as fake_top,
            patch("sqlalchemy.engine.create_engine") as fake_engine,
        ):
            importlib.reload(session_module)

        fake_top.assert_not_called()
        fake_engine.assert_not_called()
    finally:
        importlib.reload(session_module)
