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


class WeeklyInsightMetrics(BaseModel):
    """Grounded operational numbers feeding the weekly insight narrative."""

    weekly_revenue: float = Field(0.0, description="Total sales order revenue in trailing 7 days")
    weekly_orders_count: int = Field(0, description="Total sales orders created in trailing 7 days")
    confirmed_orders_count: int = Field(0, description="Confirmed sales orders in trailing 7 days")
    top_mover_product_name: str | None = Field(
        None, description="Name of highest velocity product"
    )
    top_mover_units_sold: float = Field(0.0, description="Units sold of top mover in trailing week")
    reorder_needed_count: int = Field(
        0, description="Number of products at or below reorder threshold"
    )
    dead_stock_count: int = Field(0, description="Number of stagnant dead-stock catalog products")
    dead_stock_capital: float = Field(
        0.0, description="Total capital locked in dead inventory in INR"
    )


class WeeklyInsightResponse(BaseModel):
    """Owner weekly intelligence narrative and grounded metrics summary."""

    model_config = ConfigDict(from_attributes=True)

    headline: str = Field(..., description="Executive headline or theme for the week")
    narrative: str = Field(
        ..., description="2-3 sentence grounded narrative for the warehouse owner"
    )
    metrics_summary: WeeklyInsightMetrics = Field(
        ..., description="Underlying quantitative metrics verifying narrative"
    )
    generated_at: datetime = Field(..., description="Timestamp when narrative was compiled")
    expires_at: datetime = Field(..., description="Cache expiration timestamp (7 days)")
    is_ai_generated: bool = Field(
        False, description="True if generated by Groq LLM, False if grounded rule fallback"
    )
    is_cached: bool = Field(
        False, description="True if served from cache, False if newly generated"
    )


class ItemAnomalyReport(BaseModel):
    """Line item anomaly diagnostic result."""

    product_id: str
    product_name: str | None = None
    product_sku: str | None = None
    qty: float
    is_unusual: bool
    threshold: float | None = None
    historical_mean: float | None = None
    historical_stddev: float | None = None
    sample_count: int = 0
    anomaly_reason: str | None = None


class OrderAnomalyReportResponse(BaseModel):
    """Complete anomaly report for a specific Sales Order."""

    order_id: str
    so_number: str
    buyer_name: str | None = None
    has_unusual_items: bool
    unusual_items_count: int
    items: list[ItemAnomalyReport]
    evaluated_at: datetime


# ============================================================================
# Step 15.1: Owner Analytics Dashboard Schemas
# ============================================================================


class DashboardKPIMetrics(BaseModel):
    """Executive KPI card metrics for warehouse owner."""

    monthly_sales_revenue: float = Field(
        0.0, description="Gross sales revenue for current calendar month in INR"
    )
    monthly_inventory_value: float = Field(
        0.0, description="Total valuation of on-hand inventory at month-end in INR"
    )
    monthly_inventory_units: float = Field(
        0.0, description="Total physical units on-hand in warehouse at month-end"
    )
    total_stock_value: float = Field(
        0.0, description="Current total stock valuation across all active catalog products"
    )
    open_pos_count: int = Field(
        0, description="Count of open purchase orders in draft, approved, or ordered status"
    )
    open_sos_count: int = Field(
        0, description="Count of active sales orders in draft, confirmed, packed, or shipped status"
    )
    low_stock_count: int = Field(
        0, description="Count of active products where 0 < on_hand <= reorder_point"
    )
    critical_stock_count: int = Field(
        0, description="Count of active products where on_hand == 0 (stockout)"
    )
    total_outstanding_receivables: float = Field(
        0.0, description="Total unpaid balance across non-cancelled invoices in INR"
    )
    overdue_invoices_count: int = Field(
        0, description="Count of invoices past due date with remaining positive balance"
    )


class TopProductMovement(BaseModel):
    """Fastest-moving product over trailing 30 days."""

    product_id: str = Field(..., description="Unique product ID")
    product_name: str = Field(..., description="Product catalog name")
    sku: str = Field(..., description="Stock keeping unit identifier")
    category_name: str | None = Field(None, description="Category name")
    units_moved: float = Field(..., description="Total units sold or dispatched in trailing 30d")
    revenue: float = Field(0.0, description="Total revenue generated from this product in INR")


class InboundOutboundDataPoint(BaseModel):
    """Daily inbound vs outbound movement aggregation point for timeseries charts."""

    date: str = Field(..., description="Calendar date in YYYY-MM-DD format")
    inbound_qty: float = Field(0.0, description="Total units received (PO + returns in)")
    outbound_qty: float = Field(0.0, description="Total units dispatched (SO + returns out)")


class LowStockQuickItem(BaseModel):
    """Quick-action low stock item preview on dashboard."""

    product_id: str = Field(..., description="Unique product ID")
    product_name: str = Field(..., description="Product catalog name")
    sku: str = Field(..., description="Stock keeping unit identifier")
    current_stock: float = Field(..., description="Current on-hand stock quantity")
    reorder_point: float = Field(..., description="Configured reorder trigger threshold")
    urgency: str = Field(..., description="Urgency classification: critical, high, medium")
    primary_supplier_name: str | None = Field(None, description="Primary supplier name if linked")


