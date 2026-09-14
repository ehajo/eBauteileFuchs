"""Server-rendered M6 export, backup and restore workflows."""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from starlette.background import BackgroundTask

from ebauteilefuchs.application.data_management import (
    DataManagementError,
    DataManagementService,
)
from ebauteilefuchs.web.locations import _render, _verify_csrf

router = APIRouter(include_in_schema=False)


def _service(request: Request) -> DataManagementService:
    return request.app.state.data_management_service


@router.get("/data", response_class=HTMLResponse)
def data_page(request: Request) -> HTMLResponse:
    return _render(
        request,
        "data/index.html",
        {
            "backup_dir": request.app.state.settings.resolved_backup_dir,
            "upload_limit_mb": request.app.state.settings.restore_upload_limit_mb,
        },
    )


@router.get("/data/exports/{export_name}")
def csv_export(request: Request, export_name: str) -> FileResponse:
    try:
        path, filename = _service(request).export_csv(export_name)
    except DataManagementError as error:
        return _render(
            request, "data/index.html", {"error": str(error)}, status_code=422
        )
    return FileResponse(
        path,
        filename=filename,
        media_type="text/csv; charset=utf-8",
        background=BackgroundTask(path.unlink, missing_ok=True),
    )


@router.post("/data/backups")
def create_backup(request: Request, csrf_token: str = Form()) -> Response:
    _verify_csrf(request, csrf_token)
    try:
        backup = _service(request).backup()
    except DataManagementError as error:
        return _render(
            request, "data/index.html", {"error": str(error)}, status_code=422
        )
    return FileResponse(
        backup.path,
        filename=backup.filename,
        media_type="application/zip",
    )


@router.post("/data/restore/preview", response_class=HTMLResponse)
async def preview_restore(
    request: Request,
    backup_file: UploadFile,
    csrf_token: str = Form(),
) -> HTMLResponse:
    _verify_csrf(request, csrf_token)
    if not (backup_file.filename or "").lower().endswith(".zip"):
        return _render(
            request,
            "data/index.html",
            {"error": "Wähle eine eBauteileFuchs-Sicherung im ZIP-Format."},
            status_code=422,
        )
    data_dir = request.app.state.settings.resolved_data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    descriptor, path_value = tempfile.mkstemp(
        prefix="restore-upload-", suffix=".zip", dir=data_dir
    )
    os.close(descriptor)
    upload_path = Path(path_value)
    limit = request.app.state.settings.restore_upload_limit_mb * 1024 * 1024
    size = 0
    try:
        with upload_path.open("wb") as destination:
            while block := await backup_file.read(1024 * 1024):
                size += len(block)
                if size > limit:
                    raise DataManagementError(
                        "Die Sicherungsdatei überschreitet die erlaubte Größe."
                    )
                destination.write(block)
        preview = _service(request).preview_restore(upload_path)
        return _render(request, "data/restore.html", {"preview": preview})
    except DataManagementError as error:
        upload_path.unlink(missing_ok=True)
        return _render(
            request,
            "data/index.html",
            {
                "error": str(error),
                "upload_limit_mb": request.app.state.settings.restore_upload_limit_mb,
            },
            status_code=422,
        )
    finally:
        await backup_file.close()


@router.post("/data/restore", response_class=HTMLResponse)
def restore(
    request: Request,
    restore_token: str = Form(),
    confirmation: str = Form(),
    csrf_token: str = Form(),
) -> HTMLResponse:
    _verify_csrf(request, csrf_token)
    if confirmation.strip() != "WIEDERHERSTELLEN":
        return _render(
            request,
            "data/restore.html",
            {
                "error": "Gib zur Bestätigung exakt WIEDERHERSTELLEN ein.",
                "preview": {
                    "token": restore_token,
                    "created_at": "bereits geprüft",
                    "app_version": "–",
                    "schema_revision": "–",
                    "database_size": "–",
                    "sha256": "–",
                },
            },
            status_code=422,
        )
    try:
        result = _service(request).restore(restore_token)
    except DataManagementError as error:
        return _render(
            request,
            "data/index.html",
            {"error": str(error)},
            status_code=422,
        )
    return _render(request, "data/restored.html", {"result": result})
