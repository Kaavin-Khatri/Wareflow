"""Purchase Return repository interface protocol."""

from typing import Protocol

from app.models.returns import PurchaseReturn, PurchaseReturnStatusEnum


class PurchaseReturnRepositoryInterface(Protocol):
    """Data access contract for Purchase Returns (RMA Out)."""

    def create(
        self,
        purchase_order_id: str,
        supplier_id: str,
        reason: str | None,
        items: list[dict],
    ) -> PurchaseReturn:
        """Create a new PurchaseReturn with line items in requested status."""
        ...

    def get_by_id(self, return_id: str) -> PurchaseReturn | None:
        """Fetch purchase return by primary key ID with loaded items."""
        ...

    def list_all(
        self,
        supplier_id: str | None = None,
        status: PurchaseReturnStatusEnum | None = None,
        purchase_order_id: str | None = None,
    ) -> list[PurchaseReturn]:
        """List purchase returns matching optional filters."""
        ...

    def update_status(
        self,
        return_id: str,
        status: PurchaseReturnStatusEnum,
        credit_note_ref: str | None = None,
    ) -> PurchaseReturn | None:
        """Update return status and optional vendor credit note reference."""
        ...
