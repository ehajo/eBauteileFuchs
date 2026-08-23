"""M2 REST schemas for articles and catalog reference data."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ManufacturerResponse(BaseModel):
    id: UUID
    name: str
    normalized_name: str
    is_active: bool


class ManufacturerCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ManufacturerUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    is_active: bool


class CategoryResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    is_system: bool
    is_active: bool
    sort_order: int


class CategoryCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=1_000)
    sort_order: int = Field(default=100, ge=0, le=10_000)


class CategoryUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=1_000)
    sort_order: int = Field(ge=0, le=10_000)
    is_active: bool


class AttributeDefinitionResponse(BaseModel):
    id: UUID
    code: str
    name: str
    value_kind: str
    canonical_unit: str | None
    allowed_units: list[str]


class SupplierResponse(BaseModel):
    id: UUID
    code: str
    name: str
    is_active: bool


class ArticleAttributeRequest(BaseModel):
    definition_id: UUID | None = None
    custom_name: str | None = Field(default=None, max_length=100)
    raw_value: str = Field(max_length=240)
    unit: str | None = Field(default=None, max_length=24)


class SupplierPartRequest(BaseModel):
    supplier_id: UUID
    supplier_part_number: str = Field(min_length=1, max_length=160)
    product_url: str | None = Field(default=None, max_length=500)


class ArticleWriteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category_id: UUID
    manufacturer_name: str | None = Field(default=None, max_length=120)
    manufacturer_part_number: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=4_000)
    datasheet_url: str | None = Field(default=None, max_length=500)
    product_url: str | None = Field(default=None, max_length=500)
    note: str | None = Field(default=None, max_length=4_000)
    attributes: list[ArticleAttributeRequest] = Field(
        default_factory=list, max_length=100
    )
    supplier_parts: list[SupplierPartRequest] = Field(
        default_factory=list, max_length=50
    )
    acknowledge_similar: bool = False
    is_active: bool | None = None


class ArticleAttributeResponse(BaseModel):
    id: UUID
    definition_id: UUID | None
    name: str
    raw_value: str
    normalized_text: str
    numeric_value: Decimal | None
    unit: str | None


class SupplierPartResponse(BaseModel):
    id: UUID
    supplier_id: UUID
    supplier_name: str
    supplier_part_number: str
    normalized_supplier_part_number: str
    product_url: str | None


class ArticleResponse(BaseModel):
    id: UUID
    name: str
    manufacturer: ManufacturerResponse | None
    manufacturer_part_number: str | None
    normalized_manufacturer_part_number: str | None
    category: CategoryResponse
    description: str | None
    datasheet_url: str | None
    product_url: str | None
    note: str | None
    is_active: bool
    attributes: list[ArticleAttributeResponse]
    supplier_parts: list[SupplierPartResponse]
    created_at: datetime
    updated_at: datetime


class DuplicateCandidateResponse(BaseModel):
    article_id: UUID
    name: str
    match_level: int
    reason: str
    can_override: bool


class DuplicateCheckResponse(BaseModel):
    candidates: list[DuplicateCandidateResponse]
