"""SQLAlchemy and In-Memory implementations of DeliveryRepositoryInterface."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.models.delivery import Delivery, DeliveryStatusEnum
from app.models.retailer import SalesOrder
from app.repositories.interfaces.delivery_repository import DeliveryRepositoryInterface


class SqlAlchemyDeliveryRepository(DeliveryRepositoryInterface):
    """Production SQLAlchemy implementation of DeliveryRepositoryInterface."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, delivery: Delivery) -> Delivery:
        """Persist a new delivery record."""
        self.session.add(delivery)
        self.session.flush()
        self.session.refresh(delivery)
        return delivery

    def get_by_id(self, delivery_id: str) -> Delivery | None:
        """Retrieve delivery with sales order and buyer details."""
        stmt = (
            select(Delivery)
            .options(
                joinedload(Delivery.sales_order).joinedload(SalesOrder.retailer),
                joinedload(Delivery.sales_order).joinedload(SalesOrder.customer),
            )
            .where(Delivery.id == delivery_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_sales_order_id(self, sales_order_id: str) -> Delivery | None:
        """Retrieve delivery associated with a sales order."""
        stmt = (
            select(Delivery)
            .options(
                joinedload(Delivery.sales_order).joinedload(SalesOrder.retailer),
                joinedload(Delivery.sales_order).joinedload(SalesOrder.customer),
            )
            .where(Delivery.sales_order_id == sales_order_id)
            .order_by(desc(Delivery.created_at))
        )
        return self.session.execute(stmt).scalars().first()

    def update(self, delivery: Delivery) -> Delivery:
        """Update existing delivery record."""
        self.session.merge(delivery)
        self.session.flush()
        return delivery

    def list_all(
        self,
        status: DeliveryStatusEnum | str | None = None,
        driver_name: str | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[Delivery]:
        """List deliveries with optional filtering."""
        stmt = (
            select(Delivery)
            .options(
                joinedload(Delivery.sales_order).joinedload(SalesOrder.retailer),
                joinedload(Delivery.sales_order).joinedload(SalesOrder.customer),
            )
            .order_by(desc(Delivery.created_at))
        )

        if status:
            if isinstance(status, str):
                status = DeliveryStatusEnum(status)
            stmt = stmt.where(Delivery.status == status)

        if driver_name:
            stmt = stmt.where(Delivery.driver_name.ilike(f"%{driver_name.strip()}%"))

        stmt = stmt.offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())


class InMemoryDeliveryRepository(DeliveryRepositoryInterface):
    """In-memory implementation of Delivery repository for unit testing."""

    def __init__(self, deliveries: list[Delivery] | None = None):
        self._deliveries: dict[str, Delivery] = {}
        if deliveries:
            for d in deliveries:
                self._deliveries[d.id] = d

    def create(self, delivery: Delivery) -> Delivery:
        if not delivery.id:
            delivery.id = str(uuid.uuid4())
        if not getattr(delivery, "created_at", None):
            delivery.created_at = datetime.now(UTC)
        self._deliveries[delivery.id] = delivery
        return delivery

    def get_by_id(self, delivery_id: str) -> Delivery | None:
        return self._deliveries.get(delivery_id)

    def get_by_sales_order_id(self, sales_order_id: str) -> Delivery | None:
        matches = [d for d in self._deliveries.values() if d.sales_order_id == sales_order_id]
        if not matches:
            return None
        matches.sort(key=lambda d: getattr(d, "created_at", datetime.min), reverse=True)
        return matches[0]

    def update(self, delivery: Delivery) -> Delivery:
        self._deliveries[delivery.id] = delivery
        return delivery

    def list_all(
        self,
        status: DeliveryStatusEnum | str | None = None,
        driver_name: str | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[Delivery]:
        results = list(self._deliveries.values())
        if status:
            status_val = status.value if hasattr(status, "value") else str(status)
            results = [
                d
                for d in results
                if (d.status.value if hasattr(d.status, "value") else str(d.status)) == status_val
            ]
        if driver_name:
            q = driver_name.lower()
            results = [d for d in results if d.driver_name and q in d.driver_name.lower()]

        results.sort(key=lambda d: getattr(d, "created_at", datetime.min), reverse=True)
        return results[skip : skip + limit]
