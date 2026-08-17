"""
Concrete implementations of ProductRepositoryInterface.

Includes InMemoryProductRepository (for tests and standalone dev) and
SqlAlchemyProductRepository (for Postgres persistence).
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import Product
from app.repositories.interfaces.product_repository import ProductRepositoryInterface


class InMemoryProductRepository(ProductRepositoryInterface):
    """In-memory implementation of ProductRepositoryInterface."""

    def __init__(self, seed_data: list[dict[str, Any]] | None = None) -> None:
        self._products: dict[str, dict[str, Any]] = {item["id"]: item for item in (seed_data or [])}

    def get_by_id(self, product_id: str) -> dict[str, Any] | None:
        return self._products.get(product_id)

    def list_all(self, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._products.values())[skip : skip + limit]

    def update_prices(
        self, product_id: str, wholesale_price: float, cost_price: float | None = None
    ) -> dict[str, Any] | None:
        if product_id not in self._products:
            return None
        self._products[product_id]["wholesale_price"] = wholesale_price
        if cost_price is not None:
            self._products[product_id]["cost_price"] = cost_price
        return self._products[product_id]

    def delete(self, product_id: str) -> bool:
        if product_id in self._products:
            del self._products[product_id]
            return True
        return False


class SqlAlchemyProductRepository(ProductRepositoryInterface):
    """SQLAlchemy implementation of ProductRepositoryInterface."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, product_id: str) -> Product | None:
        return self.session.scalar(select(Product).where(Product.id == product_id))

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Product]:
        return list(self.session.scalars(select(Product).offset(skip).limit(limit)).all())

    def update_prices(
        self, product_id: str, wholesale_price: float, cost_price: float | None = None
    ) -> Product | None:
        product = self.get_by_id(product_id)
        if not product:
            return None
        product.wholesale_price = wholesale_price
        if cost_price is not None:
            product.cost_price = cost_price
        self.session.commit()
        self.session.refresh(product)
        return product

    def delete(self, product_id: str) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False
        self.session.delete(product)
        self.session.commit()
        return True
