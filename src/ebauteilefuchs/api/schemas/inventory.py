"""Pydantic contracts for the M3 inventory REST API."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class InventoryBookingRequest(BaseModel):
    article_id: UUID
    location_id: UUID
    quantity: Decimal
    unit: str = Field(default="Stück", min_length=1, max_length=24)
    comment: str | None = Field(default=None, max_length=1_000)


class InventoryTransferRequest(BaseModel):
    article_id: UUID
    source_location_id: UUID
    target_location_id: UUID
    quantity: Decimal
    unit: str = Field(default="Stück", min_length=1, max_length=24)
    comment: str | None = Field(default=None, max_length=1_000)


class InventoryAdjustmentRequest(BaseModel):
    article_id: UUID
    location_id: UUID
    difference: Decimal | None = None
    target_quantity: Decimal | None = None
    unit: str = Field(default="Stück", min_length=1, max_length=24)
    comment: str | None = Field(default=None, max_length=1_000)

    @model_validator(mode="after")
    def exactly_one_quantity(self) -> "InventoryAdjustmentRequest":
        if (self.difference is None) == (self.target_quantity is None):
            raise ValueError("difference oder target_quantity muss angegeben werden")
        return self


class InventoryMovementResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    article_id: UUID
    location_id: UUID
    quantity_delta: Decimal
    unit: str
    balance_after: Decimal
    created_at: datetime


class InventoryBookingResponse(BaseModel):
    transaction_id: UUID
    transaction_type: str
    idempotency_key: str
    repeated: bool
    movements: list[InventoryMovementResponse]


class InventoryPositionResponse(BaseModel):
    article_id: UUID
    article_name: str
    location_id: UUID
    location_code: str
    location_name: str
    location_path: str
    quantity: Decimal
    unit: str
    version: int
    updated_at: datetime


class InventoryJournalResponse(BaseModel):
    movement: InventoryMovementResponse
    transaction_type: str
    comment: str | None
    article_name: str
    location_code: str
    location_path: str
