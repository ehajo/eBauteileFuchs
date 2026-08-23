"""Article catalog entities, validation, and deterministic normalization."""

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from ebauteilefuchs.domain.errors import ValidationError

SPACE = re.compile(r"\s+")
SEARCH_TOKEN = re.compile(r"[^\w]+", flags=re.UNICODE)
ValueKind = Literal["text", "decimal", "integer", "boolean"]


def clean_text(
    value: str | None,
    field_name: str,
    max_length: int,
    *,
    required: bool = False,
) -> str | None:
    cleaned = SPACE.sub(" ", unicodedata.normalize("NFKC", value or "").strip())
    if required and not cleaned:
        raise ValidationError(f"{field_name} darf nicht leer sein.")
    if len(cleaned) > max_length:
        raise ValidationError(
            f"{field_name} darf höchstens {max_length} Zeichen enthalten."
        )
    return cleaned or None


def normalize_manufacturer_name(value: str) -> str:
    return SPACE.sub(" ", unicodedata.normalize("NFKC", value).strip()).casefold()


def normalize_part_number(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).upper().strip()
    return "".join(character for character in normalized if character.isalnum())


def normalize_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(token for token in SEARCH_TOKEN.split(normalized) if token)


def validate_optional_url(value: str | None, field_name: str) -> str | None:
    cleaned = clean_text(value, field_name, 500)
    if cleaned is None:
        return None
    parsed = urlsplit(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(
            f"{field_name} muss eine vollständige HTTP- oder HTTPS-Adresse sein."
        )
    if parsed.username or parsed.password:
        raise ValidationError(f"{field_name} darf keine Zugangsdaten enthalten.")
    return cleaned


def normalized_numeric_value(raw_value: str, value_kind: ValueKind) -> Decimal | None:
    if value_kind not in {"decimal", "integer"}:
        return None
    candidate = raw_value.strip().replace(",", ".")
    try:
        value = Decimal(candidate)
    except InvalidOperation:
        return None
    if value_kind == "integer" and value != value.to_integral_value():
        return None
    return value


@dataclass(frozen=True, slots=True)
class Manufacturer:
    id: UUID
    name: str
    normalized_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Category:
    id: UUID
    code: str
    name: str
    description: str | None
    is_system: bool
    is_active: bool
    sort_order: int


@dataclass(frozen=True, slots=True)
class Supplier:
    id: UUID
    code: str
    name: str
    adapter_name: str | None
    is_system: bool
    is_active: bool


@dataclass(frozen=True, slots=True)
class AttributeDefinition:
    id: UUID
    code: str
    name: str
    value_kind: ValueKind
    canonical_unit: str | None
    is_system: bool
    is_active: bool


@dataclass(frozen=True, slots=True)
class CategoryAttribute:
    category_id: UUID
    definition: AttributeDefinition
    sort_order: int
    is_typical: bool
    allowed_units: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArticleAttribute:
    id: UUID
    article_id: UUID
    attribute_definition_id: UUID | None
    custom_name: str | None
    raw_value: str
    normalized_text: str
    numeric_value: Decimal | None
    unit: str | None
    canonical_numeric_value: Decimal | None
    canonical_unit: str | None
    sort_order: int
    definition_name: str | None = None


@dataclass(frozen=True, slots=True)
class SupplierPart:
    id: UUID
    article_id: UUID
    supplier_id: UUID
    supplier_part_number: str
    normalized_supplier_part_number: str
    product_url: str | None
    created_at: datetime
    updated_at: datetime
    supplier_name: str | None = None


@dataclass(frozen=True, slots=True)
class Article:
    id: UUID
    name: str
    manufacturer_id: UUID | None
    manufacturer_part_number: str | None
    normalized_manufacturer_part_number: str | None
    category_id: UUID
    description: str | None
    datasheet_url: str | None
    product_url: str | None
    note: str | None
    search_text: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class AttributeInput:
    raw_value: str
    definition_id: UUID | None = None
    custom_name: str | None = None
    unit: str | None = None


@dataclass(frozen=True, slots=True)
class SupplierPartInput:
    supplier_id: UUID
    supplier_part_number: str
    product_url: str | None = None


@dataclass(frozen=True, slots=True)
class ArticleDraft:
    name: str
    category_id: UUID
    manufacturer_name: str | None = None
    manufacturer_part_number: str | None = None
    description: str | None = None
    datasheet_url: str | None = None
    product_url: str | None = None
    note: str | None = None
    attributes: tuple[AttributeInput, ...] = ()
    supplier_parts: tuple[SupplierPartInput, ...] = ()
    acknowledge_similar: bool = False
