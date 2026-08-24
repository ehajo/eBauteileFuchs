"""Supplier adapter contract independent from Mouser response structures."""

from typing import Protocol

from ebauteilefuchs.domain.suppliers import SupplierProduct, SupplierSearchMode


class SupplierAdapter(Protocol):
    code: str

    @property
    def configured(self) -> bool: ...

    def search(
        self, query: str, mode: SupplierSearchMode
    ) -> tuple[SupplierProduct, ...]: ...
