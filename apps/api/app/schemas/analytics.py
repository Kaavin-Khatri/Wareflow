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


# --- Step 16.1: Profitability & Inventory Turnover Analytics ---


class ProfitabilityItem(BaseModel):
    """Profitability metric for a single group (Product, Category, or Retailer)."""

    id: str = Field(..., description="Entity ID (product_id, category_id, or retailer_id)")
    name: str = Field(..., description="Entity primary name")
    secondary_info: str | None = Field(None, description="SKU, pricing tier, or category name")
    badge: str | None = Field(None, description="Category, tier, or status badge")
    units_sold: float = Field(0.0, description="Total units sold in period")
    orders_count: int = Field(0, description="Total distinct orders in period")
    total_revenue: float = Field(0.0, description="Gross sales revenue in INR")
    total_cost: float = Field(0.0, description="Total procurement cost in INR")
    gross_margin_inr: float = Field(0.0, description="Gross profit in INR (Revenue - Cost)")
    gross_margin_pct: float = Field(0.0, description="Gross margin percentage (Margin / Revenue * 100)")


class ProfitabilitySummary(BaseModel):
    """Summary totals across all grouped profitability rows."""

    total_revenue: float = Field(0.0, description="Total revenue across all groups in INR")
    total_cost: float = Field(0.0, description="Total cost across all groups in INR")
    total_gross_margin_inr: float = Field(0.0, description="Total gross profit across all groups in INR")
    overall_margin_pct: float = Field(0.0, description="Overall blended margin percentage")
    total_units_sold: float = Field(0.0, description="Total units sold across all groups")
    total_orders: int = Field(0, description="Total order volume in period")


class ProfitabilityResponse(BaseModel):
    """Complete response for GET /analytics/profitability (Step 16.1)."""

    group_by: str = Field(..., description="Grouping dimension: product, category, or retailer")
    period: str = Field(..., description="Reporting time window: 7d, 30d, 90d, 12m, all")
    summary: ProfitabilitySummary = Field(..., description="Top summary aggregate metrics")
    items: list[ProfitabilityItem] = Field(default_factory=list, description="Grouped profitability records")
    generated_at: datetime = Field(..., description="Timestamp of calculation")


class TurnoverItem(BaseModel):
    """Inventory turnover velocity metric for a single product."""

    product_id: str = Field(..., description="Unique product ID")
    product_name: str = Field(..., description="Product catalog name")
    sku: str = Field(..., description="Stock keeping unit")
    category_name: str | None = Field(None, description="Category name")
    unit: str = Field("Piece", description="Measurement unit")
    current_on_hand: float = Field(..., description="Current physical stock on hand")
    units_sold: float = Field(..., description="Total units sold during selected period")
    average_on_hand: float = Field(..., description="Average inventory level over period")
    turnover_ratio: float = Field(..., description="Inventory turnover ratio (Units Sold / Avg Stock)")
    days_of_stock: float = Field(..., description="Days of stock on hand (Avg Stock / Units Sold * Days)")
    turnover_band: str = Field(..., description="Velocity health band: healthy, slowing, at_risk")
    cost_price: float = Field(0.0, description="Unit cost price in INR")
    tied_up_capital: float = Field(0.0, description="Capital tied up in current on-hand stock")


class TurnoverSummary(BaseModel):
    """Aggregate catalog-wide turnover velocity metrics."""

    average_turnover_ratio: float = Field(0.0, description="Catalog mean turnover ratio")
    average_days_of_stock: float = Field(0.0, description="Catalog mean days of stock on hand")
    healthy_count: int = Field(0, description="Number of products in healthy velocity band")
    slowing_count: int = Field(0, description="Number of products in slowing velocity band")
    at_risk_count: int = Field(0, description="Number of products in at-risk velocity band")
    total_products: int = Field(0, description="Total active products analyzed")


class TurnoverResponse(BaseModel):
    """Complete response for GET /analytics/turnover (Step 16.1)."""

    period: str = Field(..., description="Reporting time window: 7d, 30d, 90d, 12m, all")
    summary: TurnoverSummary = Field(..., description="Summary KPI velocity metrics")
    items: list[TurnoverItem] = Field(default_factory=list, description="Ranked product turnover velocity records")
    generated_at: datetime = Field(..., description="Timestamp of calculation")