class OverdueInvoiceQuickItem(BaseModel):
    """Quick-action overdue invoice preview on dashboard."""

    invoice_id: str = Field(..., description="Unique invoice ID")
    invoice_number: str = Field(..., description="Sequential invoice number e.g. INV/2026-27/0001")
    retailer_name: str = Field(..., description="Retailer or buyer company name")
    due_date: str = Field(..., description="Invoice due date in YYYY-MM-DD format")
    overdue_days: int = Field(..., description="Days past due date")
    balance_due: float = Field(..., description="Remaining unpaid balance in INR")
    status: str = Field(..., description="Current invoice status")


class OwnerDashboardResponse(BaseModel):
    """Unified single round-trip response for Owner Analytics Dashboard (Step 15.1)."""

    kpi_metrics: DashboardKPIMetrics = Field(
        ..., description="Top summary KPI cards for owner dashboard"
    )
    top_fastest_moving: list[TopProductMovement] = Field(
        default_factory=list, description="Top 5 fastest moving products in trailing 30 days"
    )
    top_dead_stock: list[DeadStockItem] = Field(
        default_factory=list, description="Top 5 stagnant products ranked by tied-up capital"
    )
    movement_trend_30d: list[InboundOutboundDataPoint] = Field(
        default_factory=list, description="30-day daily inbound vs outbound movement series"
    )
    low_stock_quick_list: list[LowStockQuickItem] = Field(
        default_factory=list, description="Top urgent low-stock items needing replenishment"
    )
    overdue_invoices_quick_list: list[OverdueInvoiceQuickItem] = Field(
        default_factory=list, description="Top overdue invoices for accounts receivable aging"
    )
    weekly_insight: WeeklyInsightResponse | None = Field(
        None, description="AI weekly executive briefing narrative (Groq or deterministic rule)"
    )
    is_empty_state: bool = Field(
        False, description="True if no products/orders exist in the deployment"
    )
    generated_at: datetime = Field(..., description="Timestamp of dashboard compilation")


class ARAgingBucketItem(BaseModel):
    """Accounts receivable aging breakdown for an individual wholesale retailer (Step 15.2)."""

    retailer_id: str = Field(..., description="Unique retailer UUID")
    retailer_name: str = Field(..., description="Registered wholesale business name")
    contact_person: str | None = Field(None, description="Primary contact name")
    phone: str | None = Field(None, description="Primary contact phone")
    credit_limit: float = Field(0.0, description="Authorized credit limit in INR")
    credit_balance: float = Field(0.0, description="Current credit balance utilized in INR")
    current: float = Field(0.0, description="Amount not yet overdue (0 days / future due date)")
    bucket_1_30: float = Field(0.0, description="Amount overdue 1 to 30 days")
    bucket_31_60: float = Field(0.0, description="Amount overdue 31 to 60 days")
    bucket_61_90: float = Field(0.0, description="Amount overdue 61 to 90 days")
    bucket_90_plus: float = Field(0.0, description="Amount overdue 90+ days (critical collection risk)")
    total_overdue: float = Field(0.0, description="Sum of 1-30, 31-60, 61-90, and 90+ overdue buckets")
    total_outstanding: float = Field(0.0, description="Sum of current and total overdue receivables")
    oldest_invoice_date: str | None = Field(None, description="ISO date of the oldest unpaid invoice")
    invoice_count: int = Field(0, description="Total count of open/unpaid invoices for this retailer")


class ARAgingSummary(BaseModel):
    """Portfolio-wide summary totals across all aging buckets (Step 15.2)."""

    total_current: float = Field(0.0, description="Total current receivables across all retailers")
    total_bucket_1_30: float = Field(0.0, description="Total 1-30 days overdue receivables")
    total_bucket_31_60: float = Field(0.0, description="Total 31-60 days overdue receivables")
    total_bucket_61_90: float = Field(0.0, description="Total 61-90 days overdue receivables")
    total_bucket_90_plus: float = Field(0.0, description="Total 90+ days overdue critical receivables")
    total_overdue: float = Field(0.0, description="Total overdue receivables across all buckets")
    total_outstanding: float = Field(0.0, description="Total outstanding receivables portfolio-wide")
    total_retailers: int = Field(0, description="Total count of active/reported retailers")
    overdue_retailers_count: int = Field(0, description="Count of retailers with total_overdue > 0")


class ARAgingReportResponse(BaseModel):
    """Full Accounts-Receivable Aging Report response (Step 15.2)."""

    as_of_date: str = Field(..., description="As-of reference date for overdue calculation (YYYY-MM-DD)")
    summary: ARAgingSummary = Field(..., description="Aggregated summary totals across all aging buckets")
    retailers: list[ARAgingBucketItem] = Field(
        default_factory=list, description="Per-retailer bucketed aging list sorted descending by overdue risk"
    )
    generated_at: datetime = Field(..., description="Timestamp of report compilation")
