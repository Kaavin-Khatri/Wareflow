"""Statistical Anomaly Detection Service for Sales Order line items.

Flags unusual order quantities exceeding mean + 3*stddev of that buyer's historical orders.
Advisory only — non-blocking.
"""

import math
from datetime import UTC, datetime
from typing import Any

from app.models.retailer import SalesOrder
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.schemas.analytics import ItemAnomalyReport, OrderAnomalyReportResponse


class AnomalyDetectionService:
    """Service evaluating sales order quantities against historical ordering patterns."""

    def __init__(
        self,
        so_repo: SalesOrderRepositoryInterface,
        stddev_multiplier: float = 3.0,
    ):
        self.so_repo = so_repo
        self.stddev_multiplier = float(stddev_multiplier)

    def evaluate_line_item(
        self,
        product_id: str,
        qty: float,
        retailer_id: str | None = None,
        customer_id: str | None = None,
        exclude_order_id: str | None = None,
        product_name: str | None = None,
        product_sku: str | None = None,
    ) -> ItemAnomalyReport:
        """Evaluate a single product line item against historical buyer order quantities."""
        qty = float(qty)
        history = self.so_repo.get_historical_order_quantities(
            product_id=product_id,
            retailer_id=retailer_id,
            customer_id=customer_id,
            exclude_order_id=exclude_order_id,
        )

        n = len(history)

        # Case 1: No prior history — cannot compute statistical deviation
        if n == 0:
            return ItemAnomalyReport(
                product_id=product_id,
                product_name=product_name,
                product_sku=product_sku,
                qty=qty,
                is_unusual=False,
                threshold=None,
                historical_mean=None,
                historical_stddev=None,
                sample_count=0,
                anomaly_reason=None,
            )

        # Case 2: Exactly 1 prior order — limited baseline
        if n == 1:
            prev_qty = history[0]
            # Flag if new order is > 3x larger than previous single order
            threshold = prev_qty * self.stddev_multiplier
            is_unusual = qty > threshold and qty > 10.0
            reason = (
                f"Quantity {qty:g} is >{self.stddev_multiplier:g}x larger than previous order ({prev_qty:g})."
                if is_unusual
                else None
            )
            return ItemAnomalyReport(
                product_id=product_id,
                product_name=product_name,
                product_sku=product_sku,
                qty=qty,
                is_unusual=is_unusual,
                threshold=round(threshold, 2),
                historical_mean=round(prev_qty, 2),
                historical_stddev=0.0,
                sample_count=1,
                anomaly_reason=reason,
            )

        # Case 3: 2 or more historical orders — compute sample mean & stddev
        mean = sum(history) / n
        sample_variance = sum((x - mean) ** 2 for x in history) / (n - 1)
        stddev = math.sqrt(max(sample_variance, 0.0))

        # Handle zero variance (buyer always orders the exact same quantity)
        if stddev < 1e-6:
            threshold = max(mean * self.stddev_multiplier, mean + 10.0)
            is_unusual = qty > threshold
            reason = (
                f"Quantity {qty:g} deviates from constant historical order of {mean:g} units (threshold {threshold:g})."
                if is_unusual
                else None
            )
            return ItemAnomalyReport(
                product_id=product_id,
                product_name=product_name,
                product_sku=product_sku,
                qty=qty,
                is_unusual=is_unusual,
                threshold=round(threshold, 2),
                historical_mean=round(mean, 2),
                historical_stddev=0.0,
                sample_count=n,
                anomaly_reason=reason,
            )

        # Standard normal statistical threshold: mean + 3*stddev
        threshold = mean + (self.stddev_multiplier * stddev)
        is_unusual = qty > threshold
        reason = (
            f"Quantity {qty:g} exceeds normal 3σ threshold ({threshold:.1f}). "
            f"Historical mean: {mean:.1f} ± {self.stddev_multiplier * stddev:.1f} "
            f"(stddev: {stddev:.1f}, {n} past orders)."
            if is_unusual
            else None
        )

        return ItemAnomalyReport(
            product_id=product_id,
            product_name=product_name,
            product_sku=product_sku,
            qty=qty,
            is_unusual=is_unusual,
            threshold=round(threshold, 2),
            historical_mean=round(mean, 2),
            historical_stddev=round(stddev, 2),
            sample_count=n,
            anomaly_reason=reason,
        )

    def evaluate_order(self, order: SalesOrder | Any) -> OrderAnomalyReportResponse:
        """Evaluate all line items of a sales order for anomalies."""
        order_id = getattr(order, "id", "")
        so_number = getattr(order, "so_number", "")
        retailer_id = getattr(order, "retailer_id", None)
        customer_id = getattr(order, "customer_id", None)

        buyer_name = None
        if getattr(order, "retailer", None):
            buyer_name = order.retailer.name
        elif getattr(order, "customer", None):
            buyer_name = order.customer.name

        item_reports: list[ItemAnomalyReport] = []
        for item in getattr(order, "items", []):
            p_id = getattr(item, "product_id", None)
            qty = getattr(item, "qty", 0.0)
            p_name = item.product.name if getattr(item, "product", None) else None
            p_sku = item.product.sku if getattr(item, "product", None) else None

            report = self.evaluate_line_item(
                product_id=p_id,
                qty=qty,
                retailer_id=retailer_id,
                customer_id=customer_id,
                exclude_order_id=order_id,
                product_name=p_name,
                product_sku=p_sku,
            )
            item_reports.append(report)

        unusual_items = [it for it in item_reports if it.is_unusual]

        return OrderAnomalyReportResponse(
            order_id=order_id,
            so_number=so_number,
            buyer_name=buyer_name,
            has_unusual_items=len(unusual_items) > 0,
            unusual_items_count=len(unusual_items),
            items=item_reports,
            evaluated_at=datetime.now(UTC),
        )

    def detect_anomalies_for_order_id(self, order_id: str) -> OrderAnomalyReportResponse | None:
        """Fetch order and evaluate anomalies."""
        order = self.so_repo.get_by_id(order_id)
        if not order:
            return None
        return self.evaluate_order(order)
