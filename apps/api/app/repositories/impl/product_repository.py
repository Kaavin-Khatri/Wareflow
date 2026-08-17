"""
Concrete implementations of ProductRepositoryInterface.

Includes InMemoryProductRepository (for tests and standalone dev) and
SqlAlchemyProductRepository (for Postgres persistence).
"""

from app.repositories.interfaces.product_repository import ProductRepositoryInterface


class InMemoryProductRepository(ProductRepositoryInterface):
    """In-memory implementation of ProductRepositoryInterface."""

    def __init__(self, seed_data: list[dict[str, str]] | None = None) -> None:
        self._products: dict[str, dict[str, str]] = {item["id"]: item for item in (seed_data or [])}

    def get_by_id(self, product_id: str) -> dict[str, str] | None:
        return self._products.get(product_id)

    def list_all(self) -> list[dict[str, str]]:
        return list(self._products.values())


class SqlAlchemyProductRepository(ProductRepositoryInterface):
    """SQLAlchemy implementation of ProductRepositoryInterface."""

    def __init__(self, session: object | None = None) -> None:
        self.session = session

    def get_by_id(self, product_id: str) -> dict[str, str] | None:
        # Placeholder pending Phase 2 table models
        return None

    def list_all(self) -> list[dict[str, str]]:
        # Placeholder pending Phase 2 table models
        return []
