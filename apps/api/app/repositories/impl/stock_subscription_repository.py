"""SQLAlchemy and InMemory implementations for StockSubscriptionRepository (Step 13.4)."""

import logging
from typing import Any
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.portal import StockSubscription
from app.repositories.interfaces.stock_subscription_repository import (
    StockSubscriptionRepositoryInterface,
)

logger = logging.getLogger(__name__)


class SqlAlchemyStockSubscriptionRepository(StockSubscriptionRepositoryInterface):
    """PostgreSQL SQLAlchemy implementation of StockSubscription repository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, subscription_id: str) -> StockSubscription | None:
        stmt = (
            select(StockSubscription)
            .options(
                joinedload(StockSubscription.retailer),
                joinedload(StockSubscription.product),
            )
            .where(StockSubscription.id == subscription_id)
        )
        return self.session.scalars(stmt).first()

    def get_by_product_and_retailer(
        self, product_id: str, retailer_id: str
    ) -> StockSubscription | None:
        stmt = (
            select(StockSubscription)
            .options(
                joinedload(StockSubscription.retailer),
                joinedload(StockSubscription.product),
            )
            .where(
                StockSubscription.product_id == product_id,
                StockSubscription.retailer_id == retailer_id,
            )
        )
        return self.session.scalars(stmt).first()

    def list_active_for_product(self, product_id: str) -> list[StockSubscription]:
        stmt = (
            select(StockSubscription)
            .options(
                joinedload(StockSubscription.retailer),
                joinedload(StockSubscription.product),
            )
            .where(
                StockSubscription.product_id == product_id,
                StockSubscription.is_active.is_(True),
            )
            .order_by(StockSubscription.created_at.asc())
        )
        return list(self.session.scalars(stmt).all())

    def list_for_product(self, product_id: str) -> list[StockSubscription]:
        stmt = (
            select(StockSubscription)
            .options(
                joinedload(StockSubscription.retailer),
                joinedload(StockSubscription.product),
            )
            .where(StockSubscription.product_id == product_id)
            .order_by(StockSubscription.created_at.desc())
        )
        return list(self.session.scalars(stmt).all())

    def list_for_retailer(self, retailer_id: str) -> list[StockSubscription]:
        stmt = (
            select(StockSubscription)
            .options(
                joinedload(StockSubscription.retailer),
                joinedload(StockSubscription.product),
            )
            .where(StockSubscription.retailer_id == retailer_id)
            .order_by(StockSubscription.created_at.desc())
        )
        return list(self.session.scalars(stmt).all())

    def count_active_for_retailer(self, retailer_id: str) -> int:
        stmt = select(func.count(StockSubscription.id)).where(
            StockSubscription.retailer_id == retailer_id,
            StockSubscription.is_active.is_(True),
        )
        return self.session.scalar(stmt) or 0

    def count_active_by_retailers(self) -> dict[str, int]:
        stmt = (
            select(StockSubscription.retailer_id, func.count(StockSubscription.id))
            .where(StockSubscription.is_active.is_(True))
            .group_by(StockSubscription.retailer_id)
        )
        results = self.session.execute(stmt).all()
        return {r[0]: int(r[1]) for r in results}

    def create(self, subscription: StockSubscription) -> StockSubscription:
        self.session.add(subscription)
        self.session.commit()
        self.session.refresh(subscription)
        return subscription

    def update(self, subscription: StockSubscription) -> StockSubscription:
        self.session.add(subscription)
        self.session.commit()
        self.session.refresh(subscription)
        return subscription

    def delete(self, subscription_id: str) -> bool:
        sub = self.session.get(StockSubscription, subscription_id)
        if not sub:
            return False
        self.session.delete(sub)
        self.session.commit()
        return True


class InMemoryStockSubscriptionRepository(StockSubscriptionRepositoryInterface):
    """In-memory mock repository for tests."""

    def __init__(self) -> None:
        self._subscriptions: dict[str, StockSubscription] = {}

    def get_by_id(self, subscription_id: str) -> StockSubscription | None:
        return self._subscriptions.get(subscription_id)

    def get_by_product_and_retailer(
        self, product_id: str, retailer_id: str
    ) -> StockSubscription | None:
        for sub in self._subscriptions.values():
            if sub.product_id == product_id and sub.retailer_id == retailer_id:
                return sub
        return None

    def list_active_for_product(self, product_id: str) -> list[StockSubscription]:
        return [
            s
            for s in self._subscriptions.values()
            if s.product_id == product_id and s.is_active
        ]

    def list_for_product(self, product_id: str) -> list[StockSubscription]:
        return [s for s in self._subscriptions.values() if s.product_id == product_id]

    def list_for_retailer(self, retailer_id: str) -> list[StockSubscription]:
        return [s for s in self._subscriptions.values() if s.retailer_id == retailer_id]

    def count_active_for_retailer(self, retailer_id: str) -> int:
        return sum(
            1
            for s in self._subscriptions.values()
            if s.retailer_id == retailer_id and s.is_active
        )

    def count_active_by_retailers(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for s in self._subscriptions.values():
            if s.is_active:
                counts[s.retailer_id] = counts.get(s.retailer_id, 0) + 1
        return counts

    def create(self, subscription: StockSubscription) -> StockSubscription:
        from datetime import UTC, datetime
        if not subscription.id:
            subscription.id = str(uuid.uuid4())
        if not getattr(subscription, "created_at", None):
            subscription.created_at = datetime.now(UTC)
        self._subscriptions[subscription.id] = subscription
        return subscription

    def update(self, subscription: StockSubscription) -> StockSubscription:
        self._subscriptions[subscription.id] = subscription
        return subscription

    def delete(self, subscription_id: str) -> bool:
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            return True
        return False
