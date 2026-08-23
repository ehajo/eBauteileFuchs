"""Application configuration loaded from environment variables and .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ebauteilefuchs.platform.paths import default_data_dir


class Settings(BaseSettings):
    """Validated runtime settings.

    Environment variables use the ``EBAUTEILEFUCHS_`` prefix. A local ``.env``
    file is supported for development and is intentionally ignored by Git.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="EBAUTEILEFUCHS_",
        extra="ignore",
        frozen=True,
    )

    app_env: Literal["development", "production", "test"] = "development"
    host: str = "0.0.0.0"
    port: int = Field(default=8008, ge=1, le=65535)
    data_dir: Path | None = None
    database_url: str | None = None
    log_level: str = "INFO"
    mouser_api_key: SecretStr | None = None

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        level = value.upper()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if level not in allowed:
            msg = f"log_level must be one of {', '.join(sorted(allowed))}"
            raise ValueError(msg)
        return level

    @property
    def resolved_data_dir(self) -> Path:
        return (self.data_dir or default_data_dir(self.app_env)).expanduser().resolve()

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        database_path = (self.resolved_data_dir / "ebauteilefuchs.db").as_posix()
        return f"sqlite+pysqlite:///{database_path}"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable settings instance."""

    return Settings()
