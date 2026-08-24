"""M4 neutral supplier endpoints backed by the Mouser adapter."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request

from ebauteilefuchs.api.dependencies import get_supplier_search_service
from ebauteilefuchs.api.schemas.suppliers import (
    LocalArticleResponse,
    SupplierAttributeResponse,
    SupplierImportRequest,
    SupplierImportResponse,
    SupplierProductResponse,
    SupplierSearchRequest,
    SupplierSearchResponse,
)
from ebauteilefuchs.application.supplier_search import SupplierSearchService
from ebauteilefuchs.domain.articles import ArticleDraft, AttributeInput
from ebauteilefuchs.domain.errors import ValidationError

router = APIRouter(prefix="/suppliers/mouser", tags=["suppliers"])
Service = Annotated[SupplierSearchService, Depends(get_supplier_search_service)]


@router.get("/status")
def status(service: Service) -> dict[str, bool | str]:
    return {
        "configured": service.configured,
        "cache_enabled": False,
        "cache_reason": "Durch die veröffentlichten Mouser-API-Bedingungen deaktiviert.",
    }


@router.delete("/cache")
def clear_cache(request: Request) -> dict[str, int]:
    return {"deleted": request.app.state.supplier_cache.clear()}


@router.post("/search", response_model=SupplierSearchResponse)
def search(payload: SupplierSearchRequest, service: Service) -> SupplierSearchResponse:
    result = service.search(
        payload.query, payload.mode, force_external=payload.force_external
    )
    return SupplierSearchResponse(
        query=result.query,
        mode=result.mode,
        external_searched=result.external_searched,
        local_matches=[
            LocalArticleResponse(
                id=item.article.id,
                name=item.article.name,
                manufacturer=item.manufacturer.name if item.manufacturer else None,
                manufacturer_part_number=item.article.manufacturer_part_number,
            )
            for item in result.local_matches
        ],
        external_matches=[_product(item) for item in result.external_matches],
    )


@router.post("/import", response_model=SupplierImportResponse)
def import_product(
    payload: SupplierImportRequest,
    service: Service,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> SupplierImportResponse:
    if not 8 <= len(idempotency_key.strip()) <= 128:
        raise ValidationError(
            "Der Import-Schlüssel muss zwischen 8 und 128 Zeichen lang sein."
        )
    draft = ArticleDraft(
        name=payload.name,
        category_id=payload.category_id,
        manufacturer_name=payload.manufacturer_name,
        manufacturer_part_number=payload.manufacturer_part_number,
        description=payload.description,
        datasheet_url=payload.datasheet_url,
        product_url=payload.product_url,
        attributes=tuple(
            AttributeInput(
                definition_id=item.definition_id,
                custom_name=item.custom_name,
                raw_value=item.raw_value,
                unit=item.unit,
            )
            for item in payload.attributes
        ),
        acknowledge_similar=payload.acknowledge_similar,
    )
    article = service.import_article(
        draft,
        mouser_part_number=payload.mouser_part_number,
        product_url=payload.product_url,
        existing_article_id=payload.existing_article_id,
    )
    return SupplierImportResponse(article_id=article.article.id)


def _product(item) -> SupplierProductResponse:
    return SupplierProductResponse(
        supplier_part_number=item.supplier_part_number,
        manufacturer=item.manufacturer,
        manufacturer_part_number=item.manufacturer_part_number,
        name=item.name,
        description=item.description,
        category_name=item.category_name,
        suggested_category_code=item.suggested_category_code,
        datasheet_url=item.datasheet_url,
        product_url=item.product_url,
        image_url=item.image_url,
        availability=item.availability,
        attributes=[
            SupplierAttributeResponse(
                original_name=value.original_name,
                original_value=value.original_value,
                definition_code=value.definition_code,
                value=value.value,
                unit=value.unit,
                normalized=value.normalized,
            )
            for value in item.attributes
        ],
    )
