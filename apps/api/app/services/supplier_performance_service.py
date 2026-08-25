"""
Supplier Performance Analytics Service (Step 16.2).

Computes on-time delivery rates, fulfillment accuracy, return rates, and spend analytics per vendor.
Follows SOLID Principles:
- Single Responsibility: Calculates vendor reliability metrics and quality bands.
- Open/Closed: Extensible to SLA penalties and vendor scorecards.
- Dependency Inversion: Depends on repository interfaces.
"""

from datetime import UTC, datetime

from app.models.supplier import POStatusEnum
from app.repositories.interfaces.purchase_order_repository import PurchaseOrderRepositoryInterface
from app.repositories.interfaces.purchase_return_repository import PurchaseReturnRepositoryInterface
from app.repositories.interfaces.supplier_repository import SupplierRepositoryInterface
from app.schemas.analytics import (
    SupplierPerformanceItem,
    SupplierPerformanceResponse,
    SupplierPerformanceSummary,
)


class SupplierPerformanceService:
    """Service computing supplier fulfillment reliability, on-time rate, and return metrics."""

    def __init__(
        self,
        supplier_repo: SupplierRepositoryInterface,
        purchase_order_repo: PurchaseOrderRepositoryInterface,
        purchase_return_repo: PurchaseReturnRepositoryInterface,
    ) -> None:
        self.supplier_repo = supplier_repo
        self.purchase_order_repo = purchase_order_repo
        self.purchase_return_repo = purchase_return_repo

    def get_supplier_performance(
        self, as_of: datetime | None = None
    ) -> SupplierPerformanceResponse:
        """Calculate supplier performance scorecards across all active vendors."""
        now = as_of or datetime.now(UTC)

        if hasattr(self.supplier_repo, "list_suppliers"):
            suppliers = self.supplier_repo.list_suppliers(limit=1000)
        elif hasattr(self.supplier_repo, "list_all"):
            suppliers = self.supplier_repo.list_all(limit=1000)
        else:
            suppliers = []

        if hasattr(self.purchase_order_repo, "list_purchase_orders"):
            all_pos = self.purchase_order_repo.list_purchase_orders()
        elif hasattr(self.purchase_order_repo, "list_all"):
            all_pos = self.purchase_order_repo.list_all(limit=2000)
        else:
            all_pos = []

        all_returns = self.purchase_return_repo.list_all()

        # Group POs by supplier
        pos_by_supplier: dict[str, list] = {}
        for po in all_pos:
            s_id = po.supplier_id
            pos_by_supplier.setdefault(s_id, []).append(po)

        # Group Returns by supplier
        returns_by_supplier: dict[str, list] = {}
        for ret in all_returns:
            s_id = ret.supplier_id
            returns_by_supplier.setdefault(s_id, []).append(ret)

        items: list[SupplierPerformanceItem] = []
        total_spend_all = 0.0
        total_on_time_sum = 0.0
        total_accuracy_sum = 0.0
        total_return_rate_sum = 0.0
        active_supplier_count = 0
        excellent_count = 0
        needs_improvement_count = 0

        for sup in suppliers:
            s_id = sup.id
            sup_pos = pos_by_supplier.get(s_id, [])
            sup_returns = returns_by_supplier.get(s_id, [])

            total_pos_count = len(sup_pos)
            completed_pos = [
                po
                for po in sup_pos
                if po.status in (POStatusEnum.RECEIVED, POStatusEnum.PARTIALLY_RECEIVED)
                or str(po.status).lower() in ("received", "partially_received")
            ]

            # 1. On-Time Delivery Rate
            on_time_count = 0
            evaluated_on_time_pos = 0
            for po in completed_pos:
                if po.expected_date:
                    evaluated_on_time_pos += 1
                    # Check completion/receipt date (po.created_at or order_date)
                    receipt_date = (po.order_date or po.created_at).date()
                    if receipt_date <= po.expected_date:
                        on_time_count += 1
                else:
                    # No expected date set -> count as on-time standard
                    evaluated_on_time_pos += 1
                    on_time_count += 1

            on_time_pct = (
                round((on_time_count / evaluated_on_time_pos) * 100.0, 1)
                if evaluated_on_time_pos > 0
                else 100.0
            )

            # 2. Fulfillment Accuracy (Ordered vs Received across line items)
            total_qty_ordered = 0.0
            total_qty_received = 0.0
            total_spend = 0.0

            for po in sup_pos:
                if str(po.status).lower() not in ("cancelled", POStatusEnum.CANCELLED.value):
                    total_spend += float(po.total_amount)
                    for item in getattr(po, "items", []) or []:
                        total_qty_ordered += float(item.qty_ordered)
                        total_qty_received += float(item.qty_received)

            accuracy_pct = (
                round((total_qty_received / total_qty_ordered) * 100.0, 1)
                if total_qty_ordered > 0
                else 100.0
            )
            # Cap accuracy percentage at 100%
            accuracy_pct = min(accuracy_pct, 100.0)

            # 3. Return Rate (Returned quantity vs received quantity)
            total_returned_qty = 0.0
            for ret in sup_returns:
                for item in getattr(ret, "items", []) or []:
                    total_returned_qty += float(item.qty)

            return_rate_pct = (
                round((total_returned_qty / total_qty_received) * 100.0, 1)
                if total_qty_received > 0
                else 0.0
            )

            # 4. Rating Band
            # Excellent: On-time >= 90% and Accuracy >= 95% and Return Rate <= 2%
            # Good: On-time >= 75% and Accuracy >= 85% and Return Rate <= 5%
            # Needs Improvement: otherwise
            if on_time_pct >= 90.0 and accuracy_pct >= 95.0 and return_rate_pct <= 2.0:
                rating = "excellent"
                excellent_count += 1
            elif on_time_pct >= 75.0 and accuracy_pct >= 85.0 and return_rate_pct <= 5.0:
                rating = "good"
            else:
                rating = "needs_improvement"
                needs_improvement_count += 1

            total_spend_all += total_spend
            if total_pos_count > 0:
                total_on_time_sum += on_time_pct
                total_accuracy_sum += accuracy_pct
                total_return_rate_sum += return_rate_pct
                active_supplier_count += 1

            items.append(
                SupplierPerformanceItem(
                    supplier_id=s_id,
                    supplier_name=sup.name,
                    contact_person=sup.contact_person,
                    phone=sup.phone,
                    total_pos=total_pos_count,
                    completed_pos=len(completed_pos),
                    on_time_delivery_pct=on_time_pct,
                    fulfillment_accuracy_pct=accuracy_pct,
                    return_rate_pct=return_rate_pct,
                    total_spend_inr=round(total_spend, 2),
                    rating_band=rating,
                )
            )

        # Sort descending by total spend, secondary by on-time delivery
        items.sort(key=lambda x: (-x.total_spend_inr, -x.on_time_delivery_pct, x.supplier_name.lower()))

        avg_on_time = (
            round(total_on_time_sum / active_supplier_count, 1) if active_supplier_count > 0 else 100.0
        )
        avg_accuracy = (
            round(total_accuracy_sum / active_supplier_count, 1) if active_supplier_count > 0 else 100.0
        )
        avg_return = (
            round(total_return_rate_sum / active_supplier_count, 1) if active_supplier_count > 0 else 0.0
        )

        summary = SupplierPerformanceSummary(
            average_on_time_pct=avg_on_time,
            average_accuracy_pct=avg_accuracy,
            average_return_rate_pct=avg_return,
            total_spend_inr=round(total_spend_all, 2),
            total_suppliers_analyzed=len(suppliers),
            excellent_count=excellent_count,
            needs_improvement_count=needs_improvement_count,
        )

        return SupplierPerformanceResponse(
            summary=summary,
            items=items,
            generated_at=now,
        )