# --- Step 16.2: Supplier & Retailer Performance, Warehouse Breakdown & Shrinkage ---


class SupplierPerformanceItem(BaseModel):
    """Supplier fulfillment and on-time reliability score."""

    supplier_id: str = Field(..., description="Unique supplier ID")
    supplier_name: str = Field(..., description="Registered vendor company name")
    contact_person: str | None = Field(None, description="Primary contact name")
    phone: str | None = Field(None, description="Contact phone")
    total_pos: int = Field(0, description="Total purchase orders placed with supplier")
    completed_pos: int = Field(0, description="Received or completed purchase orders")
    on_time_delivery_pct: float = Field(0.0, description="Percentage of orders delivered on or before expected date")
    fulfillment_accuracy_pct: float = Field(0.0, description="Percentage of ordered items received without discrepancy")
    return_rate_pct: float = Field(0.0, description="Percentage of received inventory returned to supplier")
    total_spend_inr: float = Field(0.0, description="Cumulative procurement spend in INR")
    rating_band: str = Field("good", description="Supplier quality band: excellent, good, needs_improvement")


class SupplierPerformanceSummary(BaseModel):
    """Portfolio-wide supplier performance summary."""

    average_on_time_pct: float = Field(0.0, description="Mean on-time delivery rate")
    average_accuracy_pct: float = Field(0.0, description="Mean fulfillment accuracy rate")
    average_return_rate_pct: float = Field(0.0, description="Mean return rate")
    total_spend_inr: float = Field(0.0, description="Total procurement capital spent")
    total_suppliers_analyzed: int = Field(0, description="Count of evaluated suppliers")
    excellent_count: int = Field(0, description="Count of excellent rated suppliers")
    needs_improvement_count: int = Field(0, description="Count of suppliers needing performance improvement")


class SupplierPerformanceResponse(BaseModel):
    """Complete response for GET /analytics/supplier-performance (Step 16.2)."""

    summary: SupplierPerformanceSummary = Field(..., description="High-level supplier portfolio KPIs")
    items: list[SupplierPerformanceItem] = Field(default_factory=list, description="Ranked supplier reliability records")
    generated_at: datetime = Field(..., description="Timestamp of calculation")


class RetailerPerformanceItem(BaseModel):
    """Retailer purchasing volume, order trend, and churn risk scoring."""

    retailer_id: str = Field(..., description="Unique retailer ID")
    retailer_name: str = Field(..., description="Store or business name")
    contact_person: str | None = Field(None, description="Primary contact name")
    phone: str | None = Field(None, description="Contact phone")
    pricing_tier: str = Field("standard", description="Assigned wholesale pricing tier")
    total_orders: int = Field(0, description="Total sales orders placed")
    total_revenue: float = Field(0.0, description="Cumulative revenue generated in INR")
    avg_order_value: float = Field(0.0, description="Average order value (AOV) in INR")
    last_order_date: str | None = Field(None, description="Date of most recent order in YYYY-MM-DD")
    days_since_last_order: int = Field(0, description="Days elapsed since most recent order")
    avg_order_gap_days: float = Field(0.0, description="Historical average days between consecutive orders")
    frequency_trend: str = Field("steady", description="Order velocity trend: increasing, steady, decreasing")
    is_churn_risk: bool = Field(False, description="True if days since last order exceeds 2x historical average gap")
    churn_risk_reason: str | None = Field(None, description="Explanation for churn risk flag")


class RetailerPerformanceSummary(BaseModel):
    """Portfolio-wide retailer performance summary."""

    total_retailers: int = Field(0, description="Total registered wholesale retailers")
    active_retailers_count: int = Field(0, description="Count of retailers with orders in past 90 days")
    churn_risk_count: int = Field(0, description="Count of retailers flagged with churn risk")
    total_portfolio_revenue_inr: float = Field(0.0, description="Total cumulative sales revenue")
    average_order_value_inr: float = Field(0.0, description="Overall blended average order value")


class RetailerPerformanceResponse(BaseModel):
    """Complete response for GET /analytics/retailer-performance (Step 16.2)."""

    summary: RetailerPerformanceSummary = Field(..., description="Summary retailer metrics")
    items: list[RetailerPerformanceItem] = Field(default_factory=list, description="Ranked retailer performance records")
    generated_at: datetime = Field(..., description="Timestamp of calculation")


