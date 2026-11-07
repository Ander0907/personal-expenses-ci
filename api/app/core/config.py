"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Runtime configuration read from the environment or a ``.env`` file.

    Attributes:
        postgres_user: Database user name.
        postgres_password: Database password, never rendered in repr/str.
        postgres_db: Database name.
        database_host: Database host (defaults to the compose service name).
        database_port: Database TCP port.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    database_host: str = "db"
    database_port: int = 5432

    @property
    def database_url(self) -> str:
        """Build the SQLAlchemy URL for the psycopg driver.

        Special characters in credentials are escaped by SQLAlchemy.

        Returns:
            The full database URL including the plain-text password.
        """
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.database_host,
            port=self.database_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings.

    Returns:
        The process-wide ``Settings`` instance.
    """
    return Settings()
