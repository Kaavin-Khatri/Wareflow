"""Supplier repository interface definition."""

from typing import Any, Protocol, runtime_checkable

from app.models.supplier import Supplier


@runtime_checkable
class SupplierRepositoryInterface(Protocol):
    """Abstraction for supplier data operations."""

    def get_by_id(self, supplier_id: str) -> Supplier | None:
        """Fetch a single supplier by unique ID."""
        ...

    def get_by_name(self, name: str) -> Supplier | None:
        """Fetch a supplier by name (case-insensitive)."""
        ...

    def list_suppliers(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Supplier]:
        """List suppliers with pagination, search, and active state filters."""
        ...

    def create_supplier(self, data: dict[str, Any]) -> Supplier:
        """Persist a new supplier entity."""
        ...

    def update_supplier(self, supplier_id: str, data: dict[str, Any]) -> Supplier | None:
        """Update fields on an existing supplier."""
        ...

    def delete_supplier(self, supplier_id: str) -> bool:
        """Permanently delete a supplier record."""
        ...
