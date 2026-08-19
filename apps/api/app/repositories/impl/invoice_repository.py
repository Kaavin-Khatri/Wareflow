"""SQLAlchemy and In-Memory implementations of InvoiceRepositoryInterface."""

import re
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.billing import Invoice, InvoiceItem
from app.models.retailer import SalesOrder
from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface


class SqlAlchemyInvoiceRepository(InvoiceRepositoryInterface):
    """PostgreSQL SQLAlchemy implementation of Invoice repository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, invoice_id: str) -> Invoice | None:
        """Fetch invoice with eagerly-loaded items and sales order."""
        stmt = (
            select(Invoice)
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.sales_order).selectinload(SalesOrder.retailer),
                selectinload(Invoice.sales_order).selectinload(SalesOrder.customer),
            )
            .where(Invoice.id == invoice_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_sales_order_id(self, sales_order_id: str) -> Invoice | None:
        """Fetch existing invoice by sales order ID for idempotent lookups."""
        stmt = (
            select(Invoice)
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.sales_order).selectinload(SalesOrder.retailer),
                selectinload(Invoice.sales_order).selectinload(SalesOrder.customer),
            )
            .where(Invoice.sales_order_id == sales_order_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_next_invoice_number(self, financial_year: str) -> str:
        """
        Generate next sequential gap-free invoice number for the financial year.

        Format: INV/{financial_year}/{seq:04d}
        """
        prefix = f"INV/{financial_year}/"
        stmt = select(Invoice.invoice_no).where(Invoice.invoice_no.like(f"{prefix}%"))
        results = self.session.execute(stmt).scalars().all()

        max_seq = 0
        pattern = re.compile(rf"^INV/{re.escape(financial_year)}/(\d+)$")
        for inv_no in results:
            match = pattern.match(inv_no)
            if match:
                try:
                    seq = int(match.group(1))
                    if seq > max_seq:
                        max_seq = seq
                except ValueError:
                    continue

        next_seq = max_seq + 1
        return f"{prefix}{next_seq:04d}"

    def create_invoice(self, invoice: Invoice, items: list[InvoiceItem]) -> Invoice:
        """Persist a new invoice with its frozen line items atomically."""
        self.session.add(invoice)
        for item in items:
            item.invoice_id = invoice.id
            self.session.add(item)
        self.session.flush()
        return invoice

    def update_invoice(
        self,
        invoice_or_id: Invoice | str,
        **kwargs: object,
    ) -> Invoice:
        """Update existing invoice state or specific fields."""
        if isinstance(invoice_or_id, str):
            inv = self.get_by_id(invoice_or_id)
            if not inv:
                raise ValueError(f"Invoice '{invoice_or_id}' not found.")
            for k, v in kwargs.items():
                if hasattr(inv, k):
                    setattr(inv, k, v)
            self.session.flush()
            return inv

        for k, v in kwargs.items():
            if hasattr(invoice_or_id, k):
                setattr(invoice_or_id, k, v)
        self.session.merge(invoice_or_id)
        self.session.flush()
        return invoice_or_id

    def list_by_retailer_id(self, retailer_id: str) -> list[Invoice]:
        """Fetch all invoices issued to a specific retailer chronologically."""
        stmt = (
            select(Invoice)
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.sales_order).selectinload(SalesOrder.retailer),
                selectinload(Invoice.sales_order).selectinload(SalesOrder.customer),
            )
            .join(Invoice.sales_order)
            .where(SalesOrder.retailer_id == retailer_id)
            .order_by(Invoice.invoice_date.asc(), Invoice.created_at.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_overdue_candidates(self, cutoff_date: datetime) -> list[Invoice]:
        """Fetch unpaid or partially-paid invoices created before cutoff_date."""
        stmt = (
            select(Invoice)
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.sales_order).selectinload(SalesOrder.retailer),
            )
            .where(
                Invoice.status.in_(["unpaid", "partially_paid"]),
                Invoice.invoice_date < cutoff_date,
            )
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_invoices(
        self,
        retailer_id: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Invoice], int]:
        """Fetch paginated, filterable invoice list."""
        query = select(Invoice).options(
            selectinload(Invoice.items),
            selectinload(Invoice.sales_order).selectinload(SalesOrder.retailer),
            selectinload(Invoice.sales_order).selectinload(SalesOrder.customer),
        )

        if retailer_id:
            query = query.join(Invoice.sales_order).where(SalesOrder.retailer_id == retailer_id)

        if status:
            query = query.where(Invoice.status == status)

        if start_date:
            query = query.where(Invoice.invoice_date >= start_date)

        if end_date:
            query = query.where(Invoice.invoice_date <= end_date)

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        total = self.session.execute(count_stmt).scalar_one()

        # Paginated results
        query = (
            query.order_by(desc(Invoice.created_at)).offset((page - 1) * page_size).limit(page_size)
        )
        items = list(self.session.execute(query).scalars().all())

        return items, total


class InMemoryInvoiceRepository(InvoiceRepositoryInterface):
    """In-Memory implementation of Invoice repository for fast hermetic unit testing."""

    def __init__(self) -> None:
        self._invoices: dict[str, Invoice] = {}
        self._items: dict[str, list[InvoiceItem]] = {}
        self._sales_orders: dict[str, SalesOrder] = {}

    def set_sales_order(self, sales_order: SalesOrder) -> None:
        """Helper to attach sales orders in tests."""
        self._sales_orders[sales_order.id] = sales_order

    def get_by_id(self, invoice_id: str) -> Invoice | None:
        inv = self._invoices.get(invoice_id)
        if inv and not hasattr(inv, "items"):
            inv.items = self._items.get(invoice_id, [])
        if inv and inv.sales_order_id and not hasattr(inv, "sales_order"):
            inv.sales_order = self._sales_orders.get(inv.sales_order_id)
        return inv

    def get_by_sales_order_id(self, sales_order_id: str) -> Invoice | None:
        for inv in self._invoices.values():
            if inv.sales_order_id == sales_order_id:
                if not hasattr(inv, "items"):
                    inv.items = self._items.get(inv.id, [])
                if not hasattr(inv, "sales_order"):
                    inv.sales_order = self._sales_orders.get(sales_order_id)
                return inv
        return None

    def get_next_invoice_number(self, financial_year: str) -> str:
        prefix = f"INV/{financial_year}/"
        pattern = re.compile(rf"^INV/{re.escape(financial_year)}/(\d+)$")
        max_seq = 0
        for inv in self._invoices.values():
            match = pattern.match(inv.invoice_no)
            if match:
                try:
                    seq = int(match.group(1))
                    if seq > max_seq:
                        max_seq = seq
                except ValueError:
                    continue
        return f"{prefix}{max_seq + 1:04d}"

    def create_invoice(self, invoice: Invoice, items: list[InvoiceItem]) -> Invoice:
        self._invoices[invoice.id] = invoice
        self._items[invoice.id] = items
        invoice.items = items
        if invoice.sales_order_id and invoice.sales_order_id in self._sales_orders:
            invoice.sales_order = self._sales_orders[invoice.sales_order_id]
        return invoice

    def update_invoice(
        self,
        invoice_or_id: Invoice | str,
        **kwargs: object,
    ) -> Invoice:
        """Update in-memory invoice state or specific fields."""
        if isinstance(invoice_or_id, str):
            inv = self._invoices.get(invoice_or_id)
            if not inv:
                raise ValueError(f"Invoice '{invoice_or_id}' not found.")
            for k, v in kwargs.items():
                setattr(inv, k, v)
            return inv

        for k, v in kwargs.items():
            setattr(invoice_or_id, k, v)
        self._invoices[invoice_or_id.id] = invoice_or_id
        return invoice_or_id

    def list_by_retailer_id(self, retailer_id: str) -> list[Invoice]:
        results = []
        for inv in self._invoices.values():
            if not hasattr(inv, "items"):
                inv.items = self._items.get(inv.id, [])
            if inv.sales_order_id and not hasattr(inv, "sales_order"):
                inv.sales_order = self._sales_orders.get(inv.sales_order_id)
            if (
                getattr(inv, "sales_order", None)
                and getattr(inv.sales_order, "retailer_id", None) == retailer_id
            ):
                results.append(inv)
        return sorted(
            results,
            key=lambda x: (
                getattr(x, "invoice_date", datetime.min),
                getattr(x, "created_at", datetime.min),
            ),
        )

    def list_overdue_candidates(self, cutoff_date: datetime) -> list[Invoice]:
        results = []
        for inv in self._invoices.values():
            if str(inv.status).lower() in ("unpaid", "partially_paid"):
                inv_date = inv.invoice_date
                if inv_date.tzinfo is not None and cutoff_date.tzinfo is None:
                    cutoff_cmp = cutoff_date.replace(tzinfo=inv_date.tzinfo)
                elif inv_date.tzinfo is None and cutoff_date.tzinfo is not None:
                    inv_date_cmp = inv_date.replace(tzinfo=cutoff_date.tzinfo)
                else:
                    inv_date_cmp = inv_date
                    cutoff_cmp = cutoff_date
                if inv_date_cmp < cutoff_cmp:
                    results.append(inv)
        return results

    def list_invoices(
        self,
        retailer_id: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Invoice], int]:

        results = list(self._invoices.values())

        if retailer_id:
            results = [
                inv
                for inv in results
                if getattr(inv, "sales_order", None)
                and getattr(inv.sales_order, "retailer_id", None) == retailer_id
            ]

        if status:
            results = [inv for inv in results if inv.status == status]

        if start_date:
            results = [inv for inv in results if inv.invoice_date >= start_date]

        if end_date:
            results = [inv for inv in results if inv.invoice_date <= end_date]

        total = len(results)
        sorted_results = sorted(
            results,
            key=lambda x: getattr(x, "created_at", datetime.now(UTC)),
            reverse=True,
        )
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = sorted_results[start_idx:end_idx]

        for inv in paginated:
            if not hasattr(inv, "items"):
                inv.items = self._items.get(inv.id, [])
            if inv.sales_order_id and not hasattr(inv, "sales_order"):
                inv.sales_order = self._sales_orders.get(inv.sales_order_id)

        return paginated, total
