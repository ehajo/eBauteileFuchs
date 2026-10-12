from pathlib import Path

import pytest

from ebauteilefuchs.config import Settings
from ebauteilefuchs.testing.migration_safety import (
    MigrationTestDatabase,
    UnsafeMigrationTestDatabaseError,
    assert_guarded_migration_environment,
    assert_safe_migration_test_database,
    run_guarded_migration,
    temporary_migration_test_database,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _normal_settings(tmp_path: Path) -> Settings:
    data_dir = tmp_path / "regular-data"
    return Settings(
        app_env="development",
        data_dir=data_dir,
        database_url=f"sqlite+pysqlite:///{(data_dir / 'ebauteilefuchs.db').as_posix()}",
    )


def test_temporary_migration_database_has_random_name_and_is_removed(
    tmp_path: Path,
) -> None:
    settings = _normal_settings(tmp_path)
    with temporary_migration_test_database(settings) as database:
        assert database.directory.name.startswith("ebauteilefuchs-migration-tests-")
        assert database.path.name.startswith("ebauteilefuchs-migration-test-")
        assert database.path.suffix == ".sqlite3"
        assert database.path.parent == database.directory
        database.path.touch()
        directory = database.directory
        path = database.path

    assert not path.exists()
    assert not directory.exists()


def test_guard_rejects_configured_normal_database(tmp_path: Path) -> None:
    settings = _normal_settings(tmp_path)
    temporary_directory = tmp_path / "temporary"
    temporary_directory.mkdir()

    with pytest.raises(UnsafeMigrationTestDatabaseError, match="Nutzdatenbank"):
        assert_safe_migration_test_database(
            settings.resolved_database_url,
            temporary_directory=temporary_directory,
            normal_database_url=settings.resolved_database_url,
            normal_data_dir=settings.resolved_data_dir,
        )


def test_test_mode_requires_an_explicit_temporary_migration_guard(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("EBAUTEILEFUCHS_MIGRATION_TEST_TEMP_DIR", raising=False)
    monkeypatch.delenv(
        "EBAUTEILEFUCHS_MIGRATION_TEST_NORMAL_DATABASE_URL", raising=False
    )
    monkeypatch.delenv("EBAUTEILEFUCHS_MIGRATION_TEST_NORMAL_DATA_DIR", raising=False)
    database = tmp_path / f"ebauteilefuchs-migration-test-{'a' * 32}.sqlite3"
    settings = Settings(
        app_env="test",
        data_dir=tmp_path,
        database_url=f"sqlite+pysqlite:///{database.as_posix()}",
    )

    with pytest.raises(UnsafeMigrationTestDatabaseError, match="Testschutz"):
        assert_guarded_migration_environment(settings)


def test_guard_rejects_database_in_regular_data_directory(tmp_path: Path) -> None:
    settings = _normal_settings(tmp_path)
    regular_data_database = settings.resolved_data_dir / (
        "ebauteilefuchs-migration-test-" + "a" * 32 + ".sqlite3"
    )

    with pytest.raises(
        UnsafeMigrationTestDatabaseError, match="regulären Datenverzeichnis"
    ):
        assert_safe_migration_test_database(
            f"sqlite+pysqlite:///{regular_data_database.as_posix()}",
            temporary_directory=settings.resolved_data_dir,
            normal_database_url=settings.resolved_database_url,
            normal_data_dir=settings.resolved_data_dir,
        )


def test_guard_rejects_unexpected_target_before_operation(tmp_path: Path) -> None:
    settings = _normal_settings(tmp_path)
    temporary_directory = tmp_path / "temporary"
    temporary_directory.mkdir()
    unsafe_database = temporary_directory / "migration.db"
    called = False

    def operation(_config: object, _revision: str) -> None:
        nonlocal called
        called = True

    with pytest.raises(UnsafeMigrationTestDatabaseError, match="sicheren Zufallsnamen"):
        run_guarded_migration(
            operation,
            object(),  # type: ignore[arg-type]
            "base",
            database=MigrationTestDatabase(
                directory=temporary_directory,
                path=unsafe_database,
                url=f"sqlite+pysqlite:///{unsafe_database.as_posix()}",
            ),
            normal_settings=settings,
        )

    assert not called


def test_ci_uses_the_guarded_migration_verifier() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "python scripts/verify-migrations.py" in workflow
    assert "python -m alembic upgrade head" not in workflow
    assert "python -m alembic downgrade" not in workflow
