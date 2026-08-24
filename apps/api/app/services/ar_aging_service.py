"""Accounts-Receivable (AR) Aging Service (Step 15.2).

Calculates bucketed accounts-receivable aging (Current, 1-30, 31-60, 61-90, 90+ days)
across wholesale retailers from live invoices and payments against the reference date.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.models.billing import InvoiceStatusEnum
from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface
from app.repositories.interfaces.retailer_repository import RetailerRepository
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.schemas.analytics import (
    ARAgingBucketItem,
    ARAgingReportResponse,
    ARAgingSummary,
)


class ARAgingService:
    """Computes Accounts-Receivable aging reports and risk distributions across retailers."""

    def __init__(
        self,
        invoice_repository: InvoiceRepositoryInterface,
        retailer_repository: RetailerRepository,
        sales_order_repository: SalesOrderRepositoryInterface | None = None,
    ) -> None:
        self._invoice_repo = invoice_repository
        self._retailer_repo = retailer_repository
        self._sales_order_repo = sales_order_repository

    def get_ar_aging_report(
        self,
        include_zero_balance: bool = True,
        as_of: date | None = None,
    ) -> ARAgingReportResponse:
        """
        Compile AR aging report grouped by wholesale retailer into 30/60/90-day buckets.

        Buckets:
        - Current: Due in future or on today's date (days_overdue <= 0)
        - 1-30 Days: 1 <= days_overdue <= 30
        - 31-60 Days: 31 <= days_overdue <= 60
        - 61-90 Days: 61 <= days_overdue <= 90
        - 90+ Days: days_overdue >= 91 (Critical collection risk)
        """
        today = as_of or datetime.now(UTC).date()

        # 1. Fetch all wholesale retailers
        try:
            retailers = self._retailer_repo.list_all(limit=5000)
        except Exception:
            retailers = []

        retailer_data: dict[str, dict[str, Any]] = {}
        for r in retailers:
            r_id = str(r.id)
            retailer_data[r_id] = {
                "retailer_id": r_id,
                "retailer_name": str(r.name),
                "contact_person": getattr(r, "contact_person", None),
                "phone": getattr(r, "phone", None),
                "credit_limit": float(getattr(r, "credit_limit", 0.0) or 0.0),
                "credit_balance": float(getattr(r, "credit_balance", 0.0) or 0.0),
                "current": 0.0,
                "bucket_1_30": 0.0,
                "bucket_31_60": 0.0,
                "bucket_61_90": 0.0,
                "bucket_90_plus": 0.0,
                "oldest_invoice_date": None,
                "invoice_count": 0,
            }

        # 2. Fetch all invoices
        try:
            invoices, _ = self._invoice_repo.list_invoices(page=1, page_size=10000)
        except Exception:
            invoices = []

        # 3. Categorize unpaid/partially-paid balances into aging buckets
        for inv in invoices:
            inv_st = (
                inv.status.value.lower()
                if hasattr(inv.status, "value")
                else str(inv.status).lower()
            )
            if inv_st in ("cancelled", "void"):
                continue

            # Calculate remaining unpaid balance
            paid_amt = (
                float(inv.paid_amount)
                if hasattr(inv, "paid_amount") and inv.paid_amount is not None
                else sum(float(getattr(p, "amount", 0.0) or 0.0) for p in getattr(inv, "payments", []))
            )
            balance = float(inv.total_amount or 0.0) - paid_amt

            if balance <= 0.001 or inv_st in ("paid", InvoiceStatusEnum.PAID.value.lower()):
                continue

            # Resolve retailer ID
            ret_id: str | None = None
            so = getattr(inv, "sales_order", None)
            if so and getattr(so, "retailer_id", None):
                ret_id = str(so.retailer_id)
            elif hasattr(inv, "retailer_id") and inv.retailer_id:
                ret_id = str(inv.retailer_id)
            elif getattr(inv, "sales_order_id", None):
                if self._sales_order_repo:
                    try:
                        fetched_so = self._sales_order_repo.get_by_id(inv.sales_order_id)
                        if fetched_so and getattr(fetched_so, "retailer_id", None):
                            ret_id = str(fetched_so.retailer_id)
                    except Exception:
                        pass
                if not ret_id and hasattr(self._invoice_repo, "_sales_orders"):
                    in_mem_so = getattr(self._invoice_repo, "_sales_orders", {}).get(inv.sales_order_id)
                    if in_mem_so and getattr(in_mem_so, "retailer_id", None):
                        ret_id = str(in_mem_so.retailer_id)

            if not ret_id:
                # Direct customer invoice without retailer linkage
                continue

            if ret_id not in retailer_data:
                ret_name = (
                    getattr(getattr(so, "retailer", None), "name", None)
                    or getattr(inv, "retailer_name", None)
                    or "Wholesale Retailer"
                )
                retailer_data[ret_id] = {
                    "retailer_id": ret_id,
                    "retailer_name": str(ret_name),
                    "contact_person": None,
                    "phone": None,
                    "credit_limit": 0.0,
                    "credit_balance": 0.0,
                    "current": 0.0,
                    "bucket_1_30": 0.0,
                    "bucket_31_60": 0.0,
                    "bucket_61_90": 0.0,
                    "bucket_90_plus": 0.0,
                    "oldest_invoice_date": None,
                    "invoice_count": 0,
                }

            # Determine due date
            due_raw = getattr(inv, "due_date", None)
            if due_raw is None and hasattr(inv, "invoice_date") and inv.invoice_date:
                # Default wholesale terms: 30 days from invoice issuance
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

            days_overdue = (today - due_date_val).days if due_date_val else 0

            # Track invoice count and earliest invoice date
            retailer_data[ret_id]["invoice_count"] += 1
            inv_date_raw = getattr(inv, "invoice_date", None)
            if inv_date_raw:
                inv_date_iso = (
                    inv_date_raw.date().isoformat()
                    if isinstance(inv_date_raw, datetime)
                    else str(inv_date_raw)[:10]
                )
                curr_oldest = retailer_data[ret_id]["oldest_invoice_date"]
                if curr_oldest is None or inv_date_iso < curr_oldest:
                    retailer_data[ret_id]["oldest_invoice_date"] = inv_date_iso

            # Assign balance to appropriate aging bucket
            if days_overdue <= 0:
                retailer_data[ret_id]["current"] += balance
            elif 1 <= days_overdue <= 30:
                retailer_data[ret_id]["bucket_1_30"] += balance
            elif 31 <= days_overdue <= 60:
                retailer_data[ret_id]["bucket_31_60"] += balance
            elif 61 <= days_overdue <= 90:
                retailer_data[ret_id]["bucket_61_90"] += balance
            else:
                retailer_data[ret_id]["bucket_90_plus"] += balance

        # 4. Construct response items and portfolio summary totals
        summary = ARAgingSummary()
        retailer_items: list[ARAgingBucketItem] = []

        for r_id, r_info in retailer_data.items():
            curr = round(r_info["current"], 2)
            b1_30 = round(r_info["bucket_1_30"], 2)
            b31_60 = round(r_info["bucket_31_60"], 2)
            b61_90 = round(r_info["bucket_61_90"], 2)
            b90_p = round(r_info["bucket_90_plus"], 2)

            tot_overdue = round(b1_30 + b31_60 + b61_90 + b90_p, 2)
            tot_outstanding = round(curr + tot_overdue, 2)

            # Exclude zero balance retailers if requested
            if not include_zero_balance and tot_outstanding <= 0.001:
                continue

            item = ARAgingBucketItem(
                retailer_id=r_info["retailer_id"],
                retailer_name=r_info["retailer_name"],
                contact_person=r_info["contact_person"],
                phone=r_info["phone"],
                credit_limit=round(r_info["credit_limit"], 2),
                credit_balance=round(r_info["credit_balance"], 2),
                current=curr,
                bucket_1_30=b1_30,
                bucket_31_60=b31_60,
                bucket_61_90=b61_90,
                bucket_90_plus=b90_p,
                total_overdue=tot_overdue,
                total_outstanding=tot_outstanding,
                oldest_invoice_date=r_info["oldest_invoice_date"],
                invoice_count=r_info["invoice_count"],
            )
            retailer_items.append(item)

            summary.total_current += curr
            summary.total_bucket_1_30 += b1_30
            summary.total_bucket_31_60 += b31_60
            summary.total_bucket_61_90 += b61_90
            summary.total_bucket_90_plus += b90_p
            summary.total_overdue += tot_overdue
            summary.total_outstanding += tot_outstanding
            summary.total_retailers += 1
            if tot_overdue > 0.001:
                summary.overdue_retailers_count += 1

        summary.total_current = round(summary.total_current, 2)
        summary.total_bucket_1_30 = round(summary.total_bucket_1_30, 2)
        summary.total_bucket_31_60 = round(summary.total_bucket_31_60, 2)
        summary.total_bucket_61_90 = round(summary.total_bucket_61_90, 2)
        summary.total_bucket_90_plus = round(summary.total_bucket_90_plus, 2)
        summary.total_overdue = round(summary.total_overdue, 2)
        summary.total_outstanding = round(summary.total_outstanding, 2)

        # Sort descending by total overdue risk, then total outstanding
        retailer_items.sort(key=lambda x: (x.total_overdue, x.total_outstanding), reverse=True)

        return ARAgingReportResponse(
            as_of_date=today.isoformat(),
            summary=summary,
            retailers=retailer_items,
            generated_at=datetime.now(UTC),
        )
