"""Map Mouser-specific products into the neutral supplier model."""

from ebauteilefuchs.domain.articles import validate_optional_url
from ebauteilefuchs.domain.errors import ValidationError
from ebauteilefuchs.domain.suppliers import (
    SupplierAttribute,
    SupplierProduct,
    map_attribute_code,
    normalize_engineering_value,
    suggest_category,
)
from ebauteilefuchs.suppliers.mouser.schemas import MouserPart


def map_part(part: MouserPart) -> SupplierProduct:
    attributes = []
    package = None
    for item in part.attributes:
        code = map_attribute_code(item.name)
        value, unit, normalized = normalize_engineering_value(item.value)
        if code == "package":
            package = item.value
        attributes.append(
            SupplierAttribute(
                original_name=item.name,
                original_value=item.value,
                definition_code=code,
                value=value,
                unit=unit,
                normalized=normalized,
            )
        )
    category_code = suggest_category(part.category, part.description, package)
    return SupplierProduct(
        supplier_code="mouser",
        supplier_part_number=part.mouser_part_number,
        manufacturer=part.manufacturer,
        manufacturer_part_number=part.manufacturer_part_number,
        name=part.description
        or part.manufacturer_part_number
        or part.mouser_part_number,
        description=part.description,
        category_name=part.category,
        suggested_category_code=category_code,
        datasheet_url=_safe_url(part.datasheet_url, "Datenblatt-Link"),
        product_url=_safe_url(part.product_url, "Produkt-Link"),
        image_url=_safe_url(part.image_url, "Produktbild"),
        availability=part.availability,
        attributes=tuple(attributes),
    )


def _safe_url(value: str | None, label: str) -> str | None:
    try:
        return validate_optional_url(value, label)
    except ValidationError:
        return None
