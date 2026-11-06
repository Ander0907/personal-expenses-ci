"""Unit tests for ``app.db.base``."""

import pytest
from sqlalchemy.orm import DeclarativeBase

from app.db.base import Base

EXPECTED_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def test_base_is_a_declarative_base() -> None:
    """Base subclasses DeclarativeBase."""
    assert issubclass(Base, DeclarativeBase)


def test_naming_convention_defines_exactly_the_expected_keys() -> None:
    """Naming convention defines exactly the expected keys."""
    assert set(Base.metadata.naming_convention) == set(EXPECTED_CONVENTION)


@pytest.mark.parametrize(("key", "pattern"), EXPECTED_CONVENTION.items())
def test_naming_convention_pattern(key: str, pattern: str) -> None:
    """Naming convention uses the expected pattern for each constraint kind."""
    assert Base.metadata.naming_convention[key] == pattern
