"""Ports used by location application services."""

from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from ebauteilefuchs.domain.locations import Location, LocationType


class LocationRepository(Protocol):
    def list_types(self, *, include_inactive: bool = False) -> list[LocationType]: ...

    def get_type(self, location_type_id: UUID) -> LocationType | None: ...

    def get_type_by_code(self, code: str) -> LocationType | None: ...

    def add_type(self, location_type: LocationType) -> None: ...

    def update_type(self, location_type: LocationType) -> None: ...

    def list_locations(self, *, include_inactive: bool = True) -> list[Location]: ...

    def get(self, location_id: UUID) -> Location | None: ...

    def get_by_qr_token(self, qr_token: str) -> Location | None: ...

    def find_sibling(
        self,
        parent_id: UUID | None,
        normalized_code: str,
        *,
        exclude_id: UUID | None = None,
    ) -> Location | None: ...

    def list_children(
        self, parent_id: UUID, *, include_inactive: bool = True
    ) -> list[Location]: ...

    def add(self, location: Location) -> None: ...

    def flush(self) -> None: ...

    def update(self, location: Location) -> None: ...

    def remove(self, location_id: UUID) -> None: ...


class LocationUnitOfWork(Protocol):
    locations: LocationRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...


LocationUnitOfWorkFactory = Callable[[], LocationUnitOfWork]
