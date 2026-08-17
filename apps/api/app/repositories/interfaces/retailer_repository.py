"""Retailer repository interface definition."""

from typing import Protocol, runtime_checkable

from app.models.retailer import Retailer


@runtime_checkable
class RetailerRepository(Protocol):
    """Abstraction for wholesale retailer data operations."""

    def get_by_id(self, retailer_id: str) -> Retailer | None:
        """Fetch retailer by ID."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Retailer]:
        """List retailers with pagination."""
        ...

    def update_credit_limit(self, retailer_id: str, new_limit: float) -> Retailer | None:
        """Update credit limit for a retailer."""
        ...
