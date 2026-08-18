"""SQLAlchemy and In-Memory implementations of SalesOrderRepositoryInterface."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.catalog import Product
from app.models.retailer import BuyerTypeEnum, Retailer, SalesOrder, SalesOrderItem, SOStatusEnum
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface


class SqlAlchemySalesOrderRepository(SalesOrderRepositoryInterface):
    """Production SQLAlchemy implementation of SalesOrderRepositoryInterface."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, order_id: str) -> SalesOrder | None:
        stmt = (
            select(SalesOrder)
            .options(
                joinedload(SalesOrder.retailer),
                joinedload(SalesOrder.items)
                .joinedload(SalesOrderItem.product)
                .joinedload(Product.base_uom),
                joinedload(SalesOrder.items).joinedload(SalesOrderItem.uom),
            )
            .where(SalesOrder.id == order_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_so_number(self, so_number: str) -> SalesOrder | None:
        stmt = (
            select(SalesOrder)
            .options(
                joinedload(SalesOrder.retailer),
                joinedload(SalesOrder.items).joinedload(SalesOrderItem.product),
            )
            .where(SalesOrder.so_number == so_number)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(
        self,
        status: str | None = None,
        retailer_id: str | None = None,
        buyer_type: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[SalesOrder], int]:
        stmt = select(SalesOrder).options(
            joinedload(SalesOrder.retailer),
            joinedload(SalesOrder.items).joinedload(SalesOrderItem.product),
        )

        if status:
            stmt = stmt.where(SalesOrder.status == status)
        if retailer_id:
            stmt = stmt.where(SalesOrder.retailer_id == retailer_id)
        if buyer_type:
            stmt = stmt.where(SalesOrder.buyer_type == buyer_type)
        if search:
            s = f"%{search.strip()}%"
            stmt = stmt.outerjoin(Retailer, SalesOrder.retailer_id == Retailer.id).where(
                or_(
                    SalesOrder.so_number.ilike(s),
                    Retailer.name.ilike(s),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        # Paginate
        stmt = stmt.order_by(SalesOrder.created_at.desc()).offset(skip).limit(limit)
        items = list(self.session.execute(stmt).scalars().all())

        return items, total

    def create(self, order: SalesOrder) -> SalesOrder:
        self.session.add(order)
        self.session.flush()
        return self.get_by_id(order.id) or order

    def update(self, order: SalesOrder) -> SalesOrder:
        self.session.flush()
        return self.get_by_id(order.id) or order

    def generate_next_so_number(self) -> str:
        now = datetime.now(UTC)
        prefix = f"SO-{now.strftime('%Y%m')}"
        stmt = select(func.count(SalesOrder.id)).where(SalesOrder.so_number.like(f"{prefix}-%"))
        count = (self.session.execute(stmt).scalar() or 0) + 1
        return f"{prefix}-{count:04d}"


class InMemorySalesOrderRepository(SalesOrderRepositoryInterface):
    """In-Memory implementation of SalesOrderRepositoryInterface for fast isolated tests."""

    def __init__(
        self,
        orders: list[dict[str, Any] | SalesOrder] | None = None,
        initial_data: list[dict[str, Any] | SalesOrder] | None = None,
    ):
        self.orders: dict[str, dict[str, Any]] = {}
        all_orders = orders or initial_data
        if all_orders:
            for o in all_orders:
                if isinstance(o, SalesOrder):
                    self.orders[o.id] = {
                        "id": o.id,
                        "so_number": o.so_number,
                        "buyer_type": o.buyer_type,
                        "retailer_id": o.retailer_id,
                        "customer_id": o.customer_id,
                        "status": o.status,
                        "total_amount": o.total_amount,
                        "order_date": o.order_date,
                        "created_at": o.created_at,
                        "items": [
                            {
                                "id": it.id,
                                "so_id": it.so_id,
                                "product_id": it.product_id,
                                "qty": it.qty,
                                "unit_price": it.unit_price,
                                "uom_id": getattr(it, "uom_id", None),
                            }
                            for it in (o.items or [])
                        ],
                    }
                else:
                    self.orders[o["id"]] = dict(o)


    def _to_model(self, data: dict[str, Any]) -> SalesOrder:
        so = SalesOrder(
            id=data["id"],
            so_number=data["so_number"],
            buyer_type=data.get("buyer_type", BuyerTypeEnum.RETAILER),
            retailer_id=data.get("retailer_id"),
            customer_id=data.get("customer_id"),
            status=data.get("status", SOStatusEnum.DRAFT),
            total_amount=float(data.get("total_amount", 0.0)),
        )
        so.order_date = data.get("order_date", datetime.now(UTC))
        so.created_at = data.get("created_at", datetime.now(UTC))

        if data.get("retailer"):
            r_data = data["retailer"]
            so.retailer = Retailer(
                id=r_data["id"],
                name=r_data["name"],
                pricing_tier=r_data.get("pricing_tier", "standard"),
                credit_limit=float(r_data.get("credit_limit", 0.0)),
                credit_balance=float(r_data.get("credit_balance", 0.0)),
                gstin=r_data.get("gstin"),
                phone=r_data.get("phone"),
                email=r_data.get("email"),
                address=r_data.get("address"),
            )


        items: list[SalesOrderItem] = []
        for item_data in data.get("items", []):
            item = SalesOrderItem(
                id=item_data.get("id", str(uuid.uuid4())),
                so_id=so.id,
                product_id=item_data["product_id"],
                qty=float(item_data["qty"]),
                unit_price=float(item_data["unit_price"]),
                uom_id=item_data.get("uom_id"),
            )
            if item_data.get("product"):
                p_data = item_data["product"]
                item.product = Product(
                    id=p_data["id"],
                    sku=p_data["sku"],
                    name=p_data["name"],
                    cost_price=float(p_data.get("cost_price", 0.0)),
                    wholesale_price=float(p_data.get("wholesale_price", 0.0)),
                )
            items.append(item)
        so.items = items
        return so

    def get_by_id(self, order_id: str) -> SalesOrder | None:
        data = self.orders.get(order_id)
        if not data:
            return None
        return self._to_model(data)

    def get_by_so_number(self, so_number: str) -> SalesOrder | None:
        for data in self.orders.values():
            if data.get("so_number") == so_number:
                return self._to_model(data)
        return None

    def list_all(
        self,
        status: str | None = None,
        retailer_id: str | None = None,
        buyer_type: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[SalesOrder], int]:
        filtered = list(self.orders.values())

        if status:
            filtered = [o for o in filtered if o.get("status") == status]
        if retailer_id:
            filtered = [o for o in filtered if o.get("retailer_id") == retailer_id]
        if buyer_type:
            filtered = [o for o in filtered if o.get("buyer_type") == buyer_type]
        if search:
            s = search.lower()
            filtered = [
                o
                for o in filtered
                if s in o.get("so_number", "").lower()
                or (o.get("retailer") and s in o["retailer"].get("name", "").lower())
            ]

        total = len(filtered)
        paged = filtered[skip : skip + limit]
        return [self._to_model(o) for o in paged], total

    def create(self, order: SalesOrder) -> SalesOrder:
        order_dict = {
            "id": order.id,
            "so_number": order.so_number,
            "buyer_type": order.buyer_type,
            "retailer_id": order.retailer_id,
            "customer_id": order.customer_id,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "order_date": order.order_date or datetime.now(UTC),
            "created_at": order.created_at or datetime.now(UTC),
            "items": [
                {
                    "id": it.id,
                    "so_id": order.id,
                    "product_id": it.product_id,
                    "qty": float(it.qty),
                    "unit_price": float(it.unit_price),
                    "uom_id": it.uom_id,
                    "product": {
                        "id": it.product.id,
                        "sku": it.product.sku,
                        "name": it.product.name,
                    }
                    if getattr(it, "product", None)
                    else None,
                }
                for it in order.items
            ],
        }
        if getattr(order, "retailer", None):
            order_dict["retailer"] = {
                "id": order.retailer.id,
                "name": order.retailer.name,
                "pricing_tier": getattr(order.retailer, "pricing_tier", "standard"),
                "credit_limit": float(order.retailer.credit_limit),
                "credit_balance": float(order.retailer.credit_balance),
                "gstin": getattr(order.retailer, "gstin", None),
                "phone": getattr(order.retailer, "phone", None),
                "email": getattr(order.retailer, "email", None),
                "address": getattr(order.retailer, "address", None),
            }
        self.orders[order.id] = order_dict

        return self._to_model(order_dict)

    def update(self, order: SalesOrder) -> SalesOrder:
        return self.create(order)

    def generate_next_so_number(self) -> str:
        now = datetime.now(UTC)
        prefix = f"SO-{now.strftime('%Y%m')}"
        count = (
            sum(1 for o in self.orders.values() if o.get("so_number", "").startswith(prefix)) + 1
        )
        return f"{prefix}-{count:04d}"
