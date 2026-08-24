"""Neutral M4 supplier search and import API contracts."""

from uuid import UUID

from pydantic import BaseModel, Field

from ebauteilefuchs.domain.suppliers import SupplierSearchMode


class SupplierSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=160)
    mode: SupplierSearchMode = SupplierSearchMode.PART_NUMBER
    force_external: bool = False


class SupplierAttributeResponse(BaseModel):
    original_name: str
    original_value: str
    definition_code: str | None
    value: str | None
    unit: str | None
    normalized: bool


class SupplierProductResponse(BaseModel):
    supplier_part_number: str
    manufacturer: str | None
    manufacturer_part_number: str | None
    name: str
    description: str | None
    category_name: str | None
    suggested_category_code: str
    datasheet_url: str | None
    product_url: str | None
    image_url: str | None
    availability: str | None
    attributes: list[SupplierAttributeResponse]


class LocalArticleResponse(BaseModel):
    id: UUID
    name: str
    manufacturer: str | None
    manufacturer_part_number: str | None


class SupplierSearchResponse(BaseModel):
    query: str
    mode: SupplierSearchMode
    external_searched: bool
    local_matches: list[LocalArticleResponse]
    external_matches: list[SupplierProductResponse]


class SupplierImportAttribute(BaseModel):
    definition_id: UUID | None = None
    custom_name: str | None = Field(default=None, max_length=100)
    raw_value: str = Field(min_length=1, max_length=240)
    unit: str | None = Field(default=None, max_length=24)


class SupplierImportRequest(BaseModel):
    mouser_part_number: str = Field(min_length=1, max_length=160)
    existing_article_id: UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    category_id: UUID
    manufacturer_name: str | None = Field(default=None, max_length=120)
    manufacturer_part_number: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    datasheet_url: str | None = Field(default=None, max_length=500)
    product_url: str | None = Field(default=None, max_length=500)
    attributes: list[SupplierImportAttribute] = Field(
        default_factory=list, max_length=40
    )
    acknowledge_similar: bool = False


class SupplierImportResponse(BaseModel):
    article_id: UUID
    created_or_linked: bool = True
