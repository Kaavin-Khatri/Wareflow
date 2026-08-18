"""Pydantic schemas for Stock Analytics & Composition Dashboard (Step 6.1)."""

from pydantic import BaseModel, Field


class CategoryValueItem(BaseModel):
    """Stock value and quantity metrics broken down by category."""

    category_id: str | None = None
    category_name: str
    total_value: float = Field(..., description="Total cost value in currency")
    total_units: float = Field(..., description="Total unit count in base UoM")
    product_count: int = Field(..., description="Distinct product count in category")
    percentage: float = Field(..., description="Percentage of total stock value")


class WarehouseValueItem(BaseModel):
    """Stock value and quantity metrics broken down by storage warehouse."""

    warehouse_id: str
    warehouse_name: str
    total_value: float = Field(..., description="Total cost value in warehouse")
    total_units: float = Field(..., description="Total units stored in warehouse")
    batch_count: int = Field(..., description="Active stock batches count")
    percentage: float = Field(..., description="Percentage of total stock value")


class StockValueSummaryResponse(BaseModel):
    """Total stock valuation across the wholesale enterprise."""

    total_stock_value: float
    total_units: float
    total_products: int
    by_category: list[CategoryValueItem]
    by_warehouse: list[WarehouseValueItem]


class HealthBandItem(BaseModel):
    """Single health band metric summary."""

    status: str
    label: str
    count: int
    percentage: float
    description: str


class StockHealthDistributionResponse(BaseModel):
    """Distribution of products across health and reorder bands."""

    healthy_count: int
    low_count: int
    critical_count: int
    out_of_stock_count: int
    total_products: int
    bands: list[HealthBandItem]


class TopProductItem(BaseModel):
    """Top product entry by capital allocation or volume."""

    product_id: str
    sku: str
    name: str
    category_name: str | None = None
    total_on_hand: float
    cost_price: float
    total_value: float
    base_uom_name: str


class TopProductsResponse(BaseModel):
    """Top products by value and unit volume."""

    by_value: list[TopProductItem]
    by_quantity: list[TopProductItem]


class ExpiryWindowItem(BaseModel):
    """Batches aggregated by upcoming expiration timeline."""

    window_key: str
    label: str
    batch_count: int
    total_quantity: float
    total_value: float


class ExpiryTimelineResponse(BaseModel):
    """Forward-looking expiry horizon analysis across active batches."""

    windows: list[ExpiryWindowItem]
    total_expiring_soon_count: int
    total_expiring_soon_value: float


# --- Step 6.2: Purchasing Spend & Trend Schemas ---


class MonthlySpendItem(BaseModel):
    """Monthly spend record on received inventory."""

    month: str = Field(..., description="Month key (e.g. 2026-08)")
    label: str = Field(..., description="Human readable month (e.g. Aug 2026)")
    total_spend: float = Field(..., description="Total money spent on received stock")
    order_count: int = Field(..., description="Number of purchase orders in month")
    received_units: float = Field(..., description="Total units received in month")


class SpendTrendResponse(BaseModel):
    """12-month purchasing spend trend."""

    monthly_trend: list[MonthlySpendItem]
    total_period_spend: float
    avg_monthly_spend: float


class SupplierSpendItem(BaseModel):
    """Procurement spend aggregated by vendor/supplier."""

    supplier_id: str
    supplier_name: str
    total_spend: float
    order_count: int
    percentage: float


class SupplierSpendResponse(BaseModel):
    """Spend breakdown by supplier."""

    suppliers: list[SupplierSpendItem]
    total_spend: float


class CategorySpendItem(BaseModel):
    """Procurement spend aggregated by product category."""

    category_id: str | None = None
    category_name: str
    total_spend: float
    received_units: float
    percentage: float


class CategorySpendResponse(BaseModel):
    """Spend breakdown by product category."""

    categories: list[CategorySpendItem]
    total_spend: float


class ProductCostPoint(BaseModel):
    """Historical cost point for a product."""

    recorded_at: str = Field(..., description="Timestamp or date string")
    cost_price: float = Field(..., description="Unit cost price at this point")
    source: str = Field(..., description="Source of price point (e.g. PO, Base)")


class ProductCostTrendItem(BaseModel):
    """Cost price evolution for a single product."""

    product_id: str
    sku: str
    name: str
    current_cost_price: float
    cost_history: list[ProductCostPoint]
    pct_change: float = Field(..., description="Percentage price creep from baseline")


class AvgCostTrendResponse(BaseModel):
    """Average cost trends across products."""

    products: list[ProductCostTrendItem]
