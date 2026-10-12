"""Safety boundary for destructive Alembic test runs.

This module deliberately keeps test migrations separate from the application's
normal startup migration path.  It is used by regression tests and CI only.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from alembic.config import Config
from sqlalchemy.engine import make_url

from ebauteilefuchs.config import Settings


class UnsafeMigrationTestDatabaseError(RuntimeError):
    """Raised when a migration test target is not provably disposable."""


@dataclass(frozen=True)
class MigrationTestDatabase:
    """A uniquely named SQLite database inside a temporary directory."""

    directory: Path
    path: Path
    url: str


def _sqlite_path(database_url: str) -> Path:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database:
        raise UnsafeMigrationTestDatabaseError(
            "Migrationstests dürfen nur eine dateibasierte SQLite-Testdatenbank verwenden."
        )
    if url.database == ":memory:":
        raise UnsafeMigrationTestDatabaseError(
            "Migrationstests benötigen eine prüfbare temporäre SQLite-Datei."
        )
    return Path(url.database).expanduser().resolve()


def assert_safe_migration_test_database(
    database_url: str,
    *,
    temporary_directory: Path,
    normal_database_url: str,
    normal_data_dir: Path,
) -> Path:
    """Reject every migration target except our random temporary test database."""

    database_path = _sqlite_path(database_url)
    expected_directory = temporary_directory.expanduser().resolve()
    normal_database_path = _sqlite_path(normal_database_url)
    normal_data_directory = normal_data_dir.expanduser().resolve()

    if database_path == normal_database_path:
        raise UnsafeMigrationTestDatabaseError(
            "Migrationstest abgebrochen: Ziel ist die konfigurierte Nutzdatenbank."
        )
    if database_path.is_relative_to(normal_data_directory):
        raise UnsafeMigrationTestDatabaseError(
            "Migrationstest abgebrochen: Ziel liegt im regulären Datenverzeichnis."
        )
    if database_path.parent != expected_directory:
        raise UnsafeMigrationTestDatabaseError(
            "Migrationstest abgebrochen: Ziel liegt nicht im erzeugten temporären Verzeichnis."
        )
    if (
        not database_path.name.startswith("ebauteilefuchs-migration-test-")
        or database_path.suffix != ".sqlite3"
    ):
        raise UnsafeMigrationTestDatabaseError(
            "Migrationstest abgebrochen: Testdatenbank hat keinen sicheren Zufallsnamen."
        )
    return database_path


@contextmanager
def temporary_migration_test_database(
    normal_settings: Settings,
) -> Iterator[MigrationTestDatabase]:
    """Create and remove an isolated database target for destructive tests."""

    directory = Path(
        tempfile.mkdtemp(prefix="ebauteilefuchs-migration-tests-")
    ).resolve()
    path = directory / f"ebauteilefuchs-migration-test-{uuid4().hex}.sqlite3"
    database = MigrationTestDatabase(
        directory=directory,
        path=path,
        url=f"sqlite+pysqlite:///{path.as_posix()}",
    )
    assert_safe_migration_test_database(
        database.url,
        temporary_directory=directory,
        normal_database_url=normal_settings.resolved_database_url,
        normal_data_dir=normal_settings.resolved_data_dir,
    )
    completed = False
    try:
        yield database
        completed = True
    finally:
        if completed and path.exists():
            path.unlink()
        shutil.rmtree(directory, ignore_errors=True)


@contextmanager
def migration_test_environment(
    database: MigrationTestDatabase, normal_settings: Settings
) -> Iterator[None]:
    """Temporarily point Alembic's settings loader at the guarded test target."""

    variable_names = (
        "EBAUTEILEFUCHS_APP_ENV",
        "EBAUTEILEFUCHS_DATA_DIR",
        "EBAUTEILEFUCHS_DATABASE_URL",
        "EBAUTEILEFUCHS_MIGRATION_TEST_TEMP_DIR",
        "EBAUTEILEFUCHS_MIGRATION_TEST_NORMAL_DATABASE_URL",
        "EBAUTEILEFUCHS_MIGRATION_TEST_NORMAL_DATA_DIR",
    )
    previous = {name: os.environ.get(name) for name in variable_names}
    os.environ["EBAUTEILEFUCHS_APP_ENV"] = "test"
    os.environ["EBAUTEILEFUCHS_DATA_DIR"] = str(database.directory)
    os.environ["EBAUTEILEFUCHS_DATABASE_URL"] = database.url
    os.environ["EBAUTEILEFUCHS_MIGRATION_TEST_TEMP_DIR"] = str(database.directory)
    os.environ["EBAUTEILEFUCHS_MIGRATION_TEST_NORMAL_DATABASE_URL"] = (
        normal_settings.resolved_database_url
    )
    os.environ["EBAUTEILEFUCHS_MIGRATION_TEST_NORMAL_DATA_DIR"] = str(
        normal_settings.resolved_data_dir
    )
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def assert_guarded_migration_environment(settings: Settings) -> None:
    """Require an explicit, disposable target whenever Alembic runs in test mode."""

    if settings.app_env != "test":
        return
    directory_value = os.environ.get("EBAUTEILEFUCHS_MIGRATION_TEST_TEMP_DIR")
    normal_database_url = os.environ.get(
        "EBAUTEILEFUCHS_MIGRATION_TEST_NORMAL_DATABASE_URL"
    )
    normal_data_dir = os.environ.get("EBAUTEILEFUCHS_MIGRATION_TEST_NORMAL_DATA_DIR")
    if not directory_value or not normal_database_url or not normal_data_dir:
        raise UnsafeMigrationTestDatabaseError(
            "Migrationstest abgebrochen: Es fehlt der explizite temporäre Testschutz."
        )
    temporary_directory = Path(directory_value).expanduser().resolve()
    system_temp_directory = Path(tempfile.gettempdir()).resolve()
    if not temporary_directory.is_relative_to(system_temp_directory):
        raise UnsafeMigrationTestDatabaseError(
            "Migrationstest abgebrochen: Das Testverzeichnis liegt nicht im System-Tempordner."
        )
    assert_safe_migration_test_database(
        settings.resolved_database_url,
        temporary_directory=temporary_directory,
        normal_database_url=normal_database_url,
        normal_data_dir=Path(normal_data_dir),
    )


def run_guarded_migration(
    operation: Callable[[Config, str], None],
    alembic_config: Config,
    revision: str,
    *,
    database: MigrationTestDatabase,
    normal_settings: Settings,
) -> None:
    """Run an Alembic operation only after validating its disposable target."""

    assert_safe_migration_test_database(
        database.url,
        temporary_directory=database.directory,
        normal_database_url=normal_settings.resolved_database_url,
        normal_data_dir=normal_settings.resolved_data_dir,
    )
    operation(alembic_config, revision)
