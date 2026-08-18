"""Pydantic schemas for Inter-Warehouse Stock Transfers (Step 9.2)."""

from datetime import datetime

from pydantic import BaseModel, Field


class StockTransferCreateRequest(BaseModel):
    """Payload for initiating an inter-warehouse stock transfer."""

    product_id: str = Field(..., description="ID of the product being transferred")
    batch_id: str = Field(..., description="Source warehouse stock batch ID")
    from_warehouse_id: str = Field(..., description="Source warehouse ID")
    to_warehouse_id: str = Field(..., description="Destination warehouse ID")
    quantity: float = Field(..., gt=0, description="Quantity of units to transfer")
    notes: str | None = Field(None, description="Optional operational notes or transfer reference")


class StockTransferResponse(BaseModel):
    """Result of an executed atomic stock transfer."""

    transfer_id: str
    product_id: str
    from_warehouse_id: str
    to_warehouse_id: str
    source_batch_id: str
    destination_batch_id: str
    quantity: float
    out_movement_id: str
    in_movement_id: str
    created_by: str | None = None
    created_at: datetime
    notes: str | None = None


class StockTransferListItemResponse(BaseModel):
    """Item in historical inter-warehouse transfers list."""

    id: str
    product_id: str
    product_name: str
    product_sku: str
    from_warehouse_id: str
    from_warehouse_name: str
    to_warehouse_id: str
    to_warehouse_name: str
    batch_no: str
    quantity: float
    created_by: str | None = None
    created_at: datetime
    notes: str | None = None


class StockTransferListResponse(BaseModel):
    """Paginated list of inter-warehouse stock transfers."""

    items: list[StockTransferListItemResponse]
    total: int
    page: int
    page_size: int
    pages: int
