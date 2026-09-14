"""Application service for portable exports and local data protection."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class DataManagementError(Exception):
    """A safe, user-facing data-management failure."""


@dataclass(frozen=True)
class BackupInfo:
    filename: str
    path: Path
    created_at: str
    schema_revision: str
    size: int
    sha256: str


@dataclass(frozen=True)
class RestorePreview:
    token: str
    created_at: str
    schema_revision: str
    app_version: str
    database_size: int
    sha256: str


@dataclass(frozen=True)
class RestoreResult:
    safety_backup: BackupInfo
    restored_schema_revision: str


class DataManagementGateway(Protocol):
    def create_csv_export(self, export_name: str) -> tuple[Path, str]: ...

    def create_backup(self, *, safety_copy: bool = False) -> BackupInfo: ...

    def stage_restore(self, upload_path: Path) -> RestorePreview: ...

    def restore(self, token: str) -> RestoreResult: ...


class DataManagementService:
    def __init__(self, gateway: DataManagementGateway) -> None:
        self._gateway = gateway

    def export_csv(self, export_name: str) -> tuple[Path, str]:
        return self._gateway.create_csv_export(export_name)

    def backup(self) -> BackupInfo:
        return self._gateway.create_backup()

    def preview_restore(self, upload_path: Path) -> RestorePreview:
        return self._gateway.stage_restore(upload_path)

    def restore(self, token: str) -> RestoreResult:
        return self._gateway.restore(token)
