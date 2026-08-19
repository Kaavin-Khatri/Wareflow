"""Overdue unpaid invoice alert rule implementation."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.models.billing import InvoiceStatusEnum
from app.services.alert_rules.base import AlertEvaluationContext, AlertResult, BaseAlertRule


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to read attributes safely from ORM models or dicts."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class OverdueInvoiceRule(BaseAlertRule):
    """
    Fires an alert when an unpaid or partially-paid invoice has crossed its due date.
    """

    @property
    def rule_name(self) -> str:
        return "overdue_invoice"

    def evaluate(self, context: AlertEvaluationContext) -> list[AlertResult]:
        results: list[AlertResult] = []
        if not context.invoice_repo:
            return results

        now = datetime.now(UTC)
        today = now.date()

        invoices = context.invoice_repo.list_overdue_candidates(now)
        for invoice in invoices:
            res = self._check_invoice(invoice, today, context)
            if res:
                results.append(res)
        return results

    def _check_invoice(
        self, invoice: Any, today: date, context: AlertEvaluationContext
    ) -> AlertResult | None:
        status = _get_val(invoice, "status")
        if status in (InvoiceStatusEnum.PAID, "paid", "cancelled"):
            return None

        total_amount = float(_get_val(invoice, "total_amount", 0.0) or 0.0)
        paid_amount = float(_get_val(invoice, "paid_amount", 0.0) or 0.0)
        amount_due = round(total_amount - paid_amount, 2)
        if amount_due <= 0:
            return None

        # Look up due_date directly or fall back to invoice_date + default 15-day credit period
        due_date_raw = _get_val(invoice, "due_date")
        if not due_date_raw:
            invoice_date = _get_val(invoice, "invoice_date")
            if invoice_date:
                inv_dt = invoice_date.date() if isinstance(invoice_date, datetime) else invoice_date
                due_date_raw = inv_dt + timedelta(days=15)
            else:
                return None

        if isinstance(due_date_raw, datetime):
            due_date = due_date_raw.date()
        else:
            due_date = due_date_raw

        if due_date >= today:
            return None

        days_overdue = (today - due_date).days
        invoice_id = str(_get_val(invoice, "id"))
        invoice_no = _get_val(invoice, "invoice_no") or _get_val(invoice, "invoice_number", invoice_id)

        retailer_id = str(_get_val(invoice, "retailer_id") or "")
        retailer_name = "Retailer"

        sales_order = _get_val(invoice, "sales_order")
        if sales_order:
            if not retailer_id:
                retailer_id = str(_get_val(sales_order, "retailer_id") or "")
            so_retailer = _get_val(sales_order, "retailer")
            if so_retailer:
                retailer_name = str(_get_val(so_retailer, "name", retailer_name))

        if context.retailer_repo and retailer_id and retailer_name == "Retailer":
            ret = context.retailer_repo.get_by_id(retailer_id)
            if ret:
                retailer_name = str(_get_val(ret, "name", retailer_name))

        title = f"Overdue Invoice Alert: #{invoice_no} ({retailer_name})"
        body = (
            f"Invoice #{invoice_no} for '{retailer_name}' is {days_overdue} days OVERDUE "
            f"(due {due_date}). Outstanding balance: ₹{amount_due:,.2f}."
        )

        return AlertResult(
            rule_name=self.rule_name,
            entity_type="invoice",
            entity_id=invoice_id,
            alert_type="overdue_invoice",
            title=title,
            body=body,
            metadata={
                "invoice_id": invoice_id,
                "invoice_number": invoice_no,
                "retailer_id": retailer_id,
                "retailer_name": retailer_name,
                "amount_due": amount_due,
                "days_overdue": days_overdue,
                "due_date": str(due_date),
                "link": f"/admin/retailers/{retailer_id}/ledger" if retailer_id else "/admin/invoices",
            },
            target_permissions=["orders:view"],
            target_roles=["Admin", "Manager"],
        )
