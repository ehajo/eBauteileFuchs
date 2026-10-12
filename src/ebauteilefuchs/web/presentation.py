"""Small presentation helpers shared by the server-rendered UI."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

UNIT_CHOICES_BY_CANONICAL: dict[str, tuple[str, ...]] = {
    "Ω": ("mΩ", "Ω", "kΩ", "MΩ", "GΩ"),
    "F": ("pF", "nF", "µF", "mF", "F"),
    "H": ("nH", "µH", "mH", "H"),
    "V": ("µV", "mV", "V", "kV"),
    "A": ("nA", "µA", "mA", "A"),
    "W": ("µW", "mW", "W", "kW"),
    "%": ("%",),
    "ppm/K": ("ppm/K",),
    "nm": ("nm", "µm"),
    "mm": ("µm", "mm", "cm", "m"),
}

COMMON_UNIT_CHOICES = tuple(
    dict.fromkeys(
        unit for choices in UNIT_CHOICES_BY_CANONICAL.values() for unit in choices
    )
)


def unit_choices(canonical_unit: str | None) -> tuple[str, ...]:
    """Return practical engineering prefixes for a canonical physical unit."""

    if not canonical_unit:
        return ()
    return UNIT_CHOICES_BY_CANONICAL.get(canonical_unit, (canonical_unit,))


def format_decimal(value: object) -> str:
    """Render a decimal without scientific notation or insignificant zeros."""

    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)
    if not number.is_finite():
        return str(value)
    rendered = format(number, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return "0" if rendered in {"-0", ""} else rendered


def format_local_datetime(value: datetime) -> str:
    """Render a UTC timestamp in the browser host's local timezone."""

    return value.astimezone().strftime("%d.%m.%Y, %H:%M Uhr")
