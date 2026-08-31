from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class SearchAttributeResponse(BaseModel):
    name: str
    value: str
    unit: str | None


class SearchPositionResponse(BaseModel):
    location_id: UUID
    path: str
    quantity: Decimal
    unit: str


class GlobalSearchItemResponse(BaseModel):
    article_id: UUID
    name: str
    manufacturer: str | None
    manufacturer_part_number: str | None
    category_id: UUID
    category: str
    attributes: list[SearchAttributeResponse]
    positions: list[SearchPositionResponse]
    totals: dict[str, Decimal]


class GlobalSearchResponse(BaseModel):
    query: str
    tokens: list[str]
    items: list[GlobalSearchItemResponse]


class ConnectionChoiceResponse(BaseModel):
    label: str
    url: str
    recommended: bool


class ConnectionResponse(BaseModel):
    hostname: str
    local_url: str
    selected_url: str
    choices: list[ConnectionChoiceResponse]
