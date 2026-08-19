"""Domain service managing Retailer Restock Subscriptions (Step 13.4)."""

from datetime import UTC, datetime
import logging
from typing import Any
import uuid

from fastapi import HTTPException, status

from app.models.portal import ChannelPreferenceEnum, StockSubscription
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.stock_subscription_repository import (
    StockSubscriptionRepositoryInterface,
)
from app.schemas.stock_subscriptions import StockSubscriptionResponse

logger = logging.getLogger(__name__)


class StockSubscriptionService:
    """Service handling retailer back-in-stock alert subscriptions."""

    def __init__(
        self,
        subscription_repo: StockSubscriptionRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        retailer_repo: RetailerRepository,
    ) -> None:
        self.subscription_repo = subscription_repo
        self.product_repo = product_repo
        self.retailer_repo = retailer_repo

    def subscribe(
        self,
        product_id: str,
        retailer_id: str,
        channel_preference: ChannelPreferenceEnum | str = ChannelPreferenceEnum.BOTH,
    ) -> StockSubscriptionResponse:
        """
        Subscribe a retailer to restock alerts for a product.

        If a subscription already exists for (product_id, retailer_id), reactivates it
        with is_active=True and notified_at=None.
        """
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found.",
            )

        retailer = self.retailer_repo.get_by_id(retailer_id)
        if not retailer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retailer '{retailer_id}' not found.",
            )

        if isinstance(channel_preference, str):
            try:
                channel_pref_enum = ChannelPreferenceEnum(channel_preference.lower())
            except ValueError:
                channel_pref_enum = ChannelPreferenceEnum.BOTH
        else:
            channel_pref_enum = channel_preference

        existing = self.subscription_repo.get_by_product_and_retailer(
            product_id=product_id, retailer_id=retailer_id
        )

        if existing:
            existing.channel_preference = channel_pref_enum
            existing.is_active = True
            existing.notified_at = None
            saved = self.subscription_repo.update(existing)
            logger.info(
                "Reactivated stock subscription for product %s and retailer %s",
                product_id,
                retailer_id,
            )
        else:
            sub = StockSubscription(
                id=str(uuid.uuid4()),
                product_id=product_id,
                retailer_id=retailer_id,
                channel_preference=channel_pref_enum,
                is_active=True,
                created_at=datetime.now(UTC),
            )
            saved = self.subscription_repo.create(sub)
            logger.info(
                "Created new stock subscription %s for product %s and retailer %s",
                saved.id,
                product_id,
                retailer_id,
            )

        r_name = getattr(retailer, "name", None) or getattr(retailer, "business_name", None)
        return self._to_response(saved, product_name=product.name, retailer_name=r_name)

    def unsubscribe(self, product_id: str, retailer_id: str) -> bool:
        """Unsubscribe a retailer by deactivating their standing subscription."""
        existing = self.subscription_repo.get_by_product_and_retailer(
            product_id=product_id, retailer_id=retailer_id
        )
        if not existing or not existing.is_active:
            return True

        existing.is_active = False
        self.subscription_repo.update(existing)
        logger.info(
            "Deactivated stock subscription for product %s and retailer %s",
            product_id,
            retailer_id,
        )
        return True

    def list_subscribers_for_product(self, product_id: str) -> list[StockSubscriptionResponse]:
        """List active standing subscriptions for a product."""
        subs = self.subscription_repo.list_active_for_product(product_id)
        responses: list[StockSubscriptionResponse] = []
        for sub in subs:
            p_name = sub.product.name if getattr(sub, "product", None) else None
            r = getattr(sub, "retailer", None)
            r_name = (getattr(r, "name", None) or getattr(r, "business_name", None)) if r else None
            responses.append(self._to_response(sub, product_name=p_name, retailer_name=r_name))
        return responses

    def list_subscriptions_for_retailer(self, retailer_id: str) -> list[StockSubscriptionResponse]:
        """List subscriptions for a retailer."""
        subs = self.subscription_repo.list_for_retailer(retailer_id)
        responses: list[StockSubscriptionResponse] = []
        for sub in subs:
            p_name = sub.product.name if getattr(sub, "product", None) else None
            r = getattr(sub, "retailer", None)
            r_name = (getattr(r, "name", None) or getattr(r, "business_name", None)) if r else None
            responses.append(self._to_response(sub, product_name=p_name, retailer_name=r_name))
        return responses

    def get_retailer_subscription_counts(self) -> dict[str, int]:
        """Get mapping of retailer_id -> count of active subscriptions."""
        return self.subscription_repo.count_active_by_retailers()

    @staticmethod
    def _to_response(
        sub: StockSubscription,
        product_name: str | None = None,
        retailer_name: str | None = None,
    ) -> StockSubscriptionResponse:
        channel_val = (
            sub.channel_preference.value
            if hasattr(sub.channel_preference, "value")
            else str(sub.channel_preference)
        )
        r = getattr(sub, "retailer", None)
        derived_r_name = retailer_name or ((getattr(r, "name", None) or getattr(r, "business_name", None)) if r else None)
        return StockSubscriptionResponse(
            id=sub.id,
            retailer_id=sub.retailer_id,
            product_id=sub.product_id,
            product_name=product_name or (sub.product.name if getattr(sub, "product", None) else None),
            retailer_name=derived_r_name,
            channel_preference=channel_val,
            is_active=sub.is_active,
            created_at=sub.created_at or datetime.now(UTC),
            notified_at=sub.notified_at,
        )
