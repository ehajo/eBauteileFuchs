from pathlib import Path

import pytest
from pydantic import ValidationError

from ebauteilefuchs.config import Settings


def test_settings_resolve_development_data_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    settings = Settings(app_env="development", data_dir=None, database_url=None)

    assert settings.resolved_data_dir == tmp_path / "data"
    assert settings.resolved_database_url.endswith("/data/ebauteilefuchs.db")


def test_settings_reject_invalid_port() -> None:
    with pytest.raises(ValidationError):
        Settings(port=70_000)


def test_settings_normalize_log_level() -> None:
    assert Settings(log_level="debug").log_level == "DEBUG"


def test_default_port_is_8008() -> None:
    assert Settings().port == 8008
