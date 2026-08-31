from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request

from ebauteilefuchs.api.schemas.search import (
    ConnectionChoiceResponse,
    ConnectionResponse,
    GlobalSearchItemResponse,
    GlobalSearchResponse,
    SearchAttributeResponse,
    SearchPositionResponse,
)
from ebauteilefuchs.application.connection import build_connection_overview
from ebauteilefuchs.application.search import GlobalSearchService
from ebauteilefuchs.platform.network import discover_ipv4_addresses, hostname

router = APIRouter(tags=["search and connection"])


@router.get("/search", response_model=GlobalSearchResponse)
def global_search(
    request: Request,
    q: Annotated[str, Query(max_length=200)] = "",
    category_id: UUID | None = None,
    with_stock: bool = False,
    location_scope_id: UUID | None = None,
) -> GlobalSearchResponse:
    service: GlobalSearchService = request.app.state.global_search_service_factory()
    result = service.search(
        q,
        category_id=category_id,
        with_stock=with_stock,
        location_scope_id=location_scope_id,
    )
    return GlobalSearchResponse(
        query=result.query,
        tokens=list(result.tokens),
        items=[
            GlobalSearchItemResponse(
                article_id=item.details.article.id,
                name=item.details.article.name,
                manufacturer=(
                    item.details.manufacturer.name
                    if item.details.manufacturer
                    else None
                ),
                manufacturer_part_number=(
                    item.details.article.manufacturer_part_number
                ),
                category_id=item.details.category.id,
                category=item.details.category.name,
                attributes=[
                    SearchAttributeResponse(
                        name=value.definition_name
                        or value.custom_name
                        or "Eigenschaft",
                        value=value.raw_value,
                        unit=value.unit,
                    )
                    for value in item.details.attributes
                ],
                positions=[
                    SearchPositionResponse(
                        location_id=value.balance.location_id,
                        path=value.location_path,
                        quantity=value.balance.quantity,
                        unit=value.balance.unit,
                    )
                    for value in item.positions
                ],
                totals=item.totals,
            )
            for item in result.items
        ],
    )


@router.get("/connection", response_model=ConnectionResponse)
def connection_status(request: Request) -> ConnectionResponse:
    settings = request.app.state.settings
    overview = build_connection_overview(
        hostname=hostname(),
        port=request.url.port or settings.port,
        local_url=str(request.base_url).rstrip("/"),
        addresses=discover_ipv4_addresses(),
        configured_url=settings.public_base_url,
    )
    return ConnectionResponse(
        hostname=overview.hostname,
        local_url=overview.local_url,
        selected_url=overview.selected_url,
        choices=[
            ConnectionChoiceResponse(
                label=item.label,
                url=item.url,
                recommended=item.recommended,
            )
            for item in overview.choices
        ],
    )
