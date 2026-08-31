from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from ebauteilefuchs.application.connection import (
    build_connection_overview,
    validate_connection_url,
)
from ebauteilefuchs.domain.errors import DomainError
from ebauteilefuchs.platform.network import discover_ipv4_addresses, hostname
from ebauteilefuchs.web.locations import _render

router = APIRouter(include_in_schema=False)


def _overview(request: Request, selected_url: str | None = None):
    settings = request.app.state.settings
    return build_connection_overview(
        hostname=hostname(),
        port=request.url.port or settings.port,
        local_url=str(request.base_url).rstrip("/"),
        addresses=discover_ipv4_addresses(),
        configured_url=settings.public_base_url,
        selected_url=selected_url,
        scheme=settings.url_scheme,
    )


@router.get("/connection", response_class=HTMLResponse)
def connection_page(request: Request) -> HTMLResponse:
    selected = request.query_params.get("base_url")
    error = None
    try:
        overview = _overview(request, selected)
    except DomainError as caught:
        overview = _overview(request)
        error = caught.message
    return _render(
        request,
        "connection/index.html",
        {"connection": overview, "error": error},
    )


@router.get("/connection/qr.svg")
def connection_qr(request: Request, base_url: str) -> Response:
    url = validate_connection_url(base_url)
    content = request.app.state.qr_renderer.render_qr_svg(url)
    return Response(
        content,
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-store", "Content-Disposition": "inline"},
    )


@router.get("/offline", response_class=HTMLResponse)
def offline_page(request: Request) -> HTMLResponse:
    return _render(request, "offline.html", {})
