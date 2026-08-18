"""Retailer repository interface definition."""

from typing import Any, Protocol, runtime_checkable

from app.models.retailer import Retailer


@runtime_checkable
class RetailerRepository(Protocol):
    """Abstraction for wholesale retailer data operations."""

    def get_by_id(self, retailer_id: str) -> Retailer | None:
        """Fetch retailer by ID."""
        ...

    def get_by_name(self, name: str) -> Retailer | None:
        """Fetch retailer by name (for duplicate validation)."""
        ...

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Retailer]:
        """List retailers with optional pagination, active filter, and search query."""
        ...

    def create(self, retailer: Retailer) -> Retailer:
        """Create and persist a new retailer record."""
        ...

    def update(self, retailer_id: str, updates: dict[str, Any]) -> Retailer | None:
        """Update fields on an existing retailer."""
        ...

    def update_credit_limit(self, retailer_id: str, new_limit: float) -> Retailer | None:
        """Update authorized credit limit for a retailer."""
        ...
