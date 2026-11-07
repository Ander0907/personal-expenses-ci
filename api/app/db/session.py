"""Engine and session management (lazy, nothing connects on import)."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

CONNECT_TIMEOUT_SECONDS = 3
"""Maximum seconds libpq waits to establish a database connection."""


def create_db_engine(url: str) -> Engine:
    """Create an engine that validates pooled connections before use.

    Args:
        url: SQLAlchemy database URL.

    Returns:
        A new ``Engine`` with ``pool_pre_ping`` enabled and a bounded
        connection timeout, so health checks fail fast with a 503 instead of
        hanging when the database host is unreachable.
    """
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
    )


@lru_cache
def get_engine() -> Engine:
    """Return the cached process-wide engine built from the settings.

    Returns:
        The shared ``Engine``.
    """
    return create_db_engine(get_settings().database_url)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return the cached session factory bound to the shared engine.

    Returns:
        A ``sessionmaker`` producing sessions without autoflush or expiry.
    """
    return sessionmaker(bind=get_engine(), expire_on_commit=False, autoflush=False)


def get_session() -> Iterator[Session]:
    """Yield a database session and always close it (FastAPI dependency).

    Yields:
        An open ``Session``.
    """
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
