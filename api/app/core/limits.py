"""Shared numeric limits used by routers and schemas."""

MAX_DB_INT = 2_147_483_647
"""Largest value of a PostgreSQL ``integer`` (int4) column."""

DEFAULT_LIMIT = 100
"""Default page size for list endpoints."""

MAX_LIMIT = 500
"""Maximum page size accepted by list endpoints."""

MAX_OFFSET = 1_000_000
"""Maximum offset accepted by list endpoints."""
