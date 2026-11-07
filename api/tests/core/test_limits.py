"""Unit tests for ``app.core.limits``."""

from app.core.limits import DEFAULT_LIMIT, MAX_DB_INT, MAX_LIMIT, MAX_OFFSET


def test_max_db_int_is_the_postgresql_int4_maximum() -> None:
    """Max DB int equals the largest PostgreSQL ``integer`` value."""
    assert MAX_DB_INT == 2_147_483_647


def test_pagination_limits_match_the_project_decisions() -> None:
    """Pagination defaults and ceilings follow the approved decisions."""
    assert DEFAULT_LIMIT == 100
    assert MAX_LIMIT == 500
    assert MAX_OFFSET == 1_000_000
