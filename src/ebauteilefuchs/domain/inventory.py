"""Framework-independent inventory journal rules and value objects."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from uuid import UUID

from ebauteilefuchs.domain.errors import ValidationError

MAX_QUANTITY = Decimal("9999999999999999.99999999")
QUANTITY_SCALE = Decimal("0.00000001")
DEFAULT_UNIT = "Stück"


class TransactionType(StrEnum):
    STOCK_IN = "stock_in"
    STOCK_OUT = "stock_out"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    INITIAL = "initial"


@dataclass(frozen=True, slots=True)
class InventoryBalance:
    id: UUID
    article_id: UUID
    location_id: UUID
    quantity: Decimal
    unit: str
    updated_at: datetime
    version: int


@dataclass(frozen=True, slots=True)
class InventoryTransaction:
    id: UUID
    transaction_type: TransactionType
    idempotency_key: str
    request_fingerprint: str
    comment: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class InventoryMovement:
    id: UUID
    transaction_id: UUID
    article_id: UUID
    location_id: UUID
    quantity_delta: Decimal
    unit: str
    balance_after: Decimal
    created_at: datetime


@dataclass(frozen=True, slots=True)
class StockPosition:
    balance: InventoryBalance
    article_name: str
    location_code: str
    location_name: str
    location_path: str


@dataclass(frozen=True, slots=True)
class MovementDetails:
    movement: InventoryMovement
    transaction_type: TransactionType
    transaction_comment: str | None
    article_name: str
    location_code: str
    location_path: str


@dataclass(frozen=True, slots=True)
class BookingResult:
    transaction: InventoryTransaction
    movements: tuple[InventoryMovement, ...]
    repeated: bool = False


def parse_quantity(value: Decimal | str | int, field: str = "Menge") -> Decimal:
    """Parse a bounded decimal without rounding or binary floats."""

    if isinstance(value, float):
        raise ValidationError(f"{field} muss als Dezimalzahl eingegeben werden.")
    try:
        quantity = Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        raise ValidationError(f"{field} ist keine gültige Zahl.") from None
    if not quantity.is_finite():
        raise ValidationError(f"{field} ist keine gültige endliche Zahl.")
    if abs(quantity) > MAX_QUANTITY:
        raise ValidationError(f"{field} ist zu groß.")
    if quantity.as_tuple().exponent < -8:
        raise ValidationError(f"{field} darf höchstens 8 Nachkommastellen haben.")
    return quantity.quantize(QUANTITY_SCALE).normalize()


def positive_quantity(value: Decimal | str | int, field: str = "Menge") -> Decimal:
    quantity = parse_quantity(value, field)
    if quantity <= 0:
        raise ValidationError(f"{field} muss größer als null sein.")
    return quantity


def clean_unit(value: str | None) -> str:
    unit = " ".join((value or DEFAULT_UNIT).split())
    if not unit or len(unit) > 24:
        raise ValidationError("Die Mengeneinheit muss 1 bis 24 Zeichen lang sein.")
    return unit


def clean_idempotency_key(value: str) -> str:
    key = value.strip()
    if not 8 <= len(key) <= 128:
        raise ValidationError(
            "Der Buchungsschlüssel muss zwischen 8 und 128 Zeichen lang sein."
        )
    if any(ord(character) < 33 or ord(character) > 126 for character in key):
        raise ValidationError(
            "Der Buchungsschlüssel darf nur druckbare ASCII-Zeichen enthalten."
        )
    return key
