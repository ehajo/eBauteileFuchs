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
    articles = request.app.state.article_service_factory().list_articles(
        include_inactive=False
    )
    locations = request.app.state.location_service_factory().list_details(
        include_inactive=False
    )
    inventory = request.app.state.inventory_service_factory()
    positions = inventory.list_positions()
    movements = inventory.list_movements(limit=5)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "branding": request.app.state.branding,
            "version": request.app.version,
            "dashboard": {
                "article_count": len(articles),
                "location_count": len(locations),
                "occupied_location_count": len(
                    {item.balance.location_id for item in positions}
                ),
                "last_movement": movements[0] if movements else None,
            },
            "movements": movements,
            "movement_labels": {
                "stock_in": "Einlagerung",
                "stock_out": "Auslagerung",
                "transfer": "Umlagerung",
                "adjustment": "Korrektur",
                "initial": "Anfangsbestand",
            },
        },
    )


@router.get("/about", response_class=HTMLResponse, include_in_schema=False)
def about(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="about.html",
        context={
            "branding": request.app.state.branding,
            "version": request.app.version,
        },
    )
