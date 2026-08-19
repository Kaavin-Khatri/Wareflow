"""Invoice domain service handling GST-ready invoice generation, snapshots, and idempotency."""

import math
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from app.core.security import CurrentUser

from app.models.billing import Invoice, InvoiceItem, InvoiceStatusEnum
from app.models.retailer import SalesOrder, SOStatusEnum
from app.repositories.interfaces.audit_repository import AuditRepository
from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface
from app.repositories.interfaces.payment_repository import PaymentRepositoryInterface
from app.repositories.interfaces.product_repository import ProductRepositoryInterface
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface
from app.schemas.invoices import (
    InvoiceItemResponse,
    InvoiceListItemResponse,
    InvoiceListResponse,
    InvoiceResponse,
)

LEGAL_INVOICE_STATUSES = {
    SOStatusEnum.CONFIRMED,
    SOStatusEnum.PACKED,
    SOStatusEnum.SHIPPED,
    SOStatusEnum.DELIVERED,
}


class InvoiceService:
    """Business logic service for invoicing."""

    def __init__(
        self,
        invoice_repo: InvoiceRepositoryInterface,
        sales_order_repo: SalesOrderRepositoryInterface,
        product_repo: ProductRepositoryInterface,
        audit_repo: AuditRepository | None = None,
        payment_repo: PaymentRepositoryInterface | None = None,
    ) -> None:
        self.invoice_repo = invoice_repo
        self.sales_order_repo = sales_order_repo
        self.product_repo = product_repo
        self.audit_repo = audit_repo
        self.payment_repo = payment_repo


    def get_financial_year(self, dt: datetime | None = None) -> str:
        """Calculate Indian Financial Year (April 1 - March 31)."""
        if dt is None:
            dt = datetime.now(UTC)
        if dt.month >= 4:
            start_year = dt.year
            end_year = (dt.year + 1) % 100
        else:
            start_year = dt.year - 1
            end_year = dt.year % 100
        return f"{start_year}-{end_year:02d}"

    def generate_invoice_for_sales_order(
        self,
        sales_order_id: str,
        current_user: CurrentUser | None = None,
    ) -> InvoiceResponse:
        """
        Generate a GST-ready tax invoice for a confirmed or later sales order.

        Idempotent: Re-requesting an invoice for an already-invoiced order returns the existing invoice.
        """
        # 1. Fetch sales order
        sales_order = self.sales_order_repo.get_by_id(sales_order_id)
        if not sales_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales Order '{sales_order_id}' not found.",
            )

        # 2. Status verification
        order_status_str = (
            sales_order.status.value
            if hasattr(sales_order.status, "value")
            else str(sales_order.status)
        )
        if order_status_str not in {
            s.value if hasattr(s, "value") else str(s) for s in LEGAL_INVOICE_STATUSES
        }:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invoices can only be generated for orders in confirmed or later status (current: {order_status_str}).",
            )

        # 3. Idempotency Check
        existing_invoice = self.invoice_repo.get_by_sales_order_id(sales_order_id)
        if existing_invoice:
            return self._build_invoice_response(existing_invoice, sales_order)

        # 4. Generate sequential invoice number
        now = datetime.now(UTC)
        fy = self.get_financial_year(now)
        invoice_no = self.invoice_repo.get_next_invoice_number(fy)

        # 5. Snapshot sales order items into frozen invoice items at current pricing
        invoice_id = str(uuid.uuid4())
        invoice_items: list[InvoiceItem] = []
        subtotal = 0.0
        tax_amount = 0.0

        for item in sales_order.items:
            product = self.product_repo.get_by_id(item.product_id)
            if isinstance(product, dict):
                product_name = product.get("name") or f"Product {item.product_id}"
                hsn_code = product.get("hsn_code") or "N/A"
            elif product:
                product_name = getattr(product, "name", None) or f"Product {item.product_id}"
                hsn_code = getattr(product, "hsn_code", None) or "N/A"
            else:
                product_name = f"Product {item.product_id}"
                hsn_code = "N/A"

            qty = float(item.qty)
            unit_price = float(item.unit_price)
            line_subtotal = round(qty * unit_price, 2)


            tax_rate = 18.00  # Default standard GST rate
            line_tax = round(line_subtotal * (tax_rate / 100.0), 2)
            line_total = round(line_subtotal + line_tax, 2)

            subtotal += line_subtotal
            tax_amount += line_tax

            invoice_items.append(
                InvoiceItem(
                    id=str(uuid.uuid4()),
                    invoice_id=invoice_id,
                    product_id=item.product_id,
                    product_name=product_name,
                    hsn_code=hsn_code,
                    qty=qty,
                    unit_price=unit_price,
                    tax_rate=tax_rate,
                    tax_amount=line_tax,
                    total=line_total,
                    uom_id=item.uom_id,
                )
            )

        total_amount = round(subtotal + tax_amount, 2)

        # 6. Create Invoice Entity
        invoice = Invoice(
            id=invoice_id,
            sales_order_id=sales_order_id,
            invoice_no=invoice_no,
            invoice_date=now,
            gst_rate=18.00,
            subtotal=round(subtotal, 2),
            tax_amount=round(tax_amount, 2),
            total_amount=total_amount,
            status=InvoiceStatusEnum.UNPAID,
            created_at=now,
        )

        persisted_invoice = self.invoice_repo.create_invoice(invoice, invoice_items)

        # 7. Audit log
        if self.audit_repo:
            actor_id = current_user.id if current_user else "system"
            self.audit_repo.create_log(
                actor_id=actor_id,
                action="invoice_generated",
                entity_type="invoice",
                entity_id=persisted_invoice.id,
                before_value=None,
                after_value={
                    "invoice_no": invoice_no,
                    "sales_order_id": sales_order_id,
                    "subtotal": subtotal,
                    "tax_amount": tax_amount,
                    "total_amount": total_amount,
                },
            )

        return self._build_invoice_response(persisted_invoice, sales_order)

    def get_invoice(self, invoice_id: str) -> InvoiceResponse:
        """Fetch invoice by primary ID with line items and buyer metadata."""
        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice '{invoice_id}' not found.",
            )
        return self._build_invoice_response(invoice, invoice.sales_order)

    def list_invoices(
        self,
        retailer_id: str | None = None,
        status_filter: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> InvoiceListResponse:
        """List paginated invoices with optional filters."""
        invoices, total = self.invoice_repo.list_invoices(
            retailer_id=retailer_id,
            status=status_filter,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )

        items: list[InvoiceListItemResponse] = []
        for inv in invoices:
            so = inv.sales_order
            buyer_name = "Direct Customer"
            buyer_type = "customer"
            if so:
                if getattr(so, "retailer", None):
                    buyer_name = so.retailer.name
                    buyer_type = "retailer"
                elif getattr(so, "customer", None):
                    buyer_name = so.customer.name
                    buyer_type = "customer"

            paid = 0.0
            if self.payment_repo:
                paid = self.payment_repo.get_total_paid_for_invoice(inv.id)
            outstanding = max(0.0, round(float(inv.total_amount) - paid, 2))

            items.append(
                InvoiceListItemResponse(
                    id=inv.id,
                    sales_order_id=inv.sales_order_id,
                    sales_order_number=getattr(so, "so_number", None) if so else None,
                    invoice_no=inv.invoice_no,
                    invoice_date=inv.invoice_date,
                    buyer_type=buyer_type,
                    buyer_name=buyer_name,
                    subtotal=float(inv.subtotal),
                    tax_amount=float(inv.tax_amount),
                    total_amount=float(inv.total_amount),
                    paid_amount=paid,
                    outstanding_balance=outstanding,
                    status=inv.status.value if hasattr(inv.status, "value") else str(inv.status),
                    items_count=len(inv.items) if hasattr(inv, "items") and inv.items else 0,
                    created_at=inv.created_at,
                )
            )

        pages = math.ceil(total / page_size) if total > 0 else 1
        return InvoiceListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def _build_invoice_response(
        self,
        invoice: Invoice,
        sales_order: SalesOrder | None = None,
    ) -> InvoiceResponse:
        """Helper to construct enriched InvoiceResponse."""
        so = sales_order or getattr(invoice, "sales_order", None)
        buyer_type = "retailer"
        buyer_id = None
        buyer_name = "Wholesale Retailer"
        buyer_gstin = None
        buyer_phone = None
        buyer_email = None
        buyer_address = None

        if so:
            if getattr(so, "retailer", None):
                buyer_type = "retailer"
                buyer_id = so.retailer.id
                buyer_name = so.retailer.name
                buyer_gstin = so.retailer.gstin
                buyer_phone = so.retailer.phone
                buyer_email = so.retailer.email
                buyer_address = so.retailer.address
            elif getattr(so, "customer", None):
                buyer_type = "customer"
                buyer_id = so.customer.id
                buyer_name = so.customer.name
                buyer_phone = so.customer.phone
                buyer_email = so.customer.email
                buyer_address = so.customer.address

        items_resp: list[InvoiceItemResponse] = []
        for item in getattr(invoice, "items", []) or []:
            items_resp.append(
                InvoiceItemResponse(
                    id=item.id,
                    invoice_id=item.invoice_id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    hsn_code=item.hsn_code,
                    qty=float(item.qty),
                    unit_price=float(item.unit_price),
                    tax_rate=float(item.tax_rate),
                    tax_amount=float(item.tax_amount),
                    total=float(item.total),
                    uom_id=item.uom_id,
                )
            )

        paid_amount = 0.0
        payment_list: list[dict[str, object]] = []
        if self.payment_repo:
            paid_amount = self.payment_repo.get_total_paid_for_invoice(invoice.id)
            payments = self.payment_repo.list_by_invoice_id(invoice.id)
            for p in payments:
                payment_list.append(
                    {
                        "id": p.id,
                        "amount": float(p.amount),
                        "method": str(p.method.value if hasattr(p.method, "value") else p.method),
                        "paid_at": p.paid_at.isoformat() if hasattr(p.paid_at, "isoformat") else str(p.paid_at),
                        "note": p.note,
                    }
                )

        outstanding_balance = max(0.0, round(float(invoice.total_amount) - paid_amount, 2))

        return InvoiceResponse(
            id=invoice.id,
            sales_order_id=invoice.sales_order_id,
            sales_order_number=getattr(so, "so_number", None) if so else None,
            buyer_type=buyer_type,
            buyer_id=buyer_id,
            buyer_name=buyer_name,
            buyer_gstin=buyer_gstin,
            buyer_phone=buyer_phone,
            buyer_email=buyer_email,
            buyer_address=buyer_address,
            invoice_no=invoice.invoice_no,
            invoice_date=invoice.invoice_date,
            gst_rate=float(invoice.gst_rate),
            subtotal=float(invoice.subtotal),
            tax_amount=float(invoice.tax_amount),
            total_amount=float(invoice.total_amount),
            paid_amount=paid_amount,
            outstanding_balance=outstanding_balance,
            status=invoice.status.value if hasattr(invoice.status, "value") else str(invoice.status),
            e_invoice_irn=invoice.e_invoice_irn,
            e_invoice_ack_no=invoice.e_invoice_ack_no,
            e_invoice_qr_code=invoice.e_invoice_qr_code,
            e_way_bill_no=invoice.e_way_bill_no,
            created_at=invoice.created_at,
            items=items_resp,
            payments=payment_list,
        )

