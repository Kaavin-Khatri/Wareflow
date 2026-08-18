"""Transfer repository interface contract (DIP)."""

from typing import Any, Protocol

from app.models.inventory import StockMovement
from app.models.warehouse import StockBatch


class TransferRepositoryInterface(Protocol):
    """Contract for atomic inter-warehouse stock transfers and transfer ledger queries."""

    def execute_transfer(
        self,
        product_id: str,
        batch_id: str,
        from_warehouse_id: str,
        to_warehouse_id: str,
        quantity: float,
        notes: str | None = None,
        created_by: str | None = None,
    ) -> tuple[str, StockBatch, StockBatch, StockMovement, StockMovement]:
        """
        Executes an atomic transfer within a single database transaction:
        - Decrements source batch quantity by `quantity`
        - Finds or creates destination batch in `to_warehouse_id` with matching batch_no and expiry_date
        - Increments destination batch quantity by `quantity`
        - Writes StockMovement(type=OUT, quantity=-quantity) at source
        - Writes StockMovement(type=IN, quantity=+quantity) at destination
        Returns (transfer_id, source_batch, dest_batch, out_movement, in_movement).
        """
        ...

    def list_transfers(
        self,
        page: int = 1,
        page_size: int = 50,
        product_id: str | None = None,
        from_warehouse_id: str | None = None,
        to_warehouse_id: str | None = None,
        start_date: Any | None = None,
        end_date: Any | None = None,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Fetch paginated historical inter-warehouse transfer records with joined metadata."""
        ...
