"""Generic supplier cache port; Mouser use is disabled by current API terms."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SupplierCacheEntry:
    supplier_id: UUID
    query_type: str
    query_normalized: str
    adapter_version: str
    response_json: str
    status: str
    created_at: datetime
    expires_at: datetime


class SupplierCache(Protocol):
    def get(
        self,
        supplier_id: UUID,
        query_type: str,
        query_normalized: str,
        adapter_version: str,
        *,
        now: datetime,
    ) -> SupplierCacheEntry | None: ...

    def put(self, entry: SupplierCacheEntry) -> None: ...
    def clear(self, supplier_id: UUID | None = None) -> int: ...
