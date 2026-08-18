"""Pydantic schemas for Stock Adjustments and Movement Ledger."""

import enum
from datetime import datetime

from pydantic import BaseModel, Field


class AdjustmentReasonEnum(enum.StrEnum):
    """Reason taxonomy for manual inventory adjustments."""

    DAMAGE = "damage"
    LOSS = "loss"
    RECOUNT = "recount"
    OTHER = "other"



class StockAdjustmentCreateRequest(BaseModel):
    """Payload for submitting a manual stock adjustment."""

    product_id: str = Field(..., description="ID of the product being adjusted")
    warehouse_id: str = Field(..., description="Warehouse where adjustment occurs")
    batch_id: str = Field(..., description="Target stock batch ID to adjust")
    delta: float = Field(..., description="Quantity delta to apply (positive or negative, non-zero)")
    reason: AdjustmentReasonEnum = Field(..., description="Mandatory adjustment reason category")
    notes: str | None = Field(None, max_length=500, description="Optional free-text notes detailing the adjustment")


class StockAdjustmentResponse(BaseModel):
    """Response returned after recording a stock adjustment."""

    movement_id: str
    product_id: str
    warehouse_id: str
    batch_id: str
    previous_quantity: float
    new_quantity: float
    delta: float
    reason: AdjustmentReasonEnum
    notes: str | None = None
    created_at: datetime
    created_by: str | None = None


class StockMovementListItemResponse(BaseModel):
    """Detailed stock movement record joined with human labels."""

    id: str
    product_id: str
    product_name: str
    product_sku: str
    warehouse_id: str
    warehouse_name: str
    batch_id: str | None = None
    batch_no: str | None = None
    type: str
    quantity: float
    reference_type: str | None = None
    reference_id: str | None = None
    human_label: str
    created_by: str | None = None
    created_at: datetime


class StockMovementListResponse(BaseModel):
    """Paginated list response for stock movements ledger."""

    items: list[StockMovementListItemResponse]
    total: int
    page: int
    page_size: int
    pages: int
