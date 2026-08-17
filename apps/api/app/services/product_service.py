"""
Product domain service.

Contains business logic for product management and price updates.
Depends strictly on ProductRepositoryInterface abstraction (Dependency Inversion Principle).
"""

from typing import Any

from fastapi import HTTPException, status

from app.models.catalog import Product
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.services.audit_service import AuditService


class ProductService:
    """Service handling product business logic and audited price updates."""

    def __init__(
        self,
        repository: ProductRepositoryInterface,
        audit_service: AuditService | None = None,
    ) -> None:
        self._repo = repository
        self._audit = audit_service

    def get_product(self, product_id: str) -> Product | dict[str, Any]:
        """Fetch a product by ID with domain validation."""
        if not product_id.strip():
            raise ValueError("Product ID cannot be empty.")
        product = self._repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' not found.",
            )
        return product

    def list_products(
        self, skip: int = 0, limit: int = 100
    ) -> list[Product] | list[dict[str, Any]]:
        """List all active inventory products."""
        return self._repo.list_all(skip=skip, limit=limit)

    def update_price(
        self,
        product_id: str,
        wholesale_price: float,
        cost_price: float | None = None,
        actor_id: str | None = None,
    ) -> Product | dict[str, Any]:
        """Update product pricing and record an immutable audit log entry."""
        if wholesale_price < 0 or (cost_price is not None and cost_price < 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price values cannot be negative.",
            )

        product = self.get_product(product_id)
        if isinstance(product, dict):
            old_wholesale = float(product.get("wholesale_price", 0))
            old_cost = float(product.get("cost_price", 0))
            prod_name = product.get("name", product_id)
            prod_sku = product.get("sku", "")
        else:
            old_wholesale = float(product.wholesale_price)
            old_cost = float(product.cost_price)
            prod_name = product.name
            prod_sku = product.sku

        updated = self._repo.update_prices(
            product_id=product_id,
            wholesale_price=wholesale_price,
            cost_price=cost_price,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' not found.",
            )

        if self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="product_price_updated",
                entity_type="product",
                entity_id=product_id,
                before={
                    "name": prod_name,
                    "sku": prod_sku,
                    "wholesale_price": old_wholesale,
                    "cost_price": old_cost,
                },
                after={
                    "name": prod_name,
                    "sku": prod_sku,
                    "wholesale_price": float(wholesale_price),
                    "cost_price": float(cost_price if cost_price is not None else old_cost),
                },
            )

        return updated

    def delete_product(self, product_id: str, actor_id: str | None = None) -> bool:
        """Delete a product and log the deletion."""
        product = self.get_product(product_id)
        prod_name = product.get("name") if isinstance(product, dict) else product.name

        deleted = self._repo.delete(product_id)
        if deleted and self._audit:
            self._audit.log(
                actor_id=actor_id,
                action="product_deleted",
                entity_type="product",
                entity_id=product_id,
                before={"name": prod_name},
                after=None,
            )
        return deleted
