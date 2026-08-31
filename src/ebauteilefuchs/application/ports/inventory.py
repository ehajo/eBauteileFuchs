"""Persistence ports used by the M3 inventory application service."""

from types import TracebackType
from typing import Protocol
from uuid import UUID

from ebauteilefuchs.domain.articles import Article
from ebauteilefuchs.domain.inventory import (
    InventoryBalance,
    InventoryMovement,
    InventoryTransaction,
    MovementDetails,
    StockPosition,
)
from ebauteilefuchs.domain.locations import Location


class InventoryRepository(Protocol):
    def get_article(self, article_id: UUID) -> Article | None: ...
    def get_location(self, location_id: UUID) -> Location | None: ...
    def list_locations(self) -> list[Location]: ...
    def update_location(self, location: Location) -> None: ...
    def update_article(self, article: Article) -> None: ...
    def get_balance(
        self, article_id: UUID, location_id: UUID, unit: str
    ) -> InventoryBalance | None: ...
    def add_balance(self, balance: InventoryBalance) -> None: ...
    def update_balance(
        self, balance: InventoryBalance, *, expected_version: int
    ) -> bool: ...
    def has_movements(self, article_id: UUID, location_id: UUID, unit: str) -> bool: ...
    def get_transaction_by_key(
        self, idempotency_key: str
    ) -> InventoryTransaction | None: ...
    def add_transaction(self, transaction: InventoryTransaction) -> None: ...
    def add_movement(self, movement: InventoryMovement) -> None: ...
    def list_transaction_movements(
        self, transaction_id: UUID
    ) -> list[InventoryMovement]: ...
    def list_positions(
        self,
        *,
        article_id: UUID | None = None,
        location_id: UUID | None = None,
        include_zero: bool = False,
    ) -> list[StockPosition]: ...
    def list_movements(
        self,
        *,
        article_id: UUID | None = None,
        location_id: UUID | None = None,
        limit: int = 25,
    ) -> list[MovementDetails]: ...


class InventoryUnitOfWork(Protocol):
    inventory: InventoryRepository

    def __enter__(self) -> "InventoryUnitOfWork": ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    def begin_write(self) -> None: ...
    def commit(self) -> None: ...


class InventoryUnitOfWorkFactory(Protocol):
    def __call__(self) -> InventoryUnitOfWork: ...
