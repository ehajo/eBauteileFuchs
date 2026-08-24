"""Versioned M3 REST resources for inventory balances and bookings."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status

from ebauteilefuchs.api.dependencies import get_inventory_service
from ebauteilefuchs.api.schemas.inventory import (
    InventoryAdjustmentRequest,
    InventoryBookingRequest,
    InventoryBookingResponse,
    InventoryJournalResponse,
    InventoryMovementResponse,
    InventoryPositionResponse,
    InventoryTransferRequest,
)
from ebauteilefuchs.application.inventory import InventoryService
from ebauteilefuchs.domain.inventory import (
    BookingResult,
    MovementDetails,
    StockPosition,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])
InventoryServiceDependency = Annotated[InventoryService, Depends(get_inventory_service)]
IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=128,
        description="Eindeutiger Schlüssel für genau diesen Buchungsversuch.",
    ),
]


def _movement(value) -> InventoryMovementResponse:
    return InventoryMovementResponse(
        id=value.id,
        transaction_id=value.transaction_id,
        article_id=value.article_id,
        location_id=value.location_id,
        quantity_delta=value.quantity_delta,
        unit=value.unit,
        balance_after=value.balance_after,
        created_at=value.created_at,
    )


def _booking(value: BookingResult) -> InventoryBookingResponse:
    return InventoryBookingResponse(
        transaction_id=value.transaction.id,
        transaction_type=value.transaction.transaction_type.value,
        idempotency_key=value.transaction.idempotency_key,
        repeated=value.repeated,
        movements=[_movement(item) for item in value.movements],
    )


def _position(value: StockPosition) -> InventoryPositionResponse:
    return InventoryPositionResponse(
        article_id=value.balance.article_id,
        article_name=value.article_name,
        location_id=value.balance.location_id,
        location_code=value.location_code,
        location_name=value.location_name,
        location_path=value.location_path,
        quantity=value.balance.quantity,
        unit=value.balance.unit,
        version=value.balance.version,
        updated_at=value.balance.updated_at,
    )


def _journal(value: MovementDetails) -> InventoryJournalResponse:
    return InventoryJournalResponse(
        movement=_movement(value.movement),
        transaction_type=value.transaction_type.value,
        comment=value.transaction_comment,
        article_name=value.article_name,
        location_code=value.location_code,
        location_path=value.location_path,
    )


@router.get("", response_model=list[InventoryPositionResponse])
def list_inventory(
    service: InventoryServiceDependency,
    article_id: UUID | None = None,
    location_id: UUID | None = None,
    include_zero: bool = False,
) -> list[InventoryPositionResponse]:
    return [
        _position(item)
        for item in service.list_positions(
            article_id=article_id,
            location_id=location_id,
            include_zero=include_zero,
        )
    ]


@router.get("/transactions", response_model=list[InventoryJournalResponse])
def list_transactions(
    service: InventoryServiceDependency,
    article_id: UUID | None = None,
    location_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=250)] = 25,
) -> list[InventoryJournalResponse]:
    return [
        _journal(item)
        for item in service.list_movements(
            article_id=article_id, location_id=location_id, limit=limit
        )
    ]


def _single_booking(service, key, payload, method) -> InventoryBookingResponse:
    return _booking(
        method(
            article_id=payload.article_id,
            location_id=payload.location_id,
            quantity=payload.quantity,
            idempotency_key=key,
            unit=payload.unit,
            comment=payload.comment,
        )
    )


@router.post(
    "/initial",
    response_model=InventoryBookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def initial_stock(
    payload: InventoryBookingRequest,
    service: InventoryServiceDependency,
    idempotency_key: IdempotencyKey,
) -> InventoryBookingResponse:
    return _single_booking(service, idempotency_key, payload, service.initial)


@router.post(
    "/stock-in",
    response_model=InventoryBookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def stock_in(
    payload: InventoryBookingRequest,
    service: InventoryServiceDependency,
    idempotency_key: IdempotencyKey,
) -> InventoryBookingResponse:
    return _single_booking(service, idempotency_key, payload, service.stock_in)


@router.post(
    "/stock-out",
    response_model=InventoryBookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def stock_out(
    payload: InventoryBookingRequest,
    service: InventoryServiceDependency,
    idempotency_key: IdempotencyKey,
) -> InventoryBookingResponse:
    return _single_booking(service, idempotency_key, payload, service.stock_out)


@router.post(
    "/transfers",
    response_model=InventoryBookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def transfer(
    payload: InventoryTransferRequest,
    service: InventoryServiceDependency,
    idempotency_key: IdempotencyKey,
) -> InventoryBookingResponse:
    return _booking(
        service.transfer(
            article_id=payload.article_id,
            source_location_id=payload.source_location_id,
            target_location_id=payload.target_location_id,
            quantity=payload.quantity,
            idempotency_key=idempotency_key,
            unit=payload.unit,
            comment=payload.comment,
        )
    )


@router.post(
    "/adjustments",
    response_model=InventoryBookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def adjustment(
    payload: InventoryAdjustmentRequest,
    service: InventoryServiceDependency,
    idempotency_key: IdempotencyKey,
) -> InventoryBookingResponse:
    return _booking(
        service.adjust(
            article_id=payload.article_id,
            location_id=payload.location_id,
            difference=payload.difference,
            target_quantity=payload.target_quantity,
            idempotency_key=idempotency_key,
            unit=payload.unit,
            comment=payload.comment,
        )
    )
