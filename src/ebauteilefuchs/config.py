"""Application configuration loaded from environment variables and .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
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
    backup_dir: Path | None = None
    restore_upload_limit_mb: int = Field(default=512, ge=1, le=4096)
    database_url: str | None = None
    public_base_url: str | None = None
    ssl_certfile: Path | None = None
    ssl_keyfile: Path | None = None
    log_level: str = "INFO"
    mouser_api_key: SecretStr | None = None
    mouser_timeout_seconds: float = Field(default=8.0, ge=1.0, le=30.0)

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        level = value.upper()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if level not in allowed:
            msg = f"log_level must be one of {', '.join(sorted(allowed))}"
            raise ValueError(msg)
        return level

    @field_validator("public_base_url")
    @classmethod
    def validate_public_base_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip().rstrip("/")
        parsed = urlsplit(cleaned)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("public_base_url must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("public_base_url must not contain credentials")
        return cleaned

    @model_validator(mode="after")
    def validate_ssl_files(self) -> "Settings":
        if bool(self.ssl_certfile) != bool(self.ssl_keyfile):
            raise ValueError("ssl_certfile and ssl_keyfile must be configured together")
        return self

    @property
    def url_scheme(self) -> str:
        return "https" if self.ssl_certfile and self.ssl_keyfile else "http"

    @property
    def resolved_data_dir(self) -> Path:
        return (self.data_dir or default_data_dir(self.app_env)).expanduser().resolve()

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        database_path = (self.resolved_data_dir / "ebauteilefuchs.db").as_posix()
        return f"sqlite+pysqlite:///{database_path}"

    @property
    def resolved_backup_dir(self) -> Path:
        return (
            (self.backup_dir or self.resolved_data_dir / "backups")
            .expanduser()
            .resolve()
        )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable settings instance."""

    return Settings()
