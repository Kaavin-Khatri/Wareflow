"""
Concrete implementations of ProductRepositoryInterface.

Includes InMemoryProductRepository (for tests and DIP verification) and
SqlAlchemyProductRepository (for PostgreSQL persistence via SQLAlchemy).
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.catalog import Category, Product
from app.models.retailer import SalesOrder, SalesOrderItem, SOStatusEnum
from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem
from app.repositories.interfaces.product_repository import ProductRepositoryInterface


class InMemoryProductRepository(ProductRepositoryInterface):
    """In-memory implementation of ProductRepositoryInterface for tests and DIP proof."""

    def __init__(
        self,
        seed_products: list[Any] | None = None,
        seed_categories: list[Any] | None = None,
        seed_data: list[Any] | None = None,
    ) -> None:
        initial = seed_products or seed_data or []
        self._products: dict[str, dict[str, Any]] = {}
        for item in initial:
            if isinstance(item, Product):
                self._products[item.id] = {
                    "id": item.id,
                    "sku": item.sku,
                    "name": item.name,
                    "barcode": item.barcode,
                    "category_id": item.category_id,
                    "base_uom_id": item.base_uom_id,
                    "reorder_point": item.reorder_point,
                    "reorder_qty": item.reorder_qty,
                    "cost_price": float(item.cost_price or 0.0),
                    "wholesale_price": float(item.wholesale_price or 0.0),
                    "unit": item.unit,
                    "is_active": getattr(item, "is_active", True),
                }
            else:
                self._products[item["id"]] = dict(item)

        self._categories: dict[str, dict[str, Any]] = {}
        for item in seed_categories or []:
            if hasattr(item, "id"):
                self._categories[item.id] = {
                    "id": item.id,
                    "name": getattr(item, "name", ""),
                }
            else:
                self._categories[item["id"]] = dict(item)
        self._open_orders: set[str] = set()

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Any]:
        """Backwards compatibility alias for list_products."""
        return list(self._products.values())[skip : skip + limit]

    def set_product_open_orders(self, product_id: str, has_open: bool) -> None:
        """Helper to simulate open orders in unit tests."""
        if has_open:
            self._open_orders.add(product_id)
        else:
            self._open_orders.discard(product_id)

    def get_by_id(self, product_id: str) -> Any:
        return self._products.get(product_id)

    def get_by_sku(self, sku: str) -> Any:
        sku_clean = sku.strip().lower()
        for prod in self._products.values():
            if str(prod.get("sku", "")).strip().lower() == sku_clean:
                return prod
        return None

    def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Any]:
        results = list(self._products.values())
        if category_id:
            results = [p for p in results if p.get("category_id") == category_id]
        if is_active is not None:
            results = [p for p in results if p.get("is_active", True) is is_active]
        if search:
            s = search.lower()
            results = [
                p
                for p in results
                if s in str(p.get("name", "")).lower()
                or s in str(p.get("sku", "")).lower()
                or s in str(p.get("barcode", "")).lower()
            ]
        return results[skip : skip + limit]

    def create_product(self, product_data: dict[str, Any]) -> Any:
        prod_id = product_data.get("id") or str(uuid.uuid4())
        record = {
            **product_data,
            "id": prod_id,
            "is_active": product_data.get("is_active", True),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        self._products[prod_id] = record
        return record

    def update_product(self, product_id: str, update_data: dict[str, Any]) -> Any:
        if product_id not in self._products:
            return None
        self._products[product_id].update(update_data)
        self._products[product_id]["updated_at"] = datetime.now(UTC)
        return self._products[product_id]

    def update_prices(
        self, product_id: str, wholesale_price: float, cost_price: float | None = None
    ) -> Any:
        if product_id not in self._products:
            return None
        self._products[product_id]["wholesale_price"] = wholesale_price
        if cost_price is not None:
            self._products[product_id]["cost_price"] = cost_price
        self._products[product_id]["updated_at"] = datetime.now(UTC)
        return self._products[product_id]

    def deactivate_product(self, product_id: str) -> Any:
        if product_id not in self._products:
            return None
        self._products[product_id]["is_active"] = False
        self._products[product_id]["updated_at"] = datetime.now(UTC)
        return self._products[product_id]

    def set_image_url(self, product_id: str, image_url: str) -> Any:
        if product_id not in self._products:
            return None
        self._products[product_id]["image_url"] = image_url
        self._products[product_id]["updated_at"] = datetime.now(UTC)
        return self._products[product_id]

    def delete(self, product_id: str) -> bool:
        if product_id in self._products:
            del self._products[product_id]
            return True
        return False

    def has_open_orders(self, product_id: str) -> bool:
        return product_id in self._open_orders

    def list_categories(self) -> list[Any]:
        return list(self._categories.values())

    def get_category_by_id(self, category_id: str) -> Any:
        return self._categories.get(category_id)

    def create_category(self, category_data: dict[str, Any]) -> Any:
        cat_id = category_data.get("id") or str(uuid.uuid4())
        record = {
            **category_data,
            "id": cat_id,
            "created_at": datetime.now(UTC),
        }
        self._categories[cat_id] = record
        return record

    def update_category(self, category_id: str, update_data: dict[str, Any]) -> Any:
        if category_id not in self._categories:
            return None
        self._categories[category_id].update(update_data)
        return self._categories[category_id]

    def delete_category(self, category_id: str) -> bool:
        if category_id in self._categories:
            del self._categories[category_id]
            return True
        return False


class SqlAlchemyProductRepository(ProductRepositoryInterface):
    """SQLAlchemy implementation of ProductRepositoryInterface."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, product_id: str) -> Product | None:
        return self.session.scalar(
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.base_uom))
            .where(Product.id == product_id)
        )

    def get_by_sku(self, sku: str) -> Product | None:
        return self.session.scalar(
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.base_uom))
            .where(func.lower(Product.sku) == sku.strip().lower())
        )

    def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Product]:
        query = select(Product).options(joinedload(Product.category), joinedload(Product.base_uom))

        if category_id:
            query = query.where(Product.category_id == category_id)

        if is_active is not None:
            query = query.where(Product.is_active == is_active)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.sku.ilike(search_pattern),
                    Product.barcode.ilike(search_pattern),
                    Product.hsn_code.ilike(search_pattern),
                )
            )

        query = query.order_by(Product.name.asc()).offset(skip).limit(limit)
        return list(self.session.scalars(query).all())

    def create_product(self, product_data: dict[str, Any]) -> Product:
        product = Product(**product_data)
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def update_product(self, product_id: str, update_data: dict[str, Any]) -> Product | None:
        product = self.get_by_id(product_id)
        if not product:
            return None
        for key, value in update_data.items():
            if hasattr(product, key):
                setattr(product, key, value)
        product.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(product)
        return product

    def update_prices(
        self, product_id: str, wholesale_price: float, cost_price: float | None = None
    ) -> Product | None:
        product = self.get_by_id(product_id)
        if not product:
            return None
        product.wholesale_price = wholesale_price
        if cost_price is not None:
            product.cost_price = cost_price
        product.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(product)
        return product

    def deactivate_product(self, product_id: str) -> Product | None:
        product = self.get_by_id(product_id)
        if not product:
            return None
        product.is_active = False
        product.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(product)
        return product

    def set_image_url(self, product_id: str, image_url: str) -> Product | None:
        product = self.get_by_id(product_id)
        if not product:
            return None
        product.image_url = image_url
        product.updated_at = datetime.now(UTC)
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

    def has_open_orders(self, product_id: str) -> bool:
        # Check open purchase order items
        po_query = (
            select(func.count(PurchaseOrderItem.id))
            .join(PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id)
            .where(
                PurchaseOrderItem.product_id == product_id,
                PurchaseOrder.status.notin_([POStatusEnum.RECEIVED, POStatusEnum.CANCELLED]),
            )
        )
        po_count = self.session.scalar(po_query) or 0
        if po_count > 0:
            return True

        # Check open sales order items
        so_query = (
            select(func.count(SalesOrderItem.id))
            .join(SalesOrder, SalesOrderItem.so_id == SalesOrder.id)
            .where(
                SalesOrderItem.product_id == product_id,
                SalesOrder.status.notin_([SOStatusEnum.DELIVERED, SOStatusEnum.CANCELLED]),
            )
        )
        so_count = self.session.scalar(so_query) or 0
        return so_count > 0

    # Category operations
    def list_categories(self) -> list[Category]:
        return list(self.session.scalars(select(Category).order_by(Category.name.asc())).all())

    def get_category_by_id(self, category_id: str) -> Category | None:
        return self.session.scalar(select(Category).where(Category.id == category_id))

    def create_category(self, category_data: dict[str, Any]) -> Category:
        category = Category(**category_data)
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category

    def update_category(self, category_id: str, update_data: dict[str, Any]) -> Category | None:
        category = self.get_category_by_id(category_id)
        if not category:
            return None
        for key, value in update_data.items():
            if hasattr(category, key):
                setattr(category, key, value)
        self.session.commit()
        self.session.refresh(category)
        return category

    def delete_category(self, category_id: str) -> bool:
        category = self.get_category_by_id(category_id)
        if not category:
            return False
        self.session.delete(category)
        self.session.commit()
        return True
