"""Unit tests for ``app.core.config``.

Environment variables are controlled exclusively through ``monkeypatch`` and
``Settings`` is always built with ``_env_file=None`` so a local ``.env`` file
never leaks into the tests.
"""

from collections.abc import Callable, Iterator

import pytest
from pydantic import SecretStr, ValidationError
from sqlalchemy.engine import make_url

from app.core.config import Settings, get_settings

REQUIRED_VARS = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
OPTIONAL_VARS = ("DATABASE_HOST", "DATABASE_PORT")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Remove every settings variable and reset the ``get_settings`` cache.

    Args:
        monkeypatch: Pytest fixture used to alter the environment.

    Yields:
        None, once the environment is clean.
    """
    for name in (*REQUIRED_VARS, *OPTIONAL_VARS):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the three required variables with fake values.

    Args:
        monkeypatch: Pytest fixture used to alter the environment.
    """
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_password")
    monkeypatch.setenv("POSTGRES_DB", "test_db")


def make_settings() -> Settings:
    """Build ``Settings`` ignoring any local ``.env`` file.

    Returns:
        A ``Settings`` instance populated from the process environment only.
    """
    return Settings(_env_file=None)


@pytest.mark.usefixtures("base_env")
def test_settings_reads_required_values_from_environment() -> None:
    """Settings reads required values from environment."""
    settings = make_settings()

    assert settings.postgres_user == "test_user"
    assert settings.postgres_db == "test_db"
    assert settings.postgres_password.get_secret_value() == "test_password"


@pytest.mark.usefixtures("base_env")
def test_settings_uses_compose_service_name_and_default_port() -> None:
    """Settings uses compose service name and default port."""
    settings = make_settings()

    assert settings.database_host == "db"
    assert settings.database_port == 5432


@pytest.mark.usefixtures("base_env")
def test_settings_reads_host_and_port_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings reads host and port overrides."""
    monkeypatch.setenv("DATABASE_HOST", "other-host")
    monkeypatch.setenv("DATABASE_PORT", "6543")

    settings = make_settings()

    assert settings.database_host == "other-host"
    assert settings.database_port == 6543
    assert isinstance(settings.database_port, int)


@pytest.mark.usefixtures("base_env")
def test_settings_rejects_non_numeric_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings rejects non numeric port."""
    monkeypatch.setenv("DATABASE_PORT", "not-a-port")

    with pytest.raises(ValidationError):
        make_settings()


@pytest.mark.parametrize("missing", REQUIRED_VARS)
def test_settings_raises_when_required_variable_is_missing(
    missing: str, base_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Settings raises when required variable is missing."""
    monkeypatch.delenv(missing)

    with pytest.raises(ValidationError):
        make_settings()


@pytest.mark.usefixtures("base_env")
def test_postgres_password_is_a_secret_str() -> None:
    """Postgres password is a secret str."""
    settings = make_settings()

    assert isinstance(settings.postgres_password, SecretStr)


@pytest.mark.usefixtures("base_env")
@pytest.mark.parametrize("render", [repr, str])
def test_rendering_settings_does_not_leak_the_password(
    render: Callable[[object], str],
) -> None:
    """Rendering settings does not leak the password."""
    settings = make_settings()

    assert "test_password" not in render(settings)


@pytest.mark.usefixtures("base_env")
def test_database_url_uses_psycopg_driver_and_service_name() -> None:
    """Database url uses psycopg driver and service name."""
    settings = make_settings()

    assert settings.database_url == (
        "postgresql+psycopg://test_user:test_password@db:5432/test_db"
    )


@pytest.mark.usefixtures("base_env")
def test_database_url_reflects_host_and_port_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Database url reflects host and port overrides."""
    monkeypatch.setenv("DATABASE_HOST", "other-host")
    monkeypatch.setenv("DATABASE_PORT", "6543")

    url = make_url(make_settings().database_url)

    assert url.host == "other-host"
    assert url.port == 6543


@pytest.mark.usefixtures("base_env")
@pytest.mark.parametrize("password", ["p@ss:w/rd", "a b#c?d%e", "x&y=z+1"])
def test_database_url_escapes_special_characters_in_password(
    password: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Database url escapes special characters in password."""
    monkeypatch.setenv("POSTGRES_PASSWORD", password)

    url = make_url(make_settings().database_url)

    assert url.drivername == "postgresql+psycopg"
    assert url.password == password
    assert url.username == "test_user"
    assert url.host == "db"
    assert url.port == 5432
    assert url.database == "test_db"


@pytest.mark.usefixtures("base_env")
def test_get_settings_returns_a_cached_singleton() -> None:
    """Get settings returns a cached singleton."""
    first = get_settings()
    second = get_settings()

    assert isinstance(first, Settings)
    assert first is second


@pytest.mark.usefixtures("base_env")
def test_get_settings_rebuilds_after_cache_clear() -> None:
    """Get settings rebuilds after cache clear."""
    first = get_settings()

    get_settings.cache_clear()

    assert get_settings() is not first