class WarehouseMetricsItem(BaseModel):
    """Per-warehouse storage valuation and 30-day movement throughput."""

    warehouse_id: str = Field(..., description="Unique warehouse ID")
    warehouse_name: str = Field(..., description="Facility name")
    location: str | None = Field(None, description="Warehouse address / city")
    is_active: bool = Field(True, description="Warehouse active status")
    total_products_stored: int = Field(0, description="Count of distinct product SKUs stored")
    total_stock_units: float = Field(0.0, description="Total physical units on hand")
    total_stock_value_inr: float = Field(0.0, description="Total inventory valuation in INR")
    inbound_30d_units: float = Field(0.0, description="Units received into warehouse in trailing 30 days")
    outbound_30d_units: float = Field(0.0, description="Units shipped out of warehouse in trailing 30 days")
    movement_count_30d: int = Field(0, description="Total movement transactions in trailing 30 days")
    valuation_share_pct: float = Field(0.0, description="Percentage of total company inventory value in this facility")


class WarehouseBreakdownSummary(BaseModel):
    """Company-wide storage summary across all facilities."""

    total_warehouses: int = Field(0, description="Total operating warehouses")
    company_total_stock_units: float = Field(0.0, description="Total physical inventory across all facilities")
    company_total_valuation_inr: float = Field(0.0, description="Total inventory asset value in INR")
    total_30d_inbound_units: float = Field(0.0, description="Total inbound throughput across all facilities")
    total_30d_outbound_units: float = Field(0.0, description="Total outbound fulfillment across all facilities")


class WarehouseBreakdownResponse(BaseModel):
    """Complete response for GET /analytics/warehouse-breakdown (Step 16.2)."""

    summary: WarehouseBreakdownSummary = Field(..., description="Summary company warehouse metrics")
    warehouses: list[WarehouseMetricsItem] = Field(default_factory=list, description="Individual facility breakdowns")
    generated_at: datetime = Field(..., description="Timestamp of calculation")


class ShrinkageItem(BaseModel):
    """Inventory shrinkage/loss metric for a single product or category."""

    id: str = Field(..., description="Entity ID (product_id or category_id)")
    name: str = Field(..., description="Entity name")
    secondary_info: str | None = Field(None, description="SKU or category name")
    badge: str | None = Field(None, description="Category or status badge")
    units_lost: float = Field(0.0, description="Total physical units lost/damaged")
    incidents_count: int = Field(0, description="Count of damage/adjustment incidents")
    shrinkage_value_inr: float = Field(0.0, description="Total monetary loss in INR (units * cost_price)")
    pct_of_total_shrinkage: float = Field(0.0, description="Percentage share of total shrinkage value")


class ShrinkageSummary(BaseModel):
    """Aggregate shrinkage loss KPIs."""

    total_shrinkage_value_inr: float = Field(0.0, description="Total monetary shrinkage in INR")
    total_units_lost: float = Field(0.0, description="Total physical units written off")
    shrinkage_rate_pct: float = Field(0.0, description="Shrinkage as percentage of total inventory value")
    damage_incidents_count: int = Field(0, description="Total distinct damage/adjustment entries")


class ShrinkageResponse(BaseModel):
    """Complete response for GET /analytics/shrinkage (Step 16.2)."""

    period: str = Field(..., description="Reporting time window: 7d, 30d, 90d, 12m, all")
    group_by: str = Field(..., description="Grouping dimension: product or category")
    summary: ShrinkageSummary = Field(..., description="Top summary loss KPIs")
    items: list[ShrinkageItem] = Field(default_factory=list, description="Grouped shrinkage records")
    generated_at: datetime = Field(..., description="Timestamp of calculation")


# --- Step 16.3: Period Comparisons & Scheduled Weekly Reports ---


class ComparisonMetricResult(BaseModel):
    """Generic period-over-period and year-over-year comparative metric result (Step 16.3)."""

    metric_key: str = Field(..., description="Programmatic metric key (e.g. revenue, margin, turnover)")
    metric_label: str = Field(..., description="Human readable label")
    current_value: float = Field(..., description="Value in current period")
    prior_value: float = Field(..., description="Value in immediately preceding period")
    prior_year_value: float | None = Field(None, description="Value in same period last year")
    delta_value: float = Field(..., description="Absolute change (current - prior)")
    delta_pct: float = Field(..., description="Percentage change ((current - prior) / prior) * 100")
    delta_year_pct: float | None = Field(None, description="Percentage change vs same period last year")
    trend: str = Field("flat", description="Trend direction: 'up', 'down', 'flat'")
    is_positive: bool = Field(True, description="True if trend movement is favorable based on polarity")
    higher_is_better: bool = Field(True, description="Whether higher values are beneficial")
    period_label: str = Field("vs prior period", description="Baseline comparison label")
    formatted_current: str | None = Field(None, description="Formatted string e.g. ₹1,20,000")
    formatted_prior: str | None = Field(None, description="Formatted string for prior value")


