"""Low-stock alert rule implementation."""

from typing import Any

from app.services.alert_rules.base import AlertEvaluationContext, AlertResult, BaseAlertRule


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to read attributes safely from ORM models or dicts."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class LowStockRule(BaseAlertRule):
    """
    Fires an alert when a product's available aggregate stock falls to or below
    its configured reorder point (but is still above critical / zero threshold).
    """

    @property
    def rule_name(self) -> str:
        return "low_stock"

    def evaluate(self, context: AlertEvaluationContext) -> list[AlertResult]:
        results: list[AlertResult] = []
        if not context.product_repo or not context.stock_repo:
            return results

        products = context.product_repo.list_products(limit=1000, is_active=True)
        for product in products:
            res = self._check_product(product, context)
            if res:
                results.append(res)
        return results

    def evaluate_entity(self, entity_id: str, context: AlertEvaluationContext) -> list[AlertResult]:
        if not context.product_repo or not context.stock_repo:
            return []
        product = context.product_repo.get_by_id(str(entity_id))
        if not product or not _get_val(product, "is_active", True):
            return []
        res = self._check_product(product, context)
        return [res] if res else []

    def _check_product(self, product: Any, context: AlertEvaluationContext) -> AlertResult | None:
        reorder_point = float(_get_val(product, "reorder_point", 0.0) or 0.0)
        if reorder_point <= 0:
            return None

        product_id = str(_get_val(product, "id"))
        current_stock = float(context.stock_repo.get_on_hand(product_id) or 0.0)

        # Critical stock (< 25% or 0) is handled by CriticalStockRule
        critical_threshold = 0.25 * reorder_point
        if current_stock <= critical_threshold:
            return None

        if current_stock <= reorder_point:
            name = str(_get_val(product, "name", "Product"))
            sku = str(_get_val(product, "sku", ""))
            base_uom = _get_val(product, "base_uom")
            uom_name = _get_val(base_uom, "name", "units") if base_uom else _get_val(product, "unit", "units")
            suggested_reorder_qty = float(
                _get_val(product, "reorder_qty")
                or _get_val(product, "reorder_quantity")
                or max(reorder_point * 2, 50.0)
            )

            title = f"Low Stock Alert: {name}"
            body = (
                f"Available balance ({current_stock:g} {uom_name}) has fallen to or below "
                f"reorder point ({reorder_point:g} {uom_name}). Suggested replenishment: "
                f"{suggested_reorder_qty:g} {uom_name}."
            )
            return AlertResult(
                rule_name=self.rule_name,
                entity_type="product",
                entity_id=product_id,
                alert_type="low_stock",
                title=title,
                body=body,
                metadata={
                    "product_id": product_id,
                    "sku": sku,
                    "current_stock": current_stock,
                    "reorder_point": reorder_point,
                    "suggested_reorder_qty": suggested_reorder_qty,
                    "link": "/admin/purchase-orders",
                },
                target_permissions=["inventory:view", "orders:create"],
                target_roles=["Admin", "Manager", "Inventory Officer", "Warehouse Staff"],
            )
        return None
