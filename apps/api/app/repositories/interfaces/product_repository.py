"""
Product repository interface contract.

Defines data-access abstraction using typing.Protocol.
Services depend exclusively on this interface, never on concrete database classes.
"""

from typing import Any, Protocol, runtime_checkable

from app.models.catalog import Product


@runtime_checkable
class ProductRepositoryInterface(Protocol):
    """Abstraction for product data operations."""

    def get_by_id(self, product_id: str) -> Product | dict[str, Any] | None:
        """Fetch a single product by ID."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Product] | list[dict[str, Any]]:
        """List all products."""
        ...

    def update_prices(
        self, product_id: str, wholesale_price: float, cost_price: float | None = None
    ) -> Product | dict[str, Any] | None:
        """Update wholesale and/or cost prices for a product."""
        ...

    def delete(self, product_id: str) -> bool:
        """Delete or deactivate a product."""
        ...
