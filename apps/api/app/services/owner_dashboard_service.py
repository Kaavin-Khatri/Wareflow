"""Owner Analytics Dashboard Domain Service (Step 15.1).

Aggregates real-time wholesale operational metrics, 30-day inventory movement trendlines,
urgent low-stock and accounts-receivable aging quick lists, and weekly intelligence narratives
in a single efficient API round trip.
"""

from datetime import UTC, date, datetime, timedelta
import logging
from typing import Any

from app.models.billing import InvoiceStatusEnum
from app.models.supplier import POStatusEnum
from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.purchase_order_repository import PurchaseOrderRepositoryInterface
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.repositories.interfaces.stock_repository import StockRepositoryInterface
from app.repositories.interfaces.supplier_repository import SupplierRepositoryInterface
from app.schemas.analytics import (
    DashboardKPIMetrics,
    InboundOutboundDataPoint,
    LowStockQuickItem,
    OverdueInvoiceQuickItem,
    OwnerDashboardResponse,
    TopProductMovement,
)
from app.services.dead_stock_service import DeadStockService
from app.services.insight_narrator import InsightNarratorService

logger = logging.getLogger(__name__)


class OwnerDashboardService:
    """Domain service for single round-trip executive analytics dashboard aggregation."""

    def __init__(
        self,
        sales_order_repo: SalesOrderRepositoryInterface,
        stock_repo: StockRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        purchase_order_repo: PurchaseOrderRepositoryInterface,
        invoice_repo: InvoiceRepositoryInterface,
        dead_stock_service: DeadStockService,
        insight_narrator: InsightNarratorService,
        supplier_repo: SupplierRepositoryInterface | None = None,
    ) -> None:
        self._sales_order_repo = sales_order_repo
        self._stock_repo = stock_repo
        self._product_repo = product_repo
        self._purchase_order_repo = purchase_order_repo
        self._invoice_repo = invoice_repo
        self._dead_stock_service = dead_stock_service
        self._insight_narrator = insight_narrator
        self._supplier_repo = supplier_repo

    def get_owner_dashboard(self) -> OwnerDashboardResponse:
        """
        Synthesize real-time wholesale KPI metrics, 30-day movement series,
        fastest/dead inventory, and quick-action queues in one round trip.
        """
        now = datetime.now(UTC)
        today = now.date()
        month_start_date = date(now.year, now.month, 1)

        # 1. Fetch products & stock valuation
        active_products = self._get_active_products()
        product_map: dict[str, Any] = {}
        total_stock_value = 0.0
        monthly_inventory_units = 0.0
        low_stock_count = 0
        critical_stock_count = 0
        low_stock_candidates: list[dict[str, Any]] = []

        for prod in active_products:
            p_id = str(prod.get("id") if isinstance(prod, dict) else getattr(prod, "id", ""))
            p_name = str(prod.get("name") if isinstance(prod, dict) else getattr(prod, "name", "Product"))
            sku = str(prod.get("sku") if isinstance(prod, dict) else getattr(prod, "sku", "SKU"))
            reorder_point = float(
                prod.get("reorder_point", 0)
                if isinstance(prod, dict)
                else getattr(prod, "reorder_point", 0) or 0
            )
            cost_price = float(
                prod.get("cost_price", 0.0)
                if isinstance(prod, dict)
                else getattr(prod, "cost_price", 0.0) or 0.0
            )
            primary_supplier_id = (
                prod.get("primary_supplier_id")
                if isinstance(prod, dict)
                else getattr(prod, "primary_supplier_id", None)
            )

            product_map[p_id] = {
                "name": p_name,
                "sku": sku,
                "cost_price": cost_price,
                "reorder_point": reorder_point,
                "primary_supplier_id": primary_supplier_id,
                "category_name": (
                    prod.get("category", {}).get("name")
                    if isinstance(prod, dict) and isinstance(prod.get("category"), dict)
                    else getattr(getattr(prod, "category", None), "name", None)
                ),
            }

            try:
                on_hand = float(self._stock_repo.get_on_hand(p_id))
            except Exception:
                on_hand = 0.0

            monthly_inventory_units += on_hand
            total_stock_value += on_hand * cost_price

            if on_hand <= 0:
                critical_stock_count += 1
                low_stock_candidates.append(
                    {
                        "product_id": p_id,
                        "product_name": p_name,
                        "sku": sku,
                        "current_stock": on_hand,
                        "reorder_point": reorder_point,
                        "urgency": "critical",
                        "primary_supplier_id": primary_supplier_id,
                        "deficit": reorder_point - on_hand,
                    }
                )
            elif reorder_point > 0 and on_hand <= reorder_point:
                low_stock_count += 1
                urgency = "high" if on_hand <= (reorder_point / 2.0) else "medium"
                low_stock_candidates.append(
                    {
                        "product_id": p_id,
                        "product_name": p_name,
                        "sku": sku,
                        "current_stock": on_hand,
                        "reorder_point": reorder_point,
                        "urgency": urgency,
                        "primary_supplier_id": primary_supplier_id,
                        "deficit": reorder_point - on_hand,
                    }
                )

        # 2. Sales Orders & Monthly Revenue
        sales_orders, _ = self._sales_order_repo.list_all(limit=5000)
        monthly_sales_revenue = 0.0
        open_sos_count = 0
        product_sales_30d: dict[str, dict[str, float]] = {}
        thirty_days_ago = now - timedelta(days=30)

        for so in sales_orders:
            st = (
                so.status.value.lower()
                if hasattr(so.status, "value")
                else str(so.status).lower()
            )
            # Count open sales orders
            if st in ("draft", "confirmed", "packed", "shipped"):
                open_sos_count += 1

            # Monthly revenue from active/completed orders
            if st in ("confirmed", "packed", "shipped", "delivered"):
                so_dt = so.created_at or so.order_date
                if isinstance(so_dt, str):
                    try:
                        so_dt = datetime.fromisoformat(so_dt.replace("Z", "+00:00"))
                    except Exception:
                        so_dt = None

                if so_dt:
                    so_date = so_dt.date() if isinstance(so_dt, datetime) else so_dt
                    if so_date >= month_start_date:
                        monthly_sales_revenue += float(so.total_amount or 0.0)

                    if (
                        isinstance(so_dt, datetime)
                        and (so_dt if so_dt.tzinfo else so_dt.replace(tzinfo=UTC)) >= thirty_days_ago
                    ):
                        # Aggregate product sales volume
                        for item in getattr(so, "items", []):
                            prod_id = item.product_id
                            qty = float(item.qty or 0.0)
                            unit_p = float(getattr(item, "unit_price", 0.0) or 0.0)
                            line_rev = float(getattr(item, "line_total", None) or (qty * unit_p))
                            if prod_id not in product_sales_30d:
                                product_sales_30d[prod_id] = {"units": 0.0, "revenue": 0.0}
                            product_sales_30d[prod_id]["units"] += qty
                            product_sales_30d[prod_id]["revenue"] += line_rev

        # 3. Purchase Orders & Inbound Pipeline
        try:
            purchase_orders = self._purchase_order_repo.list_purchase_orders()
        except Exception:
            purchase_orders = []

        open_pos_count = 0
        for po in purchase_orders:
            po_status = (
                po.status.value.lower()
                if hasattr(po.status, "value")
                else str(po.status).lower()
            )
            if po_status in (
                POStatusEnum.DRAFT.value.lower(),
                POStatusEnum.ORDERED.value.lower(),
                POStatusEnum.READY_FOR_DISPATCH.value.lower(),
                POStatusEnum.PARTIALLY_RECEIVED.value.lower(),
                "draft",
                "ordered",
                "approved",
                "ready_for_dispatch",
                "partially_received",
            ):
                open_pos_count += 1

        # 4. Invoices, Receivables & Overdue Aging
        try:
            invoices, _ = self._invoice_repo.list_invoices(page=1, page_size=1000)
        except Exception:
            invoices = []

        total_outstanding_receivables = 0.0
        overdue_invoices_count = 0
        overdue_invoice_items: list[OverdueInvoiceQuickItem] = []

        for inv in invoices:
            inv_st = (
                inv.status.value.lower()
                if hasattr(inv.status, "value")
                else str(inv.status).lower()
            )
            if inv_st in ("cancelled", "void"):
                continue

            paid_amt = (
                float(inv.paid_amount)
                if hasattr(inv, "paid_amount") and inv.paid_amount is not None
                else sum(float(getattr(p, "amount", 0.0) or 0.0) for p in getattr(inv, "payments", []))
            )
            balance = float(inv.total_amount or 0.0) - paid_amt
            if balance > 0.001 and inv_st not in ("paid", InvoiceStatusEnum.PAID.value.lower()):
                total_outstanding_receivables += balance

                # Check overdue status
                due_raw = getattr(inv, "due_date", None)
                if due_raw is None and hasattr(inv, "invoice_date") and inv.invoice_date:
                    # Default credit terms: 30 days from invoice_date
                    inv_d = inv.invoice_date.date() if isinstance(inv.invoice_date, datetime) else inv.invoice_date
                    due_raw = inv_d + timedelta(days=30)

                due_date_val: date | None = None
                if isinstance(due_raw, datetime):
                    due_date_val = due_raw.date()
                elif isinstance(due_raw, date):
                    due_date_val = due_raw
                elif isinstance(due_raw, str):
                    try:
                        due_date_val = datetime.fromisoformat(due_raw[:10]).date()
                    except Exception:
                        due_date_val = None

                if due_date_val and (due_date_val < today or inv_st == "overdue"):
                    overdue_invoices_count += 1
                    overdue_days = max(0, (today - due_date_val).days)
                    ret_name = (
                        getattr(getattr(inv, "retailer", None), "name", None)
                        or getattr(inv, "retailer_name", None)
                        or "Wholesale Retailer"
                    )
                    inv_num = str(
                        getattr(inv, "invoice_number", None)
                        or getattr(inv, "invoice_no", None)
                        or getattr(inv, "id", "")
                    )
                    overdue_invoice_items.append(
                        OverdueInvoiceQuickItem(
                            invoice_id=str(inv.id),
                            invoice_number=inv_num,
                            retailer_name=str(ret_name),
                            due_date=due_date_val.isoformat(),
                            overdue_days=overdue_days,
                            balance_due=round(balance, 2),
                            status=inv_st,
                        )
                    )

        # Sort overdue invoices descending by days overdue
        overdue_invoice_items.sort(key=lambda x: x.overdue_days, reverse=True)

        # 5. Top 5 Fastest Moving Products
        top_fastest_moving: list[TopProductMovement] = []
        sorted_movers = sorted(
            product_sales_30d.items(),
            key=lambda item: item[1]["units"],
            reverse=True,
        )
        for prod_id, metrics in sorted_movers[:5]:
            prod_meta = product_map.get(prod_id, {})
            top_fastest_moving.append(
                TopProductMovement(
                    product_id=prod_id,
                    product_name=prod_meta.get("name", "Product"),
                    sku=prod_meta.get("sku", "SKU"),
                    category_name=prod_meta.get("category_name"),
                    units_moved=metrics["units"],
                    revenue=round(metrics["revenue"], 2),
                )
            )

        # 6. Top 5 Dead Stock
        top_dead_stock = []
        try:
            dead_stock_resp = self._dead_stock_service.get_dead_stock(window_days=90)
            top_dead_stock = dead_stock_resp.items[:5]
        except Exception as e:
            logger.warning("Failed to fetch dead stock for dashboard: %s", e)

        # 7. 30-Day Daily Movement Series (Inbound vs Outbound)
        movement_trend_30d = self._build_30d_movement_series(today)

        # 8. Low Stock Quick List with Supplier Names
        supplier_name_map = self._get_supplier_name_map()
        low_stock_quick_list: list[LowStockQuickItem] = []
        # Sort candidates: critical first, then highest deficit
        low_stock_candidates.sort(
            key=lambda c: (0 if c["urgency"] == "critical" else 1, -c["deficit"])
        )
        for cand in low_stock_candidates[:5]:
            supp_name = None
            if cand.get("primary_supplier_id"):
                supp_name = supplier_name_map.get(cand["primary_supplier_id"])
            low_stock_quick_list.append(
                LowStockQuickItem(
                    product_id=cand["product_id"],
                    product_name=cand["product_name"],
                    sku=cand["sku"],
                    current_stock=cand["current_stock"],
                    reorder_point=cand["reorder_point"],
                    urgency=cand["urgency"],
                    primary_supplier_name=supp_name,
                )
            )

        # 9. AI Weekly Executive Insight
        weekly_insight = None
        try:
            weekly_insight = self._insight_narrator.get_weekly_insight(force_refresh=False)
        except Exception as e:
            logger.warning("Failed to fetch weekly insight for dashboard: %s", e)

        # 10. Check Empty State
        is_empty_state = (
            len(active_products) == 0
            and len(sales_orders) == 0
            and len(purchase_orders) == 0
        )

        return OwnerDashboardResponse(
            kpi_metrics=DashboardKPIMetrics(
                monthly_sales_revenue=round(monthly_sales_revenue, 2),
                monthly_inventory_value=round(total_stock_value, 2),
                monthly_inventory_units=round(monthly_inventory_units, 2),
                total_stock_value=round(total_stock_value, 2),
                open_pos_count=open_pos_count,
                open_sos_count=open_sos_count,
                low_stock_count=low_stock_count,
                critical_stock_count=critical_stock_count,
                total_outstanding_receivables=round(total_outstanding_receivables, 2),
                overdue_invoices_count=overdue_invoices_count,
            ),
            top_fastest_moving=top_fastest_moving,
            top_dead_stock=top_dead_stock,
            movement_trend_30d=movement_trend_30d,
            low_stock_quick_list=low_stock_quick_list,
            overdue_invoices_quick_list=overdue_invoice_items[:5],
            weekly_insight=weekly_insight,
            is_empty_state=is_empty_state,
            generated_at=now,
        )

    def _get_active_products(self) -> list[Any]:
        """Fetch active products from product repository."""
        if hasattr(self._product_repo, "list_products"):
            return self._product_repo.list_products(limit=5000, is_active=True)
        products = self._product_repo.list()
        return [
            p
            for p in products
            if (p.get("is_active", True) if isinstance(p, dict) else getattr(p, "is_active", True))
        ]

    def _get_supplier_name_map(self) -> dict[str, str]:
        """Map supplier IDs to supplier company names."""
        if not self._supplier_repo:
            return {}
        try:
            suppliers = self._supplier_repo.list_suppliers(limit=1000)
            return {
                str(s.get("id") if isinstance(s, dict) else getattr(s, "id", "")): str(
                    (s.get("name") or s.get("company_name"))
                    if isinstance(s, dict)
                    else (getattr(s, "name", None) or getattr(s, "company_name", ""))
                )
                for s in suppliers
            }
        except Exception:
            return {}

    def _build_30d_movement_series(self, today: date) -> list[InboundOutboundDataPoint]:
        """Generate 30 consecutive daily datapoints aggregating inbound vs outbound stock movements."""
        start_date = today - timedelta(days=29)
        daily_buckets: dict[str, dict[str, float]] = {}

        # Initialize all 30 days with zeroed counts
        for i in range(30):
            d = (start_date + timedelta(days=i)).isoformat()
            daily_buckets[d] = {"inbound": 0.0, "outbound": 0.0}

        try:
            movements, _ = self._stock_repo.list_movements(
                page=1,
                page_size=5000,
                start_date=datetime.combine(start_date, datetime.min.time(), tzinfo=UTC),
            )
            for m in movements:
                m_dt = m.get("created_at")
                if isinstance(m_dt, datetime):
                    m_date_str = m_dt.date().isoformat()
                elif isinstance(m_dt, str):
                    m_date_str = m_dt[:10]
                else:
                    continue

                if m_date_str in daily_buckets:
                    raw_type = m.get("type") if m.get("type") is not None else m.get("movement_type", "")
                    m_type = str(raw_type.value if hasattr(raw_type, "value") else raw_type).lower()
                    qty = abs(float(m.get("quantity", 0.0)))
                    if m_type in ("in", "return_in"):
                        daily_buckets[m_date_str]["inbound"] += qty
                    elif m_type in ("out", "return_out"):
                        daily_buckets[m_date_str]["outbound"] += qty
        except Exception as e:
            logger.warning("Failed to fetch stock movements for 30d series: %s", e)

        return [
            InboundOutboundDataPoint(
                date=d_str,
                inbound_qty=round(counts["inbound"], 2),
                outbound_qty=round(counts["outbound"], 2),
            )
            for d_str, counts in sorted(daily_buckets.items())
        ]
