import csv
import sqlite3
import zipfile
from contextlib import closing
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from ebauteilefuchs.application.data_management import DataManagementError
from ebauteilefuchs.config import Settings
from ebauteilefuchs.persistence.data_management import (
    DatabaseWriteGate,
    SqliteDataManagementGateway,
)
from ebauteilefuchs.persistence.database import create_database_engine
from ebauteilefuchs.testing.migration_safety import (
    MigrationTestDatabase,
    migration_test_environment,
)


def _migrated_gateway(tmp_path: Path) -> tuple[SqliteDataManagementGateway, Path]:
    normal_settings = Settings()
    database = tmp_path / f"ebauteilefuchs-migration-test-{uuid4().hex}.sqlite3"
    migration_database = MigrationTestDatabase(
        directory=tmp_path,
        path=database,
        url=f"sqlite+pysqlite:///{database.as_posix()}",
    )
    with migration_test_environment(migration_database, normal_settings):
        command.upgrade(Config("alembic.ini"), "head")
    settings = Settings(
        app_env="test",
        data_dir=tmp_path,
        database_url=f"sqlite+pysqlite:///{database.as_posix()}",
    )
    return SqliteDataManagementGateway(
        settings, create_database_engine(settings)
    ), database


def test_csv_exports_are_utf8_bom_and_keep_values_and_units_separate(
    tmp_path: Path,
) -> None:
    gateway, _ = _migrated_gateway(tmp_path)
    path, filename = gateway.create_csv_export("article-properties")
    assert filename == "artikel-eigenschaften.csv"
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        headers = next(csv.reader(stream))
    assert "originalwert" in headers
    assert "einheit" in headers
    assert "kanonischer_wert" in headers


def test_backup_manifest_checksum_and_restore_with_safety_copy(tmp_path: Path) -> None:
    gateway, database = _migrated_gateway(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "UPDATE category SET name='Vor Sicherung' WHERE code='other'"
        )
        connection.commit()
    backup = gateway.create_backup()
    assert backup.path.is_file()
    with zipfile.ZipFile(backup.path) as archive:
        assert set(archive.namelist()) == {"manifest.json", "database.sqlite3"}

    staged_upload = tmp_path / "upload.zip"
    staged_upload.write_bytes(backup.path.read_bytes())
    preview = gateway.stage_restore(staged_upload)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "UPDATE category SET name='Nach Sicherung' WHERE code='other'"
        )
        connection.commit()
    result = gateway.restore(preview.token)
    with closing(sqlite3.connect(database)) as connection:
        restored_name = connection.execute(
            "SELECT name FROM category WHERE code='other'"
        ).fetchone()[0]
    assert restored_name == "Vor Sicherung"
    assert result.safety_backup.path.is_file()
    assert "vorsicherung" in result.safety_backup.filename


def test_restore_rejects_modified_archive(tmp_path: Path) -> None:
    gateway, _ = _migrated_gateway(tmp_path)
    backup = gateway.create_backup()
    damaged = tmp_path / "damaged.zip"
    damaged.write_bytes(backup.path.read_bytes()[:-20] + b"not-a-valid-end")
    with pytest.raises(DataManagementError):
        gateway.stage_restore(damaged)


def test_backup_restores_into_fresh_installation(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source, source_database = _migrated_gateway(source_dir)
    with closing(sqlite3.connect(source_database)) as connection:
        connection.execute("UPDATE category SET name='Aus Quelle' WHERE code='other'")
        connection.commit()
    backup = source.create_backup()

    target_dir = tmp_path / "fresh"
    target_dir.mkdir()
    target, target_database = _migrated_gateway(target_dir)
    upload = target_dir / "fresh-restore.zip"
    upload.write_bytes(backup.path.read_bytes())
    preview = target.stage_restore(upload)
    target.restore(preview.token)

    with closing(sqlite3.connect(target_database)) as connection:
        name = connection.execute(
            "SELECT name FROM category WHERE code='other'"
        ).fetchone()[0]
    assert name == "Aus Quelle"


def test_restore_maintenance_gate_rejects_new_writes() -> None:
    gate = DatabaseWriteGate()
    assert gate.enter_write()  # the restore request
    gate.begin_maintenance()
    assert not gate.enter_write()
    gate.end_maintenance()
    gate.leave_write()
    assert gate.enter_write()
    gate.leave_write()
