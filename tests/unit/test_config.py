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


def test_public_base_url_is_normalized_and_validated() -> None:
    assert (
        Settings(public_base_url=" http://lager.local:8008/ ").public_base_url
        == "http://lager.local:8008"
    )
    with pytest.raises(ValidationError):
        Settings(public_base_url="lager.local:8008")
    with pytest.raises(ValidationError):
        Settings(public_base_url="http://name:secret@lager.local:8008")


def test_https_configuration_requires_certificate_and_key(tmp_path: Path) -> None:
    assert Settings().url_scheme == "http"
    with pytest.raises(ValidationError):
        Settings(ssl_certfile=tmp_path / "certificate.pem")
    configured = Settings(
        ssl_certfile=tmp_path / "certificate.pem",
        ssl_keyfile=tmp_path / "key.pem",
    )
    assert configured.url_scheme == "https"
