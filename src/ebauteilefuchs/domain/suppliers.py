"""Neutral supplier products and deterministic engineering-value mapping."""

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum


class SupplierSearchMode(StrEnum):
    PART_NUMBER = "part_number"
    MANUFACTURER_PART_NUMBER = "manufacturer_part_number"
    KEYWORD = "keyword"
    BARCODE = "barcode"


@dataclass(frozen=True, slots=True)
class SupplierAttribute:
    original_name: str
    original_value: str
    definition_code: str | None = None
    value: str | None = None
    unit: str | None = None
    normalized: bool = False


@dataclass(frozen=True, slots=True)
class SupplierProduct:
    supplier_code: str
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
    attributes: tuple[SupplierAttribute, ...]


ATTRIBUTE_CODES = {
    "resistance": ("resistance", "widerstand"),
    "capacitance": ("capacitance", "kapazitat"),
    "inductance": ("inductance", "induktivitat"),
    "rated_voltage": ("voltage rating", "rated voltage", "nennspannung"),
    "current": ("current", "strom"),
    "power": ("power", "leistung"),
    "tolerance": ("tolerance", "toleranz"),
    "package": ("package", "case code", "gehause", "bauform"),
    "temperature_coefficient": ("temperature coefficient", "temperaturkoeffizient"),
}

UNIT_ALIASES = {
    "ohm": "Ω",
    "ohms": "Ω",
    "ω": "Ω",
    "kohm": "kΩ",
    "kohms": "kΩ",
    "mohm": "MΩ",
    "farad": "F",
    "farads": "F",
    "uf": "µF",
    "μf": "µF",
    "µf": "µF",
    "nf": "nF",
    "pf": "pF",
    "mf": "mF",
    "volt": "V",
    "volts": "V",
    "amp": "A",
    "amps": "A",
    "watt": "W",
    "watts": "W",
    "mw": "mW",
    "uw": "µW",
    "μw": "µW",
    "µw": "µW",
    "hz": "Hz",
    "khz": "kHz",
    "mhz": "MHz",
    "ghz": "GHz",
    "c": "°C",
    "°c": "°C",
    "mm": "mm",
    "cm": "cm",
    "um": "µm",
    "μm": "µm",
    "µm": "µm",
}


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    return " ".join(
        "".join(c for c in normalized if not unicodedata.combining(c)).split()
    )


def map_attribute_code(name: str) -> str | None:
    candidate = _plain(name)
    for code, aliases in ATTRIBUTE_CODES.items():
        if any(alias in candidate for alias in aliases):
            return code
    return None


def normalize_engineering_value(raw: str) -> tuple[str, str | None, bool]:
    """Normalize an unambiguous number/unit while retaining the original separately."""

    match = re.fullmatch(
        r"\s*([+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+))\s*([^\d\s]+(?:\s*/\s*[^\d\s]+)?)?\s*",
        raw,
    )
    if not match:
        return raw.strip(), None, False
    try:
        number = Decimal(match.group(1).replace(",", "."))
    except InvalidOperation:
        return raw.strip(), None, False
    raw_unit = (match.group(2) or "").replace(" ", "")
    if raw_unit in {"mOhm", "mOhms", "mΩ"}:
        unit = "mΩ"
    elif raw_unit in {"MOhm", "MOhms", "MΩ"}:
        unit = "MΩ"
    else:
        unit = UNIT_ALIASES.get(raw_unit.casefold(), raw_unit or None)
    if unit == "Ω" and number != 0 and number % Decimal("1000") == 0:
        scaled = number / Decimal("1000")
        return _decimal_text(scaled), "kΩ", True
    if unit == "µF":
        scaled = number * Decimal("1000")
        if scaled == scaled.to_integral_value():
            return _decimal_text(scaled), "nF", True
    return _decimal_text(number), unit, bool(unit)


def _decimal_text(value: Decimal) -> str:
    rendered = format(value, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def suggest_category(*values: str | None) -> str:
    text = _plain(" ".join(value or "" for value in values))
    rules = (
        ("resistor", ("resistor", "widerstand")),
        ("capacitor", ("capacitor", "kondensator")),
        ("inductor", ("inductor", "induktivitat", "drossel")),
        ("diode", ("diode",)),
        ("led", (" led", "light emitting")),
        ("transistor_mosfet", ("transistor", "mosfet")),
        ("integrated_circuit", ("integrated circuit", "microcontroller", " ic ")),
        ("connector", ("connector", "steckverbinder")),
    )
    for code, needles in rules:
        if any(needle in f" {text} " for needle in needles):
            return code
    return "other"
