"""Public release and native-operation contracts introduced in M7."""

from pathlib import Path

from ebauteilefuchs import __version__

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_public_version_has_one_authoritative_source() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert __version__ == "0.1.0"
    assert 'dynamic = ["version"]' in pyproject
    assert 'version = { attr = "ebauteilefuchs.__version__" }' in pyproject


def test_required_public_legal_files_and_branding_notice_exist() -> None:
    for path in (
        "LICENSE",
        "THIRD_PARTY_NOTICES.md",
        "TRADEMARKS.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
    ):
        assert (PROJECT_ROOT / path).is_file()

    trademarks = (PROJECT_ROOT / "TRADEMARKS.md").read_text(encoding="utf-8")
    assert "Apache" in trademarks
    assert "Branding" in trademarks


def test_systemd_template_uses_an_unprivileged_service_and_safe_paths() -> None:
    service = (
        PROJECT_ROOT / "packaging" / "systemd" / "ebauteilefuchs.service"
    ).read_text(encoding="utf-8")

    assert "User=ebauteilefuchs" in service
    assert "After=network-online.target" in service
    assert "EnvironmentFile=-/etc/ebauteilefuchs/ebauteilefuchs.env" in service
    assert (
        "ExecStartPre=/opt/ebauteilefuchs/.venv/bin/python -m alembic upgrade head"
        in service
    )
    assert "Restart=on-failure" in service
    assert "EBAUTEILEFUCHS_DATA_DIR=/var/lib/ebauteilefuchs" in service


def test_public_build_context_excludes_runtime_data_and_secrets() -> None:
    ignored = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8")
    gitignored = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    for entry in (".env", "/data/", "/backups/", "*.sqlite3", "*.zip", "*.pdf"):
        assert entry in ignored
    for entry in (".env", "data/*", "backups/", "exports/", "output/", "tmp/"):
        assert entry in gitignored
