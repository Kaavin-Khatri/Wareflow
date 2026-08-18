"""Recall repository interface contract (DIP)."""

from typing import Any, Protocol

from app.models.recalls import BatchRecall, RecallAffectedOrder, RecallSeverityEnum


class RecallRepositoryInterface(Protocol):
    """Data access contract for Batch Recalls and Outbound Defect Traceability."""

    def create_recall(
        self,
        batch_id: str,
        product_id: str,
        reason: str,
        severity: RecallSeverityEnum = RecallSeverityEnum.MEDIUM,
    ) -> BatchRecall:
        """Persist a new batch recall in status INITIATED."""
        ...

    def find_affected_orders_by_batch(self, batch_id: str) -> list[dict[str, Any]]:
        """
        Traces every sales order that drew from the specified batch_id
        via outbound stock_movements(type=out, reference_type='sales_order').
        """
        ...

    def populate_affected_orders(
        self, recall_id: str, affected_orders_data: list[dict[str, Any]]
    ) -> list[RecallAffectedOrder]:
        """Atomically persist traced affected order records for a recall."""
        ...

    def get_recall_by_id(self, recall_id: str) -> BatchRecall | None:
        """Fetch single batch recall with joined product, batch, and affected orders."""
        ...

    def get_active_recall_for_batch(self, batch_id: str) -> BatchRecall | None:
        """Check if a batch currently has an active non-resolved recall."""
        ...

    def get_all_active_recalled_batch_ids(self) -> set[str]:
        """Retrieve set of all batch IDs currently under active recall."""
        ...

    def list_recalls(
        self,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
        severity: str | None = None,
        product_id: str | None = None,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Fetch paginated, filterable batch recall history with aggregate counts."""
        ...

    def mark_affected_orders_notified(self, recall_id: str) -> tuple[int, int]:
        """
        Broadcast timestamp update for all un-notified affected orders in a recall
        and transition recall status to NOTIFYING. Returns (retailers_count, customers_count).
        """
        ...

    def resolve_recall(self, recall_id: str) -> BatchRecall:
        """Mark a batch recall as RESOLVED and record resolved_at timestamp."""
        ...
