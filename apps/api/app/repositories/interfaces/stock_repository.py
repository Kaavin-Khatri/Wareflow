"""Stock repository interface protocol."""

from typing import Any, Protocol

from app.models.catalog import Product
from app.models.warehouse import StockBatch, Warehouse


class StockRepositoryInterface(Protocol):
    """Data access contract for multi-warehouse inventory batches and stock balances."""

    def get_on_hand(self, product_id: str, warehouse_id: str | None = None) -> float:
        """Sum total available on-hand stock quantity (in base UoM) across all or specific warehouse."""
        ...

    def get_batches_by_product(
        self, product_id: str, warehouse_id: str | None = None
    ) -> list[StockBatch]:
        """Retrieve active stock batches for a product, ordered by FIFO (expiry/received date)."""
        ...

    def get_batches_expiring_soon(
        self, days: int = 30, warehouse_id: str | None = None
    ) -> list[StockBatch]:
        """Retrieve stock batches with quantity > 0 expiring within the specified day window."""
        ...

    def get_all_warehouses(self, active_only: bool = True) -> list[Warehouse]:
        """List all registered storage warehouses."""
        ...

    def get_warehouse_by_id(self, warehouse_id: str) -> Warehouse | None:
        """Get warehouse by primary key ID."""
        ...

    def get_stock_overview_data(
        self,
        warehouse_id: str | None = None,
        category_id: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch aggregated inventory read-model rows for all active products,
        including per-warehouse breakdown and stock batch summaries.
        """
        ...

    def get_product_with_base_uom(self, product_id: str) -> Product | None:
        """Fetch product record eagerly joined with base UoM details."""
        ...

    def get_batch_by_id(self, batch_id: str) -> StockBatch | None:
        """Fetch stock batch by primary key ID."""
        ...

    def record_stock_receipt(
        self,
        product_id: str,
        warehouse_id: str,
        batch_no: str,
        quantity: float,
        expiry_date: Any | None = None,
        reference_id: str | None = None,
        created_by: str | None = None,
    ) -> tuple[StockBatch, Any]:
        """
        Record inbound stock receipt atomically:
        - Upsert matching StockBatch row (FIFO/batch identity)
        - Insert an immutable StockMovement(type=in) ledger entry
        """
        ...

    def record_stock_return(
        self,
        batch_id: str,
        product_id: str,
        warehouse_id: str,
        quantity: float,
        reference_id: str | None = None,
        created_by: str | None = None,
    ) -> tuple[StockBatch, Any]:
        """
        Record outbound stock return to supplier atomically:
        - Deduct quantity from matching StockBatch
        - Insert an immutable StockMovement(type=return_out) ledger entry
        """
        ...

