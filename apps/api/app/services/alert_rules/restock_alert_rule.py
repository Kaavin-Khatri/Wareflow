"""Restock alert rule strategy notifying subscribed retailers when stock is replenished (Step 13.4)."""

from datetime import UTC, datetime
import logging
from typing import Any

from app.models.portal import ChannelPreferenceEnum
from app.services.alert_rules.base import AlertEvaluationContext, AlertResult, BaseAlertRule

logger = logging.getLogger(__name__)


class RestockAlertRule(BaseAlertRule):
    """
    Evaluates standing retailer back-in-stock subscriptions.

    Triggered inline right after inbound stock movements (PO receiving, transfer-in, or return).
    Finds all is_active subscriptions for products that have crossed back above zero/reorder_point,
    dispatches wareflow_stock_available messages, and auto-deactivates the subscription to prevent spam.
    """

    @property
    def rule_name(self) -> str:
        return "restock_alert"

    def evaluate(self, context: AlertEvaluationContext) -> list[AlertResult]:
        """Evaluate restock subscriptions across all products."""
        if not context.stock_subscription_repo or not context.product_repo:
            return []

        if hasattr(context.product_repo, "list_products"):
            products = context.product_repo.list_products(limit=1000, is_active=True)
        elif hasattr(context.product_repo, "list_all"):
            products = context.product_repo.list_all()
        else:
            products = []

        results: list[AlertResult] = []
        for p in products:
            p_id = self._get_attr(p, "id")
            results.extend(self.evaluate_entity(p_id, context))

        return results

    def evaluate_entity(self, entity_id: str, context: AlertEvaluationContext) -> list[AlertResult]:
        """
        Evaluate restock subscriptions specifically for a single product.

        entity_id: product UUID
        """
        if not context.stock_subscription_repo or not context.product_repo:
            return []

        product = context.product_repo.get_by_id(entity_id)
        if not product:
            return []

        p_id = self._get_attr(product, "id")
        p_name = self._get_attr(product, "name") or "Product"
        uom = self._get_attr(product, "unit") or self._get_attr(product, "uom") or "units"
        reorder_point = float(self._get_attr(product, "reorder_point") or 0.0)

        # Check total on-hand stock
        current_stock = 0.0
        if context.stock_repo:
            if hasattr(context.stock_repo, "get_on_hand"):
                current_stock = float(context.stock_repo.get_on_hand(p_id) or 0.0)
            elif hasattr(context.stock_repo, "get_total_stock_for_product"):
                current_stock = float(context.stock_repo.get_total_stock_for_product(p_id) or 0.0)

        # Only trigger if product is in stock and replenished
        is_replenished = (current_stock > 0)

        if not is_replenished:
            return []

        # Find active subscriptions
        active_subs = context.stock_subscription_repo.list_active_for_product(p_id)
        if not active_subs:
            return []

        results: list[AlertResult] = []

        for sub in active_subs:
            sub_id = self._get_attr(sub, "id")
            retailer_id = self._get_attr(sub, "retailer_id")
            channel_pref = self._get_attr(sub, "channel_preference")

            retailer = None
            if context.retailer_repo:
                retailer = context.retailer_repo.get_by_id(retailer_id)

            retailer_name = self._get_attr(retailer, "business_name") if retailer else "Valued Retailer"
            retailer_email = self._get_attr(retailer, "email") if retailer else None
            retailer_phone = self._get_attr(retailer, "phone") if retailer else None
            user_id = self._get_attr(retailer, "id") or retailer_id

            # Determine notification channels
            channels: list[str] = ["in_app"]
            pref_str = channel_pref.value if hasattr(channel_pref, "value") else str(channel_pref).lower()
            if pref_str in ("whatsapp", "both"):
                channels.append("whatsapp")
            if pref_str in ("email", "both"):
                channels.append("email")

            title = f"Item Back in Stock: {p_name}"
            body = (
                f"{p_name} has been replenished and is now available for wholesale ordering "
                f"({current_stock:.0f} {uom} in stock)."
            )

            metadata = {
                "product_id": p_id,
                "product_name": p_name,
                "current_stock": current_stock,
                "uom": uom,
                "reorder_point": reorder_point,
                "retailer_id": retailer_id,
                "retailer_name": retailer_name,
                "link": f"/portal/catalog/{p_id}",
                "channel_preference": pref_str,
            }

            # Dispatch immediately via NotificationService if available
            if context.notification_service:
                try:
                    context.notification_service.notify(
                        user_id=user_id,
                        type="stock_available",
                        title=title,
                        body=body,
                        channels=channels,
                        recipient_email=retailer_email,
                        recipient_phone=retailer_phone,
                        metadata=metadata,
                    )
                    logger.info(
                        "Dispatched restock notification to retailer %s for product %s via %s",
                        retailer_id,
                        p_id,
                        channels,
                    )
                except Exception as exc:
                    logger.error("Failed to notify restock subscriber %s: %s", sub_id, exc)

            # Auto-deactivate subscription after fulfilling to prevent repeat spam
            if hasattr(sub, "notified_at"):
                sub.notified_at = datetime.now(UTC)
            if hasattr(sub, "is_active"):
                sub.is_active = False

            try:
                context.stock_subscription_repo.update(sub)
            except Exception as exc:
                logger.error("Failed to update fulfilled stock subscription %s: %s", sub_id, exc)

            results.append(
                AlertResult(
                    rule_name=self.rule_name,
                    entity_type="product",
                    entity_id=p_id,
                    alert_type="stock_available",
                    title=title,
                    body=body,
                    metadata=metadata,
                    target_permissions=["inventory:view", "portal:orders"],
                    target_roles=["Retailer", "Admin", "Manager"],
                )
            )

        return results

    @staticmethod
    def _get_attr(obj: Any, attr: str) -> Any:
        """Helper to get attributes from ORM models or dictionaries."""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get(attr)
        return getattr(obj, attr, None)
