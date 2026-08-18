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
