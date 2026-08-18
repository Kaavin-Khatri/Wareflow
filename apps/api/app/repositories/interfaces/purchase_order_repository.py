"""Purchase order repository interface protocol."""

from typing import Any, Protocol

from app.models.supplier import POStatusEnum, PurchaseOrder, PurchaseOrderItem


class PurchaseOrderRepositoryInterface(Protocol):
    """Data access contract for purchase orders and line items."""

    def get_by_id(self, po_id: str) -> PurchaseOrder | None:
        """Fetch Purchase Order by primary key ID, eagerly joined with supplier and items."""
        ...

    def get_by_po_number(self, po_number: str) -> PurchaseOrder | None:
        """Fetch Purchase Order by unique PO number string."""
        ...

    def list_purchase_orders(
        self,
        supplier_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[PurchaseOrder]:
        """List purchase orders matching optional supplier, status, or search query."""
        ...

    def create_purchase_order(
        self, po_data: dict[str, Any], items_data: list[dict[str, Any]]
    ) -> PurchaseOrder:
        """Create a new Purchase Order along with its line items."""
        ...

    def update_purchase_order(
        self,
        po_id: str,
        po_data: dict[str, Any],
        items_data: list[dict[str, Any]] | None = None,
    ) -> PurchaseOrder | None:
        """Update an existing Purchase Order metadata and optionally replace line items."""
        ...

    def update_status(self, po_id: str, status: POStatusEnum) -> PurchaseOrder | None:
        """Update the status of a Purchase Order."""
        ...

    def update_item_received_qty(
        self, item_id: str, additional_qty: float
    ) -> PurchaseOrderItem | None:
        """Atomically increment the received quantity on a Purchase Order line item."""
        ...

    def generate_next_po_number(self) -> str:
        """Generate the next unique PO number string (e.g. PO-YYYYMM-XXXX)."""
        ...
