"""Invoice repository interface protocol following DIP."""

from datetime import datetime
from typing import Protocol

from app.models.billing import Invoice, InvoiceItem


class InvoiceRepositoryInterface(Protocol):
    """Protocol contract for Invoice data access."""

    def get_by_id(self, invoice_id: str) -> Invoice | None:
        """Fetch an invoice by primary key ID."""
        ...

    def get_by_sales_order_id(self, sales_order_id: str) -> Invoice | None:
        """Fetch an invoice created for a specific sales order."""
        ...

    def get_next_invoice_number(self, financial_year: str) -> str:
        """
        Generate the next sequential invoice number for a financial year.

        Format: INV/{financial_year}/{seq:04d} (e.g. INV/2026-27/0001)
        """
        ...

    def create_invoice(self, invoice: Invoice, items: list[InvoiceItem]) -> Invoice:
        """Persist a new invoice with its frozen line items atomically."""
        ...

    def update_invoice(self, invoice: Invoice) -> Invoice:
        """Update an existing invoice's status or metadata."""
        ...

    def list_by_retailer_id(self, retailer_id: str) -> list[Invoice]:
        """Fetch all invoices issued to a specific retailer."""
        ...

    def list_overdue_candidates(self, cutoff_date: datetime) -> list[Invoice]:
        """Fetch unpaid or partially-paid invoices created before cutoff_date."""
        ...

    def list_invoices(
        self,
        retailer_id: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Invoice], int]:
        """Fetch paginated, filterable invoice records."""
        ...


