"""SQLite CSV export, backup and validated restore adapter."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sqlite3
import tempfile
import threading
import time
import zipfile
from collections.abc import Sequence
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import Engine
from sqlalchemy.engine import make_url

from ebauteilefuchs import __version__
from ebauteilefuchs.application.data_management import (
    BackupInfo,
    DataManagementError,
    RestorePreview,
    RestoreResult,
)
from ebauteilefuchs.config import Settings

BACKUP_FORMAT = "ebauteilefuchs-backup"
BACKUP_FORMAT_VERSION = 1
CURRENT_SCHEMA_REVISION = "0008_location_grid"
SUPPORTED_SCHEMA_REVISIONS = {"0007_article_barcodes", CURRENT_SCHEMA_REVISION}
DATABASE_MEMBER = "database.sqlite3"
MANIFEST_MEMBER = "manifest.json"
EXPORT_NAMES = {
    "articles": "artikel.csv",
    "article-properties": "artikel-eigenschaften.csv",
    "locations": "lagerplaetze.csv",
    "inventory": "bestaende.csv",
}


def _sqlite_path(database_url: str) -> Path:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database:
        raise DataManagementError(
            "Sicherung und Wiederherstellung werden derzeit nur für eine "
            "dateibasierte SQLite-Datenbank unterstützt."
        )
    if url.database == ":memory:":
        raise DataManagementError(
            "Eine temporäre Speicherdatenbank kann nicht gesichert werden."
        )
    return Path(url.database).expanduser().resolve()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _plain(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    # Prevent a CSV opened in spreadsheet software from executing a formula.
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


class SqliteDataManagementGateway:
    def __init__(
        self,
        settings: Settings,
        engine: Engine,
        write_gate: DatabaseWriteGate | None = None,
    ) -> None:
        self._settings = settings
        self._engine = engine
        self._database_path = _sqlite_path(settings.resolved_database_url)
        self._backup_dir = settings.resolved_backup_dir
        self._staging_dir = settings.resolved_data_dir / "restore-staging"
        self._lock = threading.Lock()
        self._write_gate = write_gate or DatabaseWriteGate()

    def create_csv_export(self, export_name: str) -> tuple[Path, str]:
        if export_name not in EXPORT_NAMES:
            raise DataManagementError("Dieser CSV-Export ist nicht bekannt.")
        self._settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)
        descriptor, path_value = tempfile.mkstemp(
            prefix="ebauteilefuchs-export-",
            suffix=".csv",
            dir=self._settings.resolved_data_dir,
        )
        os.close(descriptor)
        path = Path(path_value)
        try:
            headers, query = self._export_spec(export_name)
            with closing(sqlite3.connect(self._database_path)) as connection:
                with path.open("w", encoding="utf-8-sig", newline="") as stream:
                    writer = csv.writer(stream, dialect="excel", lineterminator="\r\n")
                    writer.writerow(headers)
                    for row in connection.execute(query):
                        writer.writerow(_plain(value) for value in row)
            return path, EXPORT_NAMES[export_name]
        except DataManagementError:
            path.unlink(missing_ok=True)
            raise
        except (OSError, sqlite3.Error) as exc:
            path.unlink(missing_ok=True)
            raise DataManagementError(
                "Der CSV-Export konnte nicht erstellt werden. Prüfe den Datenordner."
            ) from exc

    def _export_spec(self, export_name: str) -> tuple[Sequence[str], str]:
        queries = {
            "articles": (
                (
                    "article_id",
                    "bezeichnung",
                    "hersteller",
                    "hersteller_artikelnummer",
                    "kategorie",
                    "beschreibung",
                    "datenblatt_url",
                    "produkt_url",
                    "notiz",
                    "lieferanten_artikelnummern",
                    "aktiv",
                    "erstellt_utc",
                    "geaendert_utc",
                ),
                """SELECT a.id, a.name, m.name, a.manufacturer_part_number, c.name,
                    a.description, a.datasheet_url, a.product_url, a.note,
                    GROUP_CONCAT(s.name || ': ' || sp.supplier_part_number, ' | '),
                    a.is_active, a.created_at, a.updated_at
                    FROM article a JOIN category c ON c.id=a.category_id
                    LEFT JOIN manufacturer m ON m.id=a.manufacturer_id
                    LEFT JOIN supplier_part sp ON sp.article_id=a.id
                    LEFT JOIN supplier s ON s.id=sp.supplier_id
                    GROUP BY a.id ORDER BY a.name COLLATE NOCASE, a.id""",
            ),
            "article-properties": (
                (
                    "article_id",
                    "bezeichnung",
                    "eigenschaft_code",
                    "eigenschaft",
                    "originalwert",
                    "numerischer_wert",
                    "einheit",
                    "kanonischer_wert",
                    "kanonische_einheit",
                    "sortierung",
                ),
                """SELECT aa.article_id, a.name, ad.code,
                    COALESCE(ad.name, aa.custom_name), aa.raw_value, aa.numeric_value,
                    aa.unit, aa.canonical_numeric_value, aa.canonical_unit, aa.sort_order
                    FROM article_attribute aa JOIN article a ON a.id=aa.article_id
                    LEFT JOIN attribute_definition ad ON ad.id=aa.attribute_definition_id
                    ORDER BY a.name COLLATE NOCASE, aa.sort_order, aa.id""",
            ),
            "locations": (
                (
                    "lagerplatz_id",
                    "uebergeordneter_lagerplatz_id",
                    "code",
                    "name",
                    "typ",
                    "vollstaendiger_pfad",
                    "beschreibung",
                    "aktiv",
                    "erstellt_utc",
                    "geaendert_utc",
                ),
                """WITH RECURSIVE paths(id, path) AS (
                    SELECT id, code FROM location WHERE parent_id IS NULL
                    UNION ALL SELECT child.id, paths.path || ' / ' || child.code
                    FROM location child JOIN paths ON child.parent_id=paths.id)
                    SELECT l.id, l.parent_id, l.code, l.name, lt.name, paths.path,
                    l.description, l.is_active, l.created_at, l.updated_at
                    FROM location l JOIN location_type lt ON lt.id=l.location_type_id
                    JOIN paths ON paths.id=l.id ORDER BY paths.path COLLATE NOCASE""",
            ),
            "inventory": (
                (
                    "artikel_id",
                    "bezeichnung",
                    "hersteller_artikelnummer",
                    "lagerplatz_id",
                    "lagerpfad",
                    "menge",
                    "einheit",
                    "geaendert_utc",
                ),
                """WITH RECURSIVE paths(id, path) AS (
                    SELECT id, code FROM location WHERE parent_id IS NULL
                    UNION ALL SELECT child.id, paths.path || ' / ' || child.code
                    FROM location child JOIN paths ON child.parent_id=paths.id)
                    SELECT a.id, a.name, a.manufacturer_part_number, b.location_id,
                    paths.path, b.quantity, b.unit, b.updated_at
                    FROM inventory_balance b JOIN article a ON a.id=b.article_id
                    JOIN paths ON paths.id=b.location_id
                    ORDER BY a.name COLLATE NOCASE, paths.path COLLATE NOCASE""",
            ),
        }
        return queries[export_name]

    def create_backup(self, *, safety_copy: bool = False) -> BackupInfo:
        try:
            with self._lock:
                return self._create_backup_locked(safety_copy=safety_copy)
        except DataManagementError:
            raise
        except (OSError, sqlite3.Error) as exc:
            raise DataManagementError(
                "Die Sicherung konnte nicht erstellt werden. Prüfe Daten- und "
                "Sicherungsordner."
            ) from exc

    def _create_backup_locked(self, *, safety_copy: bool) -> BackupInfo:
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        kind = "vorsicherung" if safety_copy else "sicherung"
        filename = f"ebauteilefuchs-{kind}-{stamp}-{uuid4().hex[:8]}.zip"
        target = self._backup_dir / filename
        with tempfile.TemporaryDirectory(dir=self._backup_dir) as temp_name:
            temp_dir = Path(temp_name)
            snapshot = temp_dir / DATABASE_MEMBER
            source = sqlite3.connect(self._database_path)
            destination = sqlite3.connect(snapshot)
            try:
                source.backup(destination)
            finally:
                destination.close()
                source.close()
            schema_revision = self._validate_database(snapshot)
            digest = _sha256(snapshot)
            created_at = datetime.now(UTC).isoformat()
            manifest = {
                "format": BACKUP_FORMAT,
                "format_version": BACKUP_FORMAT_VERSION,
                "app_version": __version__,
                "schema_revision": schema_revision,
                "created_at": created_at,
                "database_file": DATABASE_MEMBER,
                "database_size": snapshot.stat().st_size,
                "database_sha256": digest,
            }
            archive_temp = temp_dir / "backup.zip"
            with zipfile.ZipFile(archive_temp, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(MANIFEST_MEMBER, json.dumps(manifest, indent=2) + "\n")
                archive.write(snapshot, DATABASE_MEMBER)
            os.replace(archive_temp, target)
        return BackupInfo(
            filename, target, created_at, schema_revision, target.stat().st_size, digest
        )

    def stage_restore(self, upload_path: Path) -> RestorePreview:
        try:
            return self._stage_restore(upload_path)
        except DataManagementError:
            raise
        except (OSError, sqlite3.Error) as exc:
            upload_path.unlink(missing_ok=True)
            raise DataManagementError(
                "Die Sicherungsdatei konnte nicht sicher geprüft werden."
            ) from exc

    def _stage_restore(self, upload_path: Path) -> RestorePreview:
        token = uuid4().hex
        self._staging_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_staging()
        staged_archive = self._staging_dir / f"{token}.zip"
        os.replace(upload_path, staged_archive)
        try:
            manifest = self._validate_archive(staged_archive, extract_database=False)
        except Exception:
            staged_archive.unlink(missing_ok=True)
            raise
        return RestorePreview(
            token=token,
            created_at=manifest["created_at"],
            schema_revision=manifest["schema_revision"],
            app_version=manifest["app_version"],
            database_size=manifest["database_size"],
            sha256=manifest["database_sha256"],
        )

    def _cleanup_staging(self) -> None:
        cutoff = time.time() - 24 * 60 * 60
        for candidate in self._staging_dir.iterdir():
            try:
                if candidate.is_file() and candidate.stat().st_mtime < cutoff:
                    candidate.unlink()
            except OSError:
                # A concurrently checked file is retained for the next cleanup.
                continue

    def restore(self, token: str) -> RestoreResult:
        if not re.fullmatch(r"[0-9a-f]{32}", token):
            raise DataManagementError("Die Wiederherstellungsfreigabe ist ungültig.")
        archive_path = self._staging_dir / f"{token}.zip"
        if not archive_path.is_file():
            raise DataManagementError(
                "Die vorbereitete Sicherung wurde nicht gefunden."
            )
        try:
            return self._restore_locked(archive_path, token)
        except DataManagementError:
            raise
        except (OSError, sqlite3.Error) as exc:
            raise DataManagementError(
                "Die Wiederherstellung konnte sicher nicht abgeschlossen werden. "
                "Die Vorsicherung bleibt erhalten."
            ) from exc

    def _restore_locked(self, archive_path: Path, token: str) -> RestoreResult:
        with self._lock:
            extracted = self._staging_dir / f"{token}.sqlite3"
            rollback = self._database_path.with_name(
                f".{self._database_path.name}.restore-{token}"
            )
            try:
                self._validate_archive(
                    archive_path, extract_database=True, target=extracted
                )
                self._write_gate.begin_maintenance()
                try:
                    safety = self._create_backup_locked(safety_copy=True)
                    self._engine.dispose()
                    with closing(sqlite3.connect(self._database_path)) as connection:
                        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    for suffix in ("-wal", "-shm"):
                        Path(f"{self._database_path}{suffix}").unlink(missing_ok=True)
                    os.replace(self._database_path, rollback)
                    try:
                        os.replace(extracted, self._database_path)
                        self._validate_database(self._database_path)
                    except Exception:
                        self._database_path.unlink(missing_ok=True)
                        os.replace(rollback, self._database_path)
                        raise
                    rollback.unlink(missing_ok=True)
                    return RestoreResult(safety, CURRENT_SCHEMA_REVISION)
                finally:
                    self._write_gate.end_maintenance()
            finally:
                extracted.unlink(missing_ok=True)
                archive_path.unlink(missing_ok=True)

    def _validate_archive(
        self, archive_path: Path, *, extract_database: bool, target: Path | None = None
    ) -> dict:
        max_size = self._settings.restore_upload_limit_mb * 1024 * 1024
        if archive_path.stat().st_size > max_size:
            raise DataManagementError(
                "Die Sicherungsdatei überschreitet die erlaubte Größe."
            )
        try:
            with zipfile.ZipFile(archive_path) as archive:
                if set(archive.namelist()) != {MANIFEST_MEMBER, DATABASE_MEMBER}:
                    raise DataManagementError(
                        "Die ZIP-Datei hat nicht den erwarteten Sicherungsinhalt."
                    )
                database_info = archive.getinfo(DATABASE_MEMBER)
                if archive.getinfo(MANIFEST_MEMBER).file_size > 64 * 1024:
                    raise DataManagementError(
                        "Das Sicherungsmanifest ist unzulässig groß."
                    )
                if database_info.file_size > max_size or database_info.file_size > max(
                    archive_path.stat().st_size * 200, 10 * 1024 * 1024
                ):
                    raise DataManagementError(
                        "Die entpackte Datenbank ist unzulässig groß."
                    )
                manifest = json.loads(archive.read(MANIFEST_MEMBER))
                required = {
                    "format",
                    "format_version",
                    "app_version",
                    "schema_revision",
                    "created_at",
                    "database_file",
                    "database_size",
                    "database_sha256",
                }
                if (
                    set(manifest) != required
                    or manifest["format"] != BACKUP_FORMAT
                    or manifest["format_version"] != BACKUP_FORMAT_VERSION
                    or manifest["database_file"] != DATABASE_MEMBER
                ):
                    raise DataManagementError(
                        "Das Sicherungsmanifest ist ungültig oder nicht unterstützt."
                    )
                if manifest["schema_revision"] not in SUPPORTED_SCHEMA_REVISIONS:
                    raise DataManagementError(
                        "Die Sicherung verwendet einen nicht unterstützten Datenbankstand."
                    )
                extract_path = (
                    target or self._staging_dir / f"check-{uuid4().hex}.sqlite3"
                )
                with (
                    archive.open(DATABASE_MEMBER) as source,
                    extract_path.open("wb") as destination,
                ):
                    digest = hashlib.sha256()
                    size = 0
                    while block := source.read(1024 * 1024):
                        size += len(block)
                        if size > max_size:
                            raise DataManagementError(
                                "Die entpackte Datenbank ist unzulässig groß."
                            )
                        digest.update(block)
                        destination.write(block)
                if (
                    size != manifest["database_size"]
                    or digest.hexdigest() != manifest["database_sha256"]
                ):
                    raise DataManagementError(
                        "Prüfsumme oder Größe der Sicherung stimmt nicht."
                    )
                if manifest["schema_revision"] != CURRENT_SCHEMA_REVISION:
                    self._upgrade_snapshot(extract_path)
                self._validate_database(extract_path)
                if not extract_database:
                    extract_path.unlink(missing_ok=True)
                return manifest
        except (zipfile.BadZipFile, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise DataManagementError(
                "Die Datei ist keine gültige eBauteileFuchs-Sicherung."
            ) from exc

    @staticmethod
    def _validate_database(path: Path) -> str:
        try:
            connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
            try:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()
                if not integrity or integrity[0] != "ok":
                    raise DataManagementError(
                        "Die Datenbank-Integritätsprüfung ist fehlgeschlagen."
                    )
                if connection.execute("PRAGMA foreign_key_check").fetchone():
                    raise DataManagementError(
                        "Die Sicherung enthält ungültige Datenbankbezüge."
                    )
                row = connection.execute(
                    "SELECT version_num FROM alembic_version"
                ).fetchone()
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise DataManagementError(
                "Die Sicherung enthält keine lesbare eBauteileFuchs-Datenbank."
            ) from exc
        if not row or row[0] != CURRENT_SCHEMA_REVISION:
            raise DataManagementError(
                "Die Sicherung verwendet einen nicht unterstützten Datenbankstand."
            )
        return str(row[0])

    @staticmethod
    def _upgrade_snapshot(path: Path) -> None:
        with closing(sqlite3.connect(path)) as connection:
            connection.execute("ALTER TABLE location ADD COLUMN grid_columns INTEGER")
            connection.execute("ALTER TABLE location ADD COLUMN grid_rows INTEGER")
            connection.execute(
                "UPDATE alembic_version SET version_num = ?",
                (CURRENT_SCHEMA_REVISION,),
            )
            connection.commit()


class DatabaseWriteGate:
    """Coordinate ordinary writes with the short restore maintenance window."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._active_writes = 0
        self._maintenance = False

    def enter_write(self) -> bool:
        with self._condition:
            if self._maintenance:
                return False
            self._active_writes += 1
            return True

    def leave_write(self) -> None:
        with self._condition:
            self._active_writes -= 1
            self._condition.notify_all()

    def begin_maintenance(self) -> None:
        with self._condition:
            self._maintenance = True
            # The restore form itself is one active write when called via HTTP.
            while self._active_writes > 1:
                self._condition.wait()

    def end_maintenance(self) -> None:
        with self._condition:
            self._maintenance = False
            self._condition.notify_all()
