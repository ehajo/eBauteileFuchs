"""M0 server-rendered pages."""

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse

from ebauteilefuchs.main_paths import PACKAGE_DIR

router = APIRouter()


@router.get("/service-worker.js", include_in_schema=False)
def service_worker() -> FileResponse:
    return FileResponse(
        PACKAGE_DIR / "static" / "service-worker.js",
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache",
        },
    )


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "branding": request.app.state.branding,
            "version": request.app.version,
        },
    )
