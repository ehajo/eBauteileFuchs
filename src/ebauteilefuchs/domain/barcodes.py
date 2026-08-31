"""Deterministic interpretation of packaging barcode data identifiers."""

import re
from dataclasses import dataclass

_DISPLAYED_SEPARATOR = re.compile(r"<(?:GS|RS|EOT)>", re.IGNORECASE)
_CONTROL_SEPARATOR = re.compile(r"[\x04\x1c-\x1f]+")


@dataclass(frozen=True, slots=True)
class PackagingBarcode:
    product_codes: tuple[str, ...] = ()
    lot_numbers: tuple[str, ...] = ()
    quantities: tuple[str, ...] = ()

    @property
    def recognized(self) -> bool:
        return bool(self.product_codes or self.lot_numbers or self.quantities)


def parse_packaging_barcode(value: str) -> PackagingBarcode:
    """Parse Würth-style 1P/1T/Q data identifiers without guessing values."""

    expanded = _DISPLAYED_SEPARATOR.sub("\x1d", value.strip())
    product_codes: list[str] = []
    lot_numbers: list[str] = []
    quantities: list[str] = []
    for raw_segment in _CONTROL_SEPARATOR.split(expanded):
        segment = raw_segment.strip()
        if segment.startswith("]d2"):
            segment = segment[3:].strip()
        if segment.startswith("[)>"):
            segment = segment[3:].strip()
        if segment in {"05", "06"}:
            continue
        upper = segment.upper()
        if upper.startswith("1P") and segment[2:].strip():
            product_codes.append(segment[2:].strip())
        elif upper.startswith("1T") and segment[2:].strip():
            lot_numbers.append(segment[2:].strip())
        elif re.fullmatch(r"Q\s*[+-]?\d+(?:[.,]\d+)?", segment, re.IGNORECASE):
            quantities.append(segment[1:].strip())
    return PackagingBarcode(
        product_codes=tuple(dict.fromkeys(product_codes)),
        lot_numbers=tuple(dict.fromkeys(lot_numbers)),
        quantities=tuple(dict.fromkeys(quantities)),
    )
