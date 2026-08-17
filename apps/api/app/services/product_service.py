"""
Product domain service.

Contains business logic for product management.
Depends strictly on ProductRepositoryInterface abstraction (Dependency Inversion Principle).
"""

from app.repositories.interfaces.product_repository import ProductRepositoryInterface


class ProductService:
    """Service handling product business logic."""

    def __init__(self, repository: ProductRepositoryInterface) -> None:
        self._repo = repository

    def get_product(self, product_id: str) -> dict[str, str] | None:
        """Fetch a product by ID with domain validation."""
        if not product_id.strip():
            raise ValueError("Product ID cannot be empty.")
        return self._repo.get_by_id(product_id)

    def list_products(self) -> list[dict[str, str]]:
        """List all active inventory products."""
        return self._repo.list_all()
