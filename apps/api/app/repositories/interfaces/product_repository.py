"""
Product and Category repository interface contract.

Defines data-access abstraction using typing.Protocol.
Services depend exclusively on this interface, never on concrete database classes.
No SQLAlchemy-specific constructs or session leaks are exposed.
"""

from typing import Any, Protocol, runtime_checkable

from app.models.catalog import Category, Product


@runtime_checkable
class ProductRepositoryInterface(Protocol):
    """Abstraction for product and category catalog data operations."""

    def get_by_id(self, product_id: str) -> Product | None:
        """Fetch a single product by unique ID."""
        ...

    def get_by_sku(self, sku: str) -> Product | None:
        """Fetch a single product by SKU natural key."""
        ...

    def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Product]:
        """List products with pagination, category filtering, search, and active state filters."""
        ...

    def create_product(self, product_data: dict[str, Any]) -> Product:
        """Persist a newly created product entity."""
        ...

    def update_product(self, product_id: str, update_data: dict[str, Any]) -> Product | None:
        """Update fields on an existing product."""
        ...

    def update_prices(
        self, product_id: str, wholesale_price: float, cost_price: float | None = None
    ) -> Product | None:
        """Update wholesale and/or cost prices for a product."""
        ...

    def deactivate_product(self, product_id: str) -> Product | None:
        """Deactivate a product (soft delete by setting is_active=False)."""
        ...

    def set_image_url(self, product_id: str, image_url: str) -> Product | None:
        """Set or update the public image URL for a product."""
        ...

    def delete(self, product_id: str) -> bool:
        """Permanently delete a product record."""
        ...

    def has_open_orders(self, product_id: str) -> bool:
        """Check whether any open Purchase Orders or Sales Orders reference this product."""
        ...

    # Category operations
    def list_categories(self) -> list[Category]:
        """List all product categories."""
        ...

    def get_category_by_id(self, category_id: str) -> Category | None:
        """Fetch a single category by ID."""
        ...

    def create_category(self, category_data: dict[str, Any]) -> Category:
        """Create a new product category."""
        ...

    def update_category(self, category_id: str, update_data: dict[str, Any]) -> Category | None:
        """Update an existing product category."""
        ...

    def delete_category(self, category_id: str) -> bool:
        """Delete a category by ID."""
        ...