class PeriodComparisonsResponse(BaseModel):
    """Comprehensive comparative scorecard across all major ERP KPIs (Step 16.3)."""

    period: str = Field(..., description="Selected time horizon (7d, 30d, 90d, 12m)")
    current_range: str = Field(..., description="Human readable current date range")
    prior_range: str = Field(..., description="Human readable comparison date range")
    metrics: dict[str, ComparisonMetricResult] = Field(..., description="Map of metric_key -> comparison result")
    generated_at: datetime = Field(..., description="Timestamp of calculation")


class WeeklyReportHighlightItem(BaseModel):
    """Structured highlight item for the weekly owner summary."""

    title: str = Field(..., description="Highlight title")
    description: str = Field(..., description="Contextual note / explanation")
    category: str = Field(..., description="Category: movers, slow_movers, low_stock, overdue_ar, turnover, shrinkage")
    metric_value: str | None = Field(None, description="Optional metric display text")
    badge_variant: str | None = Field("neutral", description="Visual badge style")


class WeeklyReportData(BaseModel):
    """Complete data structure for the 1-page Weekly Business Summary (Step 16.3)."""

    report_id: str = Field(..., description="Unique generated report ID")
    start_date: str = Field(..., description="Start date of the 7-day period (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date of the 7-day period (YYYY-MM-DD)")
    period_label: str = Field(..., description="Human friendly date range label")
    generated_at: datetime = Field(..., description="Timestamp of report generation")
    # Executive Scorecard
    revenue_inr: float = Field(0.0, description="Gross sales revenue in the week")
    revenue_delta_pct: float = Field(0.0, description="Revenue % change vs prior week")
    gross_margin_pct: float = Field(0.0, description="Gross profit margin % in the week")
    gross_margin_delta_pct: float = Field(0.0, description="Margin % change vs prior week")
    total_stock_valuation_inr: float = Field(0.0, description="Current total inventory valuation")
    turnover_ratio_30d: float = Field(0.0, description="Trailing 30-day inventory turnover ratio")
    # Operational Alerts
    low_stock_count: int = Field(0, description="Count of products below reorder point")
    overdue_invoices_count: int = Field(0, description="Count of unpaid invoices past due")
    overdue_amount_inr: float = Field(0.0, description="Total outstanding overdue AR in INR")
    shrinkage_inr: float = Field(0.0, description="Weekly damage & loss write-off value")
    # Fast & Slow Movers
    top_fast_movers: list[dict] = Field(default_factory=list, description="Top 3 revenue generating products")
    top_slow_movers: list[dict] = Field(default_factory=list, description="Top 3 stagnant SKUs by tied-up capital")
    # Key Highlights
    highlights: list[WeeklyReportHighlightItem] = Field(default_factory=list, description="AI & business insights")
    narrative_summary: str = Field("", description="Concise executive paragraph summarizing the week")


class SendWeeklyReportRequest(BaseModel):
    """Payload to trigger manual or automated dispatch of the weekly report."""

    channels: list[str] = Field(default_factory=lambda: ["email", "whatsapp"], description="Target channels")
    recipients: list[str] | None = Field(None, description="Optional custom recipient email/phone override")
    force_fresh: bool = Field(False, description="Recompute fresh metrics instead of cached")


class SendWeeklyReportResponse(BaseModel):
    """Response returned when weekly report is dispatched."""

    success: bool = Field(True, description="Whether dispatch was initiated successfully")
    report_id: str = Field(..., description="ID of the sent report")
    dispatched_at: datetime = Field(..., description="Timestamp of dispatch")
    channels_sent: list[str] = Field(default_factory=list, description="Channels successfully dispatched to")
    recipients_count: int = Field(0, description="Total recipients reached")
    summary_text: str = Field("", description="Executive summary text dispatched in message")



