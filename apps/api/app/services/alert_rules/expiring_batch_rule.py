"""Expiring inventory batch alert rule implementation."""

from datetime import UTC, date, datetime
from typing import Any

from app.services.alert_rules.base import AlertEvaluationContext, AlertResult, BaseAlertRule


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to read attributes safely from ORM models or dicts."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class ExpiringBatchRule(BaseAlertRule):
    """
    Fires an alert when an active stock batch has positive inventory and is
    approaching its expiration date within a threshold window (e.g. <= 30 days).
    """

    def __init__(self, threshold_days: int = 30) -> None:
        self.threshold_days = threshold_days

    @property
    def rule_name(self) -> str:
        return "expiring_batch"

    def evaluate(self, context: AlertEvaluationContext) -> list[AlertResult]:
        results: list[AlertResult] = []
        if not context.stock_repo:
            return results

        expiring_batches = context.stock_repo.get_batches_expiring_soon(days=self.threshold_days)
        today = datetime.now(UTC).date()

        for batch in expiring_batches:
            res = self._check_batch(batch, today, context)
            if res:
                results.append(res)
        return results

    def _check_batch(
        self, batch: Any, today: date, context: AlertEvaluationContext
    ) -> AlertResult | None:
        qty = float(_get_val(batch, "quantity", 0.0) or 0.0)
        if qty <= 0:
            return None

        expiry_date = _get_val(batch, "expiry_date")
        if not expiry_date:
            return None

        exp_date = (
            expiry_date.date()
            if isinstance(expiry_date, datetime)
            else expiry_date
        )

        days_remaining = (exp_date - today).days
        if days_remaining > self.threshold_days:
            return None

        batch_id = str(_get_val(batch, "id"))
        batch_no = _get_val(batch, "batch_no") or _get_val(batch, "batch_number", "Unknown")
        product_id = str(_get_val(batch, "product_id"))

        product_name = "Product"
        if context.product_repo:
            prod = context.product_repo.get_by_id(product_id)
            if prod:
                product_name = str(_get_val(prod, "name", product_name))

        if days_remaining <= 0:
            title = f"EXPIRED BATCH: {product_name} (Batch #{batch_no})"
            body = (
                f"Batch #{batch_no} of '{product_name}' ({qty:g} units) has EXPIRED on {exp_date}. "
                f"Immediate quarantine or write-off required under FSSAI compliance."
            )
        else:
            title = f"Expiring Batch Alert: {product_name} (Batch #{batch_no})"
            body = (
                f"Batch #{batch_no} of '{product_name}' ({qty:g} units) will expire in "
                f"{days_remaining} days (on {exp_date}). Priority dispatch / discounting advised."
            )

        return AlertResult(
            rule_name=self.rule_name,
            entity_type="batch",
            entity_id=batch_id,
            alert_type="expiring_batch",
            title=title,
            body=body,
            metadata={
                "batch_id": batch_id,
                "batch_number": batch_no,
                "product_id": product_id,
                "product_name": product_name,
                "quantity": qty,
                "expiry_date": str(exp_date),
                "days_remaining": days_remaining,
                "link": "/admin/stock/ledger",
            },
            target_permissions=["inventory:view"],
            target_roles=["Admin", "Manager", "Inventory Officer"],
        )
