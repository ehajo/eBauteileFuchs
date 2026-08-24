"""Defensive response models for the subset of Mouser Search API used by M4."""

from dataclasses import dataclass
from typing import Any

from ebauteilefuchs.domain.errors import SupplierResponseError


@dataclass(frozen=True, slots=True)
class MouserAttribute:
    name: str
    value: str


@dataclass(frozen=True, slots=True)
class MouserPart:
    mouser_part_number: str
    manufacturer_part_number: str | None
    manufacturer: str | None
    description: str | None
    category: str | None
    datasheet_url: str | None
    product_url: str | None
    image_url: str | None
    availability: str | None
    attributes: tuple[MouserAttribute, ...]


def parse_search_response(payload: Any) -> tuple[MouserPart, ...]:
    if not isinstance(payload, dict):
        raise SupplierResponseError("Mouser hat eine unerwartete Antwort geliefert.")
    errors = payload.get("Errors")
    if isinstance(errors, list) and errors:
        message = errors[0].get("Message") if isinstance(errors[0], dict) else None
        raise SupplierResponseError(
            f"Mouser meldet einen Fehler: {message or 'Anfrage abgelehnt.'}"
        )
    results = payload.get("SearchResults")
    if not isinstance(results, dict):
        raise SupplierResponseError("Die Mouser-Antwort enthält keine Suchergebnisse.")
    parts = results.get("Parts") or []
    if not isinstance(parts, list):
        raise SupplierResponseError("Die Mouser-Trefferliste ist ungültig.")
    if len(parts) > 50:
        raise SupplierResponseError(
            "Die Mouser-Antwort enthält unerwartet viele Treffer."
        )
    return tuple(_parse_part(item) for item in parts if isinstance(item, dict))


def _text(item: dict, key: str) -> str | None:
    value = item.get(key)
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


def _parse_part(item: dict) -> MouserPart:
    number = _text(item, "MouserPartNumber")
    if not number:
        raise SupplierResponseError("Ein Mouser-Treffer besitzt keine Artikelnummer.")
    raw_attributes = item.get("ProductAttributes") or []
    attributes = tuple(
        MouserAttribute(name=name, value=value)
        for raw in raw_attributes
        if isinstance(raw, dict)
        if (name := _text(raw, "AttributeName"))
        if (value := _text(raw, "AttributeValue"))
    )
    return MouserPart(
        mouser_part_number=number,
        manufacturer_part_number=_text(item, "ManufacturerPartNumber"),
        manufacturer=_text(item, "Manufacturer"),
        description=_text(item, "Description"),
        category=_text(item, "Category"),
        datasheet_url=_text(item, "DataSheetUrl"),
        product_url=_text(item, "ProductDetailUrl"),
        image_url=_text(item, "ImagePath"),
        availability=_text(item, "Availability"),
        attributes=attributes,
    )
