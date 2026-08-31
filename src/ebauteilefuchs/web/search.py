from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ebauteilefuchs.application.location_selection import build_location_scopes
from ebauteilefuchs.domain.errors import DomainError
from ebauteilefuchs.web.locations import _render

router = APIRouter(include_in_schema=False)


def _optional_uuid(value: str) -> UUID | None:
    return UUID(value) if value else None


@router.get("/search", response_class=HTMLResponse)
def search_page(request: Request) -> HTMLResponse:
    query = request.query_params.get("q", "")
    category_id = request.query_params.get("category_id", "")
    location_scope_id = request.query_params.get("location_scope_id", "")
    with_stock = request.query_params.get("with_stock") == "1"
    result = None
    error = None
    try:
        if query or category_id or location_scope_id or with_stock:
            result = request.app.state.global_search_service_factory().search(
                query,
                category_id=_optional_uuid(category_id),
                with_stock=with_stock,
                location_scope_id=_optional_uuid(location_scope_id),
            )
    except (ValueError, DomainError) as caught:
        error = (
            caught.message
            if isinstance(caught, DomainError)
            else "Ein gewählter Filter ist ungültig."
        )
    articles = request.app.state.article_service_factory()
    locations = request.app.state.location_service_factory()
    return _render(
        request,
        "search/index.html",
        {
            "query": query,
            "category_id": category_id,
            "location_scope_id": location_scope_id,
            "with_stock": with_stock,
            "categories": articles.list_categories(),
            "locations": build_location_scopes(
                locations.list_details(include_inactive=False)
            ),
            "result": result,
            "error": error,
        },
    )
