"""Repository interface protocol for Payment records."""

from typing import Protocol, runtime_checkable

from app.models.billing import Payment


@runtime_checkable
class PaymentRepositoryInterface(Protocol):
    """Protocol for recording and querying customer/retailer invoice payments."""

    def create(self, payment: Payment) -> Payment:
        """Persist a new payment transaction."""
        ...

    def get_by_id(self, payment_id: str) -> Payment | None:
        """Fetch payment by unique ID."""
        ...

    def list_by_invoice_id(self, invoice_id: str) -> list[Payment]:
        """Fetch all payments recorded against a specific invoice."""
        ...

    def list_by_retailer_id(self, retailer_id: str) -> list[Payment]:
        """Fetch all payments received from a specific retailer."""
        ...

    def get_total_paid_for_invoice(self, invoice_id: str) -> float:
        """Calculate cumulative amount paid against an invoice."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> tuple[list[Payment], int]:
        """List all payments with pagination."""
        ...
