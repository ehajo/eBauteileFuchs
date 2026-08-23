"""Versioned M2 REST resources for the article catalog."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ebauteilefuchs.api.dependencies import get_article_service
from ebauteilefuchs.api.schemas.articles import (
    ArticleAttributeResponse,
    ArticleResponse,
    ArticleWriteRequest,
    AttributeDefinitionResponse,
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
    DuplicateCandidateResponse,
    DuplicateCheckResponse,
    ManufacturerCreateRequest,
    ManufacturerResponse,
    ManufacturerUpdateRequest,
    SupplierPartResponse,
    SupplierResponse,
)
from ebauteilefuchs.application.articles import ArticleDetails, ArticleService
from ebauteilefuchs.domain.articles import (
    ArticleDraft,
    AttributeInput,
    Category,
    Manufacturer,
    SupplierPartInput,
)

router = APIRouter(tags=["articles"])
ArticleServiceDependency = Annotated[ArticleService, Depends(get_article_service)]


def _manufacturer_response(value: Manufacturer) -> ManufacturerResponse:
    return ManufacturerResponse(
        id=value.id,
        name=value.name,
        normalized_name=value.normalized_name,
        is_active=value.is_active,
    )


def _category_response(value: Category) -> CategoryResponse:
    return CategoryResponse(
        id=value.id,
        code=value.code,
        name=value.name,
        description=value.description,
        is_system=value.is_system,
        is_active=value.is_active,
        sort_order=value.sort_order,
    )


def _article_response(details: ArticleDetails) -> ArticleResponse:
    article = details.article
    return ArticleResponse(
        id=article.id,
        name=article.name,
        manufacturer=(
            _manufacturer_response(details.manufacturer)
            if details.manufacturer
            else None
        ),
        manufacturer_part_number=article.manufacturer_part_number,
        normalized_manufacturer_part_number=article.normalized_manufacturer_part_number,
        category=_category_response(details.category),
        description=article.description,
        datasheet_url=article.datasheet_url,
        product_url=article.product_url,
        note=article.note,
        is_active=article.is_active,
        attributes=[
            ArticleAttributeResponse(
                id=value.id,
                definition_id=value.attribute_definition_id,
                name=value.definition_name or value.custom_name or "Eigenschaft",
                raw_value=value.raw_value,
                normalized_text=value.normalized_text,
                numeric_value=value.numeric_value,
                unit=value.unit,
            )
            for value in details.attributes
        ],
        supplier_parts=[
            SupplierPartResponse(
                id=value.id,
                supplier_id=value.supplier_id,
                supplier_name=value.supplier_name or "Lieferant",
                supplier_part_number=value.supplier_part_number,
                normalized_supplier_part_number=value.normalized_supplier_part_number,
                product_url=value.product_url,
            )
            for value in details.supplier_parts
        ],
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


def _draft(payload: ArticleWriteRequest) -> ArticleDraft:
    return ArticleDraft(
        name=payload.name,
        category_id=payload.category_id,
        manufacturer_name=payload.manufacturer_name,
        manufacturer_part_number=payload.manufacturer_part_number,
        description=payload.description,
        datasheet_url=payload.datasheet_url,
        product_url=payload.product_url,
        note=payload.note,
        attributes=tuple(
            AttributeInput(
                definition_id=value.definition_id,
                custom_name=value.custom_name,
                raw_value=value.raw_value,
                unit=value.unit,
            )
            for value in payload.attributes
        ),
        supplier_parts=tuple(
            SupplierPartInput(
                supplier_id=value.supplier_id,
                supplier_part_number=value.supplier_part_number,
                product_url=value.product_url,
            )
            for value in payload.supplier_parts
        ),
        acknowledge_similar=payload.acknowledge_similar,
    )


@router.get("/manufacturers", response_model=list[ManufacturerResponse])
def list_manufacturers(
    service: ArticleServiceDependency, include_inactive: bool = False
) -> list[ManufacturerResponse]:
    return [
        _manufacturer_response(item)
        for item in service.list_manufacturers(include_inactive=include_inactive)
    ]


@router.post(
    "/manufacturers",
    response_model=ManufacturerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_manufacturer(
    payload: ManufacturerCreateRequest, service: ArticleServiceDependency
) -> ManufacturerResponse:
    return _manufacturer_response(service.create_manufacturer(payload.name))


@router.put("/manufacturers/{manufacturer_id}", response_model=ManufacturerResponse)
def update_manufacturer(
    manufacturer_id: UUID,
    payload: ManufacturerUpdateRequest,
    service: ArticleServiceDependency,
) -> ManufacturerResponse:
    return _manufacturer_response(
        service.update_manufacturer(
            manufacturer_id, name=payload.name, is_active=payload.is_active
        )
    )


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(
    service: ArticleServiceDependency, include_inactive: bool = False
) -> list[CategoryResponse]:
    return [
        _category_response(item)
        for item in service.list_categories(include_inactive=include_inactive)
    ]


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: CategoryCreateRequest, service: ArticleServiceDependency
) -> CategoryResponse:
    return _category_response(
        service.create_category(
            code=payload.code,
            name=payload.name,
            description=payload.description,
            sort_order=payload.sort_order,
        )
    )


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    payload: CategoryUpdateRequest,
    service: ArticleServiceDependency,
) -> CategoryResponse:
    return _category_response(
        service.update_category(
            category_id,
            name=payload.name,
            description=payload.description,
            sort_order=payload.sort_order,
            is_active=payload.is_active,
        )
    )


@router.get(
    "/categories/{category_id}/attributes",
    response_model=list[AttributeDefinitionResponse],
)
def category_attributes(
    category_id: UUID, service: ArticleServiceDependency
) -> list[AttributeDefinitionResponse]:
    return [
        AttributeDefinitionResponse(
            id=value.definition.id,
            code=value.definition.code,
            name=value.definition.name,
            value_kind=value.definition.value_kind,
            canonical_unit=value.definition.canonical_unit,
            allowed_units=list(value.allowed_units),
        )
        for value in service.list_category_attributes(category_id)
    ]


@router.get("/suppliers", response_model=list[SupplierResponse])
def list_suppliers(service: ArticleServiceDependency) -> list[SupplierResponse]:
    return [
        SupplierResponse(
            id=item.id, code=item.code, name=item.name, is_active=item.is_active
        )
        for item in service.list_suppliers()
    ]


@router.get("/articles", response_model=list[ArticleResponse])
def list_articles(
    service: ArticleServiceDependency,
    q: Annotated[str | None, Query(max_length=200)] = None,
    include_inactive: bool = True,
) -> list[ArticleResponse]:
    return [
        _article_response(item)
        for item in service.list_articles(query=q, include_inactive=include_inactive)
    ]


@router.post(
    "/articles",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_article(
    payload: ArticleWriteRequest, service: ArticleServiceDependency
) -> ArticleResponse:
    return _article_response(service.create(_draft(payload)))


@router.post("/articles/duplicates", response_model=DuplicateCheckResponse)
def check_duplicates(
    payload: ArticleWriteRequest,
    service: ArticleServiceDependency,
) -> DuplicateCheckResponse:
    return DuplicateCheckResponse(
        candidates=[
            DuplicateCandidateResponse(
                article_id=value.article_id,
                name=value.name,
                match_level=value.match_level,
                reason=value.reason,
                can_override=value.can_override,
            )
            for value in service.check_duplicates(_draft(payload))
        ]
    )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
def get_article(article_id: UUID, service: ArticleServiceDependency) -> ArticleResponse:
    return _article_response(service.get(article_id))


@router.put("/articles/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: UUID,
    payload: ArticleWriteRequest,
    service: ArticleServiceDependency,
) -> ArticleResponse:
    return _article_response(
        service.update(article_id, _draft(payload), is_active=payload.is_active)
    )
