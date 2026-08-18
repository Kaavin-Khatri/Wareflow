"""Pydantic schemas for Stock and Batch Management."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class WarehouseSummary(BaseModel):
    """Warehouse summary representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    location: str | None = None
    is_active: bool = True


class StockBatchResponse(BaseModel):
    """Stock batch details with calculated expiry indicators."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    warehouse_id: str
    warehouse_name: str
    batch_no: str
    quantity: float
    expiry_date: date | None = None
    received_at: datetime
    days_until_expiry: int | None = None
    is_expired: bool = False


class WarehouseStockBreakdown(BaseModel):
    """Per-warehouse stock breakdown for a product."""

    warehouse_id: str
    warehouse_name: str
    on_hand: float
    batch_count: int


class ProductStockResponse(BaseModel):
    """Comprehensive stock view for a single product across all warehouses and batches."""

    product_id: str
    sku: str
    name: str
    base_uom_name: str
    cost_price: float
    wholesale_price: float
    reorder_point: int
    reorder_qty: int
    total_on_hand: float
    preferred_uom_name: str | None = None
    preferred_uom_qty: float | None = None
    stock_status: Literal["ok", "low", "critical"]
    warehouses: list[WarehouseStockBreakdown] = Field(default_factory=list)
    batches: list[StockBatchResponse] = Field(default_factory=list)


class StockOverviewItem(BaseModel):
    """Summarized product stock line item for multi-warehouse inventory feed."""

    product_id: str
    sku: str
    name: str
    category_id: str | None = None
    category_name: str | None = None
    image_url: str | None = None
    base_uom_name: str
    total_on_hand: float
    preferred_uom_name: str | None = None
    preferred_uom_qty: float | None = None
    reorder_point: int
    stock_status: Literal["ok", "low", "critical"]
    warehouses: list[WarehouseStockBreakdown] = Field(default_factory=list)


class StockOverviewResponse(BaseModel):
    """Inventory overview summary feed with health counters."""

    items: list[StockOverviewItem]
    total_products: int
    ok_count: int
    low_count: int
    critical_count: int
