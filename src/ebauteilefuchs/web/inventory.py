"""Server-rendered M3 stock-in, stock-out, transfer, and adjustment workflows."""

import secrets
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ebauteilefuchs.domain.errors import DomainError, ValidationError
from ebauteilefuchs.web.locations import _render, _verify_csrf

router = APIRouter(include_in_schema=False)

MODE_LABELS = {
    "stock-in": ("Einlagern", "Bestand hinzufügen"),
    "stock-out": ("Auslagern", "Bestand entnehmen"),
    "initial": ("Initialen Bestand erfassen", "Anfangsbestand buchen"),
    "transfer": ("Umlagern", "Umlagerung buchen"),
    "adjustment": ("Bestand korrigieren", "Korrektur buchen"),
}


def _services(request: Request):
    return (
        request.app.state.inventory_service_factory(),
        request.app.state.article_service_factory(),
        request.app.state.location_service_factory(),
    )


def _context(
    request: Request,
    mode: str,
    *,
    values: dict | None = None,
    error: str | None = None,
    result=None,
) -> dict:
    inventory, articles, locations = _services(request)
    current_values = values or {}

    def supplied(name: str, default: str = "") -> str:
        return str(current_values.get(name, request.query_params.get(name, default)))

    query = supplied("q")
    article_id = supplied("article_id")
    location_id = supplied("location_id")
    source_location_id = supplied("source_location_id", location_id)
    target_location_id = supplied("target_location_id")
    article_results = (
        articles.list_articles(query=query, include_inactive=False) if query else []
    )
    selected_article = None
    if article_id:
        try:
            candidate = articles.get(UUID(article_id))
            if candidate.article.is_active:
                selected_article = candidate
        except (ValueError, DomainError):
            article_id = ""
    location_results = locations.list_details(include_inactive=False)
    positions = []
    if article_id:
        try:
            positions = inventory.list_positions(article_id=UUID(article_id))
        except ValueError:
            pass
    position_location_ids = {item.balance.location_id for item in positions}
    source_locations = [
        item for item in location_results if item.location.id in position_location_ids
    ]
    preserved = {
        "location_id": location_id,
        "source_location_id": source_location_id,
        "target_location_id": target_location_id,
    }
    article_choices = []
    for details in article_results:
        parameters = {
            "q": query,
            "article_id": str(details.article.id),
            **{key: value for key, value in preserved.items() if value},
        }
        article_choices.append(
            {
                "details": details,
                "url": f"/inventory/{mode}?{urlencode(parameters)}",
            }
        )
    return {
        "mode": mode,
        "heading": MODE_LABELS[mode][0],
        "submit_label": MODE_LABELS[mode][1],
        "article_choices": article_choices,
        "selected_article": selected_article,
        "locations": location_results,
        "source_locations": source_locations,
        "positions": positions,
        "values": {
            "q": query,
            "article_id": article_id,
            "location_id": location_id,
            "source_location_id": source_location_id,
            "target_location_id": target_location_id,
            "quantity": str(current_values.get("quantity", "")),
            "difference": str(current_values.get("difference", "")),
            "target_quantity": str(current_values.get("target_quantity", "")),
            "adjustment_mode": str(current_values.get("adjustment_mode", "target")),
            "unit": str(current_values.get("unit", "Stück")),
            "comment": str(current_values.get("comment", "")),
        },
        "booking_token": secrets.token_urlsafe(24),
        "error": error,
        "result": result,
    }


@router.get("/inventory", response_class=HTMLResponse)
def inventory_overview(request: Request) -> HTMLResponse:
    inventory, _, _ = _services(request)
    return _render(
        request,
        "inventory/list.html",
        {
            "positions": inventory.list_positions(),
            "movements": inventory.list_movements(limit=20),
        },
    )


def _get_form(mode: str, request: Request) -> HTMLResponse:
    return _render(request, "inventory/form.html", _context(request, mode))


@router.get("/inventory/stock-in", response_class=HTMLResponse)
def stock_in_form(request: Request) -> HTMLResponse:
    return _get_form("stock-in", request)


@router.get("/inventory/stock-out", response_class=HTMLResponse)
def stock_out_form(request: Request) -> HTMLResponse:
    return _get_form("stock-out", request)


@router.get("/inventory/initial", response_class=HTMLResponse)
def initial_form(request: Request) -> HTMLResponse:
    return _get_form("initial", request)


@router.get("/inventory/transfer", response_class=HTMLResponse)
def transfer_form(request: Request) -> HTMLResponse:
    return _get_form("transfer", request)


@router.get("/inventory/adjustment", response_class=HTMLResponse)
def adjustment_form(request: Request) -> HTMLResponse:
    return _get_form("adjustment", request)


async def _book(mode: str, request: Request) -> HTMLResponse:
    form = await request.form()
    values = {key: str(value) for key, value in form.items()}
    try:
        _verify_csrf(request, values.get("csrf_token", ""))
        inventory, _, _ = _services(request)
        common = {
            "article_id": UUID(values.get("article_id", "")),
            "idempotency_key": values.get("idempotency_key", ""),
            "unit": values.get("unit", "Stück"),
            "comment": values.get("comment", ""),
        }
        if mode == "transfer":
            result = inventory.transfer(
                **common,
                source_location_id=UUID(values.get("source_location_id", "")),
                target_location_id=UUID(values.get("target_location_id", "")),
                quantity=values.get("quantity", ""),
            )
        elif mode == "adjustment":
            adjustment_mode = values.get("adjustment_mode", "target")
            result = inventory.adjust(
                **common,
                location_id=UUID(values.get("location_id", "")),
                difference=(
                    values.get("difference", "")
                    if adjustment_mode == "difference"
                    else None
                ),
                target_quantity=(
                    values.get("target_quantity", "")
                    if adjustment_mode == "target"
                    else None
                ),
            )
        else:
            method = {
                "stock-in": inventory.stock_in,
                "stock-out": inventory.stock_out,
                "initial": inventory.initial,
            }[mode]
            result = method(
                **common,
                location_id=UUID(values.get("location_id", "")),
                quantity=values.get("quantity", ""),
            )
    except (DomainError, ValueError) as error:
        message = (
            error.message if isinstance(error, DomainError) else "Ungültige Auswahl."
        )
        return _render(
            request,
            "inventory/form.html",
            _context(request, mode, values=values, error=message),
            status_code=(
                422 if isinstance(error, (ValidationError, ValueError)) else 409
            ),
        )
    return _render(
        request,
        "inventory/form.html",
        _context(request, mode, values=values, result=result),
        status_code=200,
    )


@router.post("/inventory/stock-in", response_class=HTMLResponse)
async def stock_in(request: Request) -> HTMLResponse:
    return await _book("stock-in", request)


@router.post("/inventory/stock-out", response_class=HTMLResponse)
async def stock_out(request: Request) -> HTMLResponse:
    return await _book("stock-out", request)


@router.post("/inventory/initial", response_class=HTMLResponse)
async def initial(request: Request) -> HTMLResponse:
    return await _book("initial", request)


@router.post("/inventory/transfer", response_class=HTMLResponse)
async def transfer(request: Request) -> HTMLResponse:
    return await _book("transfer", request)


@router.post("/inventory/adjustment", response_class=HTMLResponse)
async def adjustment(request: Request) -> HTMLResponse:
    return await _book("adjustment", request)
