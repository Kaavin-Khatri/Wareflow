"""Implementations for StockAnalyticsRepositoryInterface (Step 6.1)."""

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.catalog import Category, Product
from app.models.warehouse import StockBatch, Warehouse
from app.repositories.interfaces.stock_analytics_repository import (
    StockAnalyticsRepositoryInterface,
)


class SqlAlchemyStockAnalyticsRepository(StockAnalyticsRepositoryInterface):
    """SQLAlchemy implementation of StockAnalyticsRepositoryInterface."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_stock_valuation_data(self) -> list[dict[str, Any]]:
        """Fetch joined batches with product cost_price, category, and warehouse info."""
        results = (
            self.session.query(
                StockBatch.id.label("batch_id"),
                StockBatch.batch_no,
                StockBatch.quantity,
                StockBatch.warehouse_id,
                Warehouse.name.label("warehouse_name"),
                Product.id.label("product_id"),
                Product.sku,
                Product.name.label("product_name"),
                Product.cost_price,
                Product.category_id,
                Category.name.label("category_name"),
            )
            .join(Product, StockBatch.product_id == Product.id)
            .join(Warehouse, StockBatch.warehouse_id == Warehouse.id)
            .outerjoin(Category, Product.category_id == Category.id)
            .filter(StockBatch.quantity > 0, Product.is_active.is_(True))
            .all()
        )
        rows: list[dict[str, Any]] = []
        for r in results:
            d = r._asdict()
            d["quantity"] = float(d["quantity"])
            d["cost_price"] = float(d["cost_price"] or 0.0)
            rows.append(d)
        return rows

    def get_health_distribution_data(self) -> list[dict[str, Any]]:
        """Fetch active products with reorder_points and on-hand totals."""
        products = (
            self.session.query(Product)
            .filter(Product.is_active.is_(True))
            .options(joinedload(Product.category))
            .all()
        )
        on_hand_subq = dict(
            self.session.query(
                StockBatch.product_id,
                func.coalesce(func.sum(StockBatch.quantity), 0.0),
            )
            .group_by(StockBatch.product_id)
            .all()
        )
        rows: list[dict[str, Any]] = []
        for p in products:
            on_hand = float(on_hand_subq.get(p.id, 0.0))
            rows.append(
                {
                    "product_id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "reorder_point": p.reorder_point or 0,
                    "total_on_hand": on_hand,
                }
            )
        return rows

    def get_top_products_data(self) -> list[dict[str, Any]]:
        """Fetch active products with total on-hand, cost_price, and base unit."""
        products = (
            self.session.query(Product)
            .filter(Product.is_active.is_(True))
            .options(
                joinedload(Product.category),
                joinedload(Product.base_uom),
            )
            .all()
        )
        on_hand_subq = dict(
            self.session.query(
                StockBatch.product_id,
                func.coalesce(func.sum(StockBatch.quantity), 0.0),
            )
            .group_by(StockBatch.product_id)
            .all()
        )
        rows: list[dict[str, Any]] = []
        for p in products:
            on_hand = float(on_hand_subq.get(p.id, 0.0))
            cost = float(p.cost_price or 0.0)
            rows.append(
                {
                    "product_id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "category_name": p.category.name if p.category else "Uncategorized",
                    "total_on_hand": on_hand,
                    "cost_price": cost,
                    "total_value": round(on_hand * cost, 2),
                    "base_uom_name": p.base_uom.name if p.base_uom else "Units",
                }
            )
        return rows

    def get_batch_expiry_data(self) -> list[dict[str, Any]]:
        """Fetch all positive stock batches with product cost and expiry dates."""
        results = (
            self.session.query(
                StockBatch.id.label("batch_id"),
                StockBatch.batch_no,
                StockBatch.quantity,
                StockBatch.expiry_date,
                Product.cost_price,
            )
            .join(Product, StockBatch.product_id == Product.id)
            .filter(StockBatch.quantity > 0, Product.is_active.is_(True))
            .all()
        )
        rows: list[dict[str, Any]] = []
        for r in results:
            d = r._asdict()
            d["quantity"] = float(d["quantity"])
            d["cost_price"] = float(d["cost_price"] or 0.0)
            rows.append(d)
        return rows


class InMemoryStockAnalyticsRepository(StockAnalyticsRepositoryInterface):
    """In-memory test double for StockAnalyticsRepositoryInterface."""

    def __init__(
        self,
        products: list[dict[str, Any]] | None = None,
        categories: list[dict[str, Any]] | None = None,
        warehouses: list[dict[str, Any]] | None = None,
        batches: list[dict[str, Any]] | None = None,
    ) -> None:
        self.products = {p["id"]: p for p in (products or [])}
        self.categories = {c["id"]: c for c in (categories or [])}
        self.warehouses = {w["id"]: w for w in (warehouses or [])}
        self.batches = {b["id"]: b for b in (batches or [])}

    def get_stock_valuation_data(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for b in self.batches.values():
            qty = float(b.get("quantity", 0.0))
            if qty <= 0:
                continue
            prod = self.products.get(b.get("product_id"))
            if not prod or not prod.get("is_active", True):
                continue
            wh = self.warehouses.get(b.get("warehouse_id"), {})
            cat = self.categories.get(prod.get("category_id"), {})
            rows.append(
                {
                    "batch_id": b["id"],
                    "batch_no": b.get("batch_no", ""),
                    "quantity": qty,
                    "warehouse_id": b.get("warehouse_id", ""),
                    "warehouse_name": wh.get("name", "Unknown Warehouse"),
                    "product_id": prod["id"],
                    "sku": prod.get("sku", ""),
                    "product_name": prod.get("name", ""),
                    "cost_price": float(prod.get("cost_price", 0.0)),
                    "category_id": prod.get("category_id"),
                    "category_name": cat.get("name", "Uncategorized"),
                }
            )
        return rows

    def get_health_distribution_data(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for prod in self.products.values():
            if not prod.get("is_active", True):
                continue
            pid = prod["id"]
            on_hand = sum(
                float(b.get("quantity", 0.0))
                for b in self.batches.values()
                if b.get("product_id") == pid
            )
            rows.append(
                {
                    "product_id": pid,
                    "sku": prod.get("sku", ""),
                    "name": prod.get("name", ""),
                    "reorder_point": prod.get("reorder_point", 0),
                    "total_on_hand": on_hand,
                }
            )
        return rows

    def get_top_products_data(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for prod in self.products.values():
            if not prod.get("is_active", True):
                continue
            pid = prod["id"]
            on_hand = sum(
                float(b.get("quantity", 0.0))
                for b in self.batches.values()
                if b.get("product_id") == pid
            )
            cost = float(prod.get("cost_price", 0.0))
            cat = self.categories.get(prod.get("category_id"), {})
            rows.append(
                {
                    "product_id": pid,
                    "sku": prod.get("sku", ""),
                    "name": prod.get("name", ""),
                    "category_name": cat.get("name", "Uncategorized"),
                    "total_on_hand": on_hand,
                    "cost_price": cost,
                    "total_value": round(on_hand * cost, 2),
                    "base_uom_name": prod.get("base_uom_name", "Units"),
                }
            )
        return rows

    def get_batch_expiry_data(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for b in self.batches.values():
            qty = float(b.get("quantity", 0.0))
            if qty <= 0:
                continue
            prod = self.products.get(b.get("product_id"))
            if not prod or not prod.get("is_active", True):
                continue
            rows.append(
                {
                    "batch_id": b["id"],
                    "batch_no": b.get("batch_no", ""),
                    "quantity": qty,
                    "expiry_date": b.get("expiry_date"),
                    "cost_price": float(prod.get("cost_price", 0.0)),
                }
            )
        return rows
