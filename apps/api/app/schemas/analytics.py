"""Pydantic schemas for Reorder Suggestions & Dead Stock Detection (Step 14.2)."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ReorderSuggestionItem(BaseModel):
    """Actionable reorder suggestion for a low or depleted product."""

    model_config = ConfigDict(from_attributes=True)

    product_id: str = Field(..., description="Unique product ID")
    product_name: str = Field(..., description="Product catalog name")
    sku: str = Field(..., description="Stock keeping unit identifier")
    category_name: str | None = Field(None, description="Product category name")
    unit: str = Field("Piece", description="Measurement unit")
    on_hand: float = Field(..., description="Current on-hand physical inventory")
    reorder_point: int = Field(..., description="Configured reorder trigger threshold")
    reorder_qty: int = Field(..., description="Standard product batch reorder quantity")
    forecasted_daily_demand: float = Field(
        ..., description="Projected units consumed per day from statistical forecasting"
    )
    lead_time_days_buffer: int = Field(
        ..., description="Supplier lead time buffer applied in calculation"
    )
    suggested_reorder_qty: int = Field(
        ..., description="Calculated optimal reorder quantity to cover lead time"
    )
    unit_cost: float = Field(..., description="Unit cost price for purchase order")
    estimated_cost: float = Field(
        ..., description="Total estimated capital required for suggested quantity"
    )
    days_of_stock_remaining: float | None = Field(
        None, description="Estimated days before total inventory depletion"
    )
    urgency: str = Field(
        ..., description="Depletion urgency: critical (0-3d), high (<=half point), medium"
    )
    primary_supplier_id: str | None = Field(
        None, description="Last or default supplier associated with product"
    )
    primary_supplier_name: str | None = Field(
        None, description="Name of primary supplier if identified"
    )


class ReorderSuggestionsResponse(BaseModel):
    """Aggregate actionable reorder suggestions for warehouse purchasing."""

    items: list[ReorderSuggestionItem] = Field(..., description="List of recommended items")
    total_suggested_items: int = Field(..., description="Count of items needing replenishment")
    total_estimated_cost: float = Field(
        ..., description="Total purchase capital needed across all suggestions"
    )
    critical_count: int = Field(..., description="Number of items at critical urgency level")
    high_count: int = Field(..., description="Number of items at high urgency level")
    generated_at: datetime = Field(..., description="Timestamp of calculation")


class POFromSuggestionItem(BaseModel):
    """Single line item payload for creating a Purchase Order from suggestions."""

    product_id: str = Field(..., description="Product ID to order")
    qty_ordered: float = Field(..., gt=0, description="Quantity to purchase")
    unit_cost: float = Field(..., ge=0, description="Purchase unit price")
    uom_id: str | None = Field(None, description="Unit of measure ID if applicable")


class CreatePOFromSuggestionsRequest(BaseModel):
    """Payload to create a draft Purchase Order from one or more reorder suggestions."""

    supplier_id: str = Field(..., description="Target supplier ID")
    items: list[POFromSuggestionItem] = Field(
        ..., min_length=1, description="Line items for the purchase order"
    )
    expected_date: str | None = Field(None, description="Expected delivery date in YYYY-MM-DD")
    notes: str | None = Field(None, description="Internal purchase order notes")


class DeadStockItem(BaseModel):
    """Product with zero movement during the trailing window holding tied-up capital."""

    model_config = ConfigDict(from_attributes=True)

    product_id: str = Field(..., description="Unique product identifier")
    product_name: str = Field(..., description="Product catalog name")
    sku: str = Field(..., description="Stock keeping unit identifier")
    category_name: str | None = Field(None, description="Category name")
    unit: str = Field("Piece", description="Measurement unit")
    on_hand: float = Field(..., description="Physical units sitting in warehouse")
    cost_price: float = Field(..., description="Unit cost price")
    tied_up_capital: float = Field(
        ..., description="Total capital tied up in sitting inventory (on_hand * cost_price)"
    )
    last_movement_at: datetime | None = Field(
        None, description="Date of last outbound sale/shipment, if any"
    )
    idle_days: int = Field(..., description="Days since last movement or product addition")
    recommended_action: str = Field(
        ...,
        description="Strategic action code: discount_clearance, bundle_promotion, liquidate_or_return",
    )
    action_label: str = Field(..., description="Human-readable recommended action advice")


class DeadStockResponse(BaseModel):
    """Ranked listing of dead-stock inventory holding dormant capital."""

    items: list[DeadStockItem] = Field(
        ..., description="Ranked dead stock items (descending by tied-up capital)"
    )
    total_dead_items: int = Field(..., description="Total count of dead stock products")
    total_tied_up_capital: float = Field(
        ..., description="Total capital locked in non-moving inventory"
    )
    window_days: int = Field(..., description="Trailing observation window in days (e.g., 60, 90)")
    generated_at: datetime = Field(..., description="Timestamp of report compilation")
