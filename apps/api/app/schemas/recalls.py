"""Pydantic schemas for Batch Recall and Defect Traceability (Step 9.3)."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.recalls import RecallSeverityEnum, RecallStatusEnum


class BatchRecallCreateRequest(BaseModel):
    """Payload for initiating a batch quality recall."""

    batch_id: str = Field(..., description="ID of the defective or contaminated stock batch")
    reason: str = Field(..., min_length=5, description="Root cause or defect description for the recall")
    severity: RecallSeverityEnum = Field(
        default=RecallSeverityEnum.MEDIUM,
        description="Severity classification (low, medium, critical)",
    )


class RecallAffectedOrderItemResponse(BaseModel):
    """Traced sales order and buyer affected by a batch recall."""

    id: str
    sales_order_id: str
    sales_order_number: str | None = None
    buyer_type: str = "retailer"
    buyer_id: str | None = None
    buyer_name: str
    buyer_phone: str | None = None
    buyer_email: str | None = None
    order_date: datetime | None = None
    quantity_supplied: float
    notified_at: datetime | None = None


class BatchRecallResponse(BaseModel):
    """Detailed batch recall entity with traced affected orders and buyer details."""

    id: str
    batch_id: str
    batch_no: str
    product_id: str
    product_name: str
    product_sku: str
    warehouse_id: str
    warehouse_name: str
    remaining_quantity: float
    reason: str
    severity: RecallSeverityEnum
    status: RecallStatusEnum
    initiated_at: datetime
    resolved_at: datetime | None = None
    affected_orders_count: int
    affected_orders: list[RecallAffectedOrderItemResponse] = Field(default_factory=list)


class BatchRecallListItemResponse(BaseModel):
    """Summary item for recall list and historical audit feeds."""

    id: str
    batch_id: str
    batch_no: str
    product_id: str
    product_name: str
    product_sku: str
    warehouse_name: str
    remaining_quantity: float
    reason: str
    severity: RecallSeverityEnum
    status: RecallStatusEnum
    initiated_at: datetime
    resolved_at: datetime | None = None
    affected_orders_count: int
    notified_count: int


class BatchRecallListResponse(BaseModel):
    """Paginated list of batch recall records."""

    items: list[BatchRecallListItemResponse]
    total: int
    page: int
    page_size: int
    pages: int


class BatchRecallNotifyResponse(BaseModel):
    """Result of broadcasting recall alerts to affected retailers."""

    recall_id: str
    status: RecallStatusEnum
    retailers_notified_count: int
    customers_notified_count: int
    notified_at: datetime
