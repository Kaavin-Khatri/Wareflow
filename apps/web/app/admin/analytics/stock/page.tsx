"use client";

import { useEffect, useState, useMemo } from "react";
import dynamic from "next/dynamic";
import AppLayout from "@/components/AppLayout";
import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassTiltCard } from "@/components/glass/GlassTiltCard";
import { AnimatedNumber } from "@/components/motion/AnimatedNumber";
import { apiClient } from "@/lib/api-client";
import {
  Boxes,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Clock,
  Warehouse,
  PieChart as PieIcon,
  Layers,
  ArrowUpRight,
  Receipt,
  Building2,
  Tag,
  LineChart as LineChartIcon,
  Sparkles,
  Info,
  RefreshCw,
} from "lucide-react";

import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  AreaChart,
  Area,
  LineChart,
  Line,
} from "recharts";

// Dynamic 3D Topology component
const StockTopology3D = dynamic(() => import("@/components/analytics/StockTopology3D"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[220px] rounded-3xl bg-white/[0.02] border border-white/10 flex items-center justify-center text-xs text-white/40 font-mono">
      Initializing 3D Inventory Topology Core...
    </div>
  ),
});

// --- Types ---

export interface CategoryValueItem {
  category_id: string | null;
  category_name: string;
  total_value: number;
  total_units: number;
  product_count: number;
  percentage: number;
}

export interface WarehouseValueItem {
  warehouse_id: string;
  warehouse_name: string;
  total_value: number;
  total_units: number;
  batch_count: number;
  percentage: number;
}

export interface StockValueSummary {
  total_stock_value: number;
  total_units: number;
  total_products: number;
  by_category: CategoryValueItem[];
  by_warehouse: WarehouseValueItem[];
}

export interface HealthBandItem {
  status: string;
  label: string;
  count: number;
  percentage: number;
  description: string;
}

export interface StockHealthDistribution {
  healthy_count: number;
  low_count: number;
  critical_count: number;
  out_of_stock_count: number;
  total_products: number;
  bands: HealthBandItem[];
}

export interface TopProductItem {
  product_id: string;
  sku: string;
  name: string;
  category_name: string | null;
  total_on_hand: number;
  cost_price: number;
  total_value: number;
  base_uom_name: string;
}

export interface TopProductsResponse {
  by_value: TopProductItem[];
  by_quantity: TopProductItem[];
}

export interface ExpiryWindowItem {
  window_key: string;
  label: string;
  batch_count: number;
  total_quantity: number;
  total_value: number;
}

export interface ExpiryTimelineResponse {
  windows: ExpiryWindowItem[];
  total_expiring_soon_count: number;
  total_expiring_soon_value: number;
}

// Step 6.2 Types
export interface MonthlySpendItem {
  month: string;
  label: string;
  total_spend: number;
  order_count: number;
  received_units: number;
}

export interface SpendTrendResponse {
  monthly_trend: MonthlySpendItem[];
  total_period_spend: number;
  avg_monthly_spend: number;
}

export interface SupplierSpendItem {
  supplier_id: string;
  supplier_name: string;
  total_spend: number;
  order_count: number;
  percentage: number;
}

export interface SupplierSpendResponse {
  suppliers: SupplierSpendItem[];
  total_spend: number;
}

export interface CategorySpendItem {
  category_id: string | null;
  category_name: string;
  total_spend: number;
  received_units: number;
  percentage: number;
}

export interface CategorySpendResponse {
  categories: CategorySpendItem[];
  total_spend: number;
}

export interface ProductCostPoint {
  recorded_at: string;
  cost_price: number;
  source: string;
}

export interface ProductCostTrendItem {
  product_id: string;
  sku: string;
  name: string;
  current_cost_price: number;
  cost_history: ProductCostPoint[];
  pct_change: number;
}

export interface AvgCostTrendResponse {
  products: ProductCostTrendItem[];
}

const CATEGORY_COLORS = [
  "#8b5cf6", // Purple
  "#3b82f6", // Blue
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#ec4899", // Pink
  "#6366f1", // Indigo
  "#14b8a6", // Teal
  "#f97316", // Orange
];

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name?: string;
    value?: number;
    payload?: Record<string, unknown>;
  }>;
}

function CustomChartTooltip({ active, payload }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    const data = payload[0];
    const raw = data.payload as Record<string, unknown> | undefined;
    return (
      <div className="bg-neutral-900/95 border border-white/20 p-3 rounded-xl shadow-2xl backdrop-blur-xl text-xs font-mono">
        <div className="font-sans font-bold text-white mb-1">
          {(raw?.category_name as string) ||
            (raw?.warehouse_name as string) ||
            (raw?.supplier_name as string) ||
            (raw?.label as string) ||
            (raw?.name as string) ||
            data.name}
        </div>
        <div className="text-purple-400">Value: ₹{(Number(data.value) || 0).toLocaleString()}</div>
        {raw?.percentage !== undefined && (
          <div className="text-white/60 text-[11px]">Share: {String(raw.percentage)}%</div>
        )}
        {raw?.total_units !== undefined && (
          <div className="text-white/60 text-[11px]">
            Units: {Number(raw.total_units).toLocaleString()}
          </div>
        )}
        {raw?.order_count !== undefined && (
          <div className="text-white/60 text-[11px]">
            Orders: {Number(raw.order_count).toLocaleString()}
          </div>
        )}
      </div>
    );
  }
  return null;
}

function EmptySpendState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="h-64 flex flex-col items-center justify-center text-center p-6 rounded-2xl bg-white/[0.02] border border-white/5 space-y-3">
      <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shadow-[0_0_20px_-4px_rgba(168,85,247,0.4)]">
        <Receipt className="w-6 h-6" />
      </div>
      <div>
        <h4 className="text-sm font-semibold text-white/90">{title}</h4>
        <p className="text-xs text-white/50 max-w-sm mt-1">
          {description ||
            "No purchase data yet — this fills in automatically once you start receiving stock in Phase 6."}
        </p>
      </div>
      <GlassBadge variant="neutral">Pre-Phase 6 Ready</GlassBadge>
    </div>
  );
}

export default function StockAnalyticsPage() {
  // Step 6.1 State
  const [valueSummary, setValueSummary] = useState<StockValueSummary | null>(null);
  const [healthDist, setHealthDist] = useState<StockHealthDistribution | null>(null);
  const [topProducts, setTopProducts] = useState<TopProductsResponse | null>(null);
  const [expiryTimeline, setExpiryTimeline] = useState<ExpiryTimelineResponse | null>(null);

  // Step 6.2 State
  const [spendMonths, setSpendMonths] = useState<number>(12);
  const [spendTrend, setSpendTrend] = useState<SpendTrendResponse | null>(null);
  const [spendBySupplier, setSpendBySupplier] = useState<SupplierSpendResponse | null>(null);
  const [spendByCategory, setSpendByCategory] = useState<CategorySpendResponse | null>(null);
  const [avgCostTrend, setAvgCostTrend] = useState<AvgCostTrendResponse | null>(null);
  const [selectedCostSku, setSelectedCostSku] = useState<string | null>(null);

  // Interactive View Modes & Filters
  const [activeTab, setActiveTab] = useState<"all" | "valuation" | "spend">("all");
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string | null>(null);
  const [hoveredCategoryIdx, setHoveredCategoryIdx] = useState<number | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    async function loadAnalytics() {
      try {
        setLoading(true);
        setError(null);
        const [valData, healthData, topData, expData, spendT, supSpend, catSpend, costTrend] =
          await Promise.all([
            apiClient.get<StockValueSummary>("/analytics/stock/value-summary"),
            apiClient.get<StockHealthDistribution>("/analytics/stock/health-distribution"),
            apiClient.get<TopProductsResponse>("/analytics/stock/top-value-products?limit=10"),
            apiClient.get<ExpiryTimelineResponse>("/analytics/stock/expiry-timeline"),
            apiClient.get<SpendTrendResponse>(`/analytics/stock/spend-trend?months=${spendMonths}`),
            apiClient.get<SupplierSpendResponse>(
              `/analytics/stock/spend-by-supplier?months=${spendMonths}`,
            ),
            apiClient.get<CategorySpendResponse>(
              `/analytics/stock/spend-by-category?months=${spendMonths}`,
            ),
            apiClient.get<AvgCostTrendResponse>("/analytics/stock/avg-cost-trend"),
          ]);

        if (!ignore) {
          setValueSummary(valData);
          setHealthDist(healthData);
          setTopProducts(topData);
          setExpiryTimeline(expData);
          setSpendTrend(spendT);
          setSpendBySupplier(supSpend);
          setSpendByCategory(catSpend);
          setAvgCostTrend(costTrend);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load stock analytics.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadAnalytics();
    return () => {
      ignore = true;
    };
  }, [spendMonths]);

  // Selected product cost trend points
  const activeProductCost = useMemo(() => {
    if (!avgCostTrend || !avgCostTrend.products.length) return null;
    return (
      (selectedCostSku && avgCostTrend.products.find((p) => p.sku === selectedCostSku)) ||
      avgCostTrend.products[0]
    );
  }, [avgCostTrend, selectedCostSku]);

  // Filtered top products by category selection
  const filteredTopProducts = useMemo(() => {
    if (!topProducts) return [];
    if (!selectedCategoryFilter) return topProducts.by_value;
    return topProducts.by_value.filter((p) => p.category_name === selectedCategoryFilter);
  }, [topProducts, selectedCategoryFilter]);

  // Donut Center Readout
  const donutCenterReadout = useMemo(() => {
    if (!valueSummary) return { label: "Total Valuation", value: "₹0", sub: "100%" };
    if (hoveredCategoryIdx !== null && valueSummary.by_category[hoveredCategoryIdx]) {
      const cat = valueSummary.by_category[hoveredCategoryIdx];
      return {
        label: cat.category_name,
        value: `₹${cat.total_value.toLocaleString()}`,
        sub: `${cat.percentage}% share (${cat.total_units} units)`,
      };
    }
    return {
      label: "Total Valuation",
      value: `₹${valueSummary.total_stock_value.toLocaleString()}`,
      sub: `${valueSummary.total_units.toLocaleString()} total units`,
    };
  }, [valueSummary, hoveredCategoryIdx]);

  const kpiCardsContent = (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* KPI 1: Total Valuation */}
      <GlassTiltCard className="p-4 border-purple-500/20 bg-purple-500/5 relative overflow-hidden group">
        <div className="flex justify-between items-start">
          <div>
            <span className="text-xs font-semibold text-purple-300/80 uppercase tracking-wider block">
              Total Stock Valuation
            </span>
            <div className="text-2xl font-bold text-white font-mono mt-1 flex items-baseline gap-1">
              <span>₹</span>
              <AnimatedNumber value={valueSummary?.total_stock_value || 0} />
            </div>
            <span className="text-[11px] text-white/50 block mt-0.5">
              Based on purchase cost price
            </span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center shrink-0 group-hover:scale-110 group-hover:shadow-[0_0_15px_rgba(168,85,247,0.5)] transition-all">
            <TrendingUp className="w-5 h-5 text-purple-400" />
          </div>
        </div>
      </GlassTiltCard>

      {/* KPI 2: Total Units On-Hand */}
      <GlassTiltCard className="p-4 border-white/10 relative overflow-hidden group">
        <div className="flex justify-between items-start">
          <div>
            <span className="text-xs font-semibold text-white/60 uppercase tracking-wider block">
              Total Units On Hand
            </span>
            <div className="text-2xl font-bold text-white font-mono mt-1">
              <AnimatedNumber value={valueSummary?.total_units || 0} />
            </div>
            <span className="text-[11px] text-white/50 block mt-0.5">
              Across {valueSummary?.total_products || 0} active SKUs
            </span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
            <Boxes className="w-5 h-5 text-white/70" />
          </div>
        </div>
      </GlassTiltCard>

      {/* KPI 3: Healthy Stock Ratio */}
      <GlassTiltCard className="p-4 border-emerald-500/20 bg-emerald-500/5 relative overflow-hidden group">
        <div className="flex justify-between items-start">
          <div>
            <span className="text-xs font-semibold text-emerald-300/80 uppercase tracking-wider block">
              Healthy Stock
            </span>
            <div className="text-2xl font-bold text-emerald-400 font-mono mt-1">
              <AnimatedNumber value={healthDist?.healthy_count || 0} />
            </div>
            <span className="text-[11px] text-emerald-400/70 block mt-0.5">
              Above reorder threshold
            </span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0 group-hover:scale-110 group-hover:shadow-[0_0_15px_rgba(16,185,129,0.5)] transition-all">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
        </div>
      </GlassTiltCard>

      {/* KPI 4: Action Required */}
      <GlassTiltCard className="p-4 border-rose-500/20 bg-rose-500/5 relative overflow-hidden group">
        <div className="flex justify-between items-start">
          <div>
            <span className="text-xs font-semibold text-rose-300/80 uppercase tracking-wider block">
              Attention Required
            </span>
            <div className="text-2xl font-bold text-rose-400 font-mono mt-1">
              <AnimatedNumber
                value={
                  (healthDist?.low_count || 0) +
                  (healthDist?.critical_count || 0) +
                  (healthDist?.out_of_stock_count || 0)
                }
              />
            </div>
            <span className="text-[11px] text-rose-400/70 block mt-0.5">
              Low: {healthDist?.low_count || 0} • Crit: {healthDist?.critical_count || 0} • Out:{" "}
              {healthDist?.out_of_stock_count || 0}
            </span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center shrink-0 group-hover:scale-110 group-hover:shadow-[0_0_15px_rgba(244,63,94,0.5)] transition-all">
            <AlertTriangle className="w-5 h-5 text-rose-400" />
          </div>
        </div>
      </GlassTiltCard>
    </div>
  );

  const mainDashboardContent = (
    <>
      {error && (
        <div className="mb-6 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="py-24 text-center text-sm text-white/40 font-mono flex flex-col items-center justify-center gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-purple-400" />
          <span>Calculating live inventory valuations and spend distributions...</span>
        </div>
      ) : (
        <div className="space-y-8">
          {/* TOP CONTROLS & 3D TOPOLOGY CORE */}
          <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 p-4 rounded-3xl bg-white/[0.02] border border-white/10 backdrop-blur-xl">
            {/* View Mode Tabs */}
            <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-neutral-900/80 border border-white/10">
              <button
                onClick={() => setActiveTab("all")}
                className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
                  activeTab === "all"
                    ? "bg-purple-600 text-white shadow-[0_0_16px_rgba(147,51,234,0.5)]"
                    : "text-white/60 hover:text-white hover:bg-white/5"
                }`}
              >
                All Intelligence
              </button>
              <button
                onClick={() => setActiveTab("valuation")}
                className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
                  activeTab === "valuation"
                    ? "bg-purple-600 text-white shadow-[0_0_16px_rgba(147,51,234,0.5)]"
                    : "text-white/60 hover:text-white hover:bg-white/5"
                }`}
              >
                Valuation & Composition
              </button>
              <button
                onClick={() => setActiveTab("spend")}
                className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
                  activeTab === "spend"
                    ? "bg-purple-600 text-white shadow-[0_0_16px_rgba(147,51,234,0.5)]"
                    : "text-white/60 hover:text-white hover:bg-white/5"
                }`}
              >
                Procurement & Spend
              </button>
            </div>

            {/* Active Category Filter Clear */}
            {selectedCategoryFilter && (
              <div className="flex items-center gap-2 text-xs">
                <GlassBadge variant="accent">Filtered: {selectedCategoryFilter}</GlassBadge>
                <button
                  onClick={() => setSelectedCategoryFilter(null)}
                  className="text-[11px] text-white/50 hover:text-white underline transition-colors"
                >
                  Clear filter
                </button>
              </div>
            )}
          </div>

          {/* Interactive 3D Multi-Warehouse Topology Core */}
          {(activeTab === "all" || activeTab === "valuation") && <StockTopology3D />}

          {/* ============================================================ */}
          {/* SECTION 1: INVENTORY VALUATION & COMPOSITION (Step 6.1)      */}
          {/* ============================================================ */}
          {(activeTab === "all" || activeTab === "valuation") && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                    <PieIcon className="w-5 h-5 text-purple-400" />
                    Inventory Valuation & Composition
                  </h2>
                  <p className="text-xs text-white/50 mt-0.5">
                    Real-time capital balance, category allocations, warehouse holdings, and batch
                    expiry.
                  </p>
                </div>
                <GlassBadge variant="accent">Live Warehouse Data</GlassBadge>
              </div>

              {/* ROW 1: Donut (Category) + Bar (Warehouse) */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Category Composition Donut with Active Center Readout */}
                <GlassCard className="p-6 border-white/10 flex flex-col">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <PieIcon className="w-5 h-5 text-purple-400" />
                      <h3 className="font-semibold text-white text-sm">
                        Capital Concentration by Category
                      </h3>
                    </div>
                    <GlassBadge variant="accent">
                      {valueSummary?.by_category.length || 0} Categories
                    </GlassBadge>
                  </div>

                  {!valueSummary?.by_category.length ? (
                    <div className="h-64 flex items-center justify-center text-xs text-white/40">
                      No category stock data available
                    </div>
                  ) : (
                    <div className="relative h-72 w-full flex items-center justify-center">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={valueSummary.by_category}
                            dataKey="total_value"
                            nameKey="category_name"
                            cx="50%"
                            cy="50%"
                            innerRadius={70}
                            outerRadius={100}
                            paddingAngle={4}
                            onMouseEnter={(_, index) => setHoveredCategoryIdx(index)}
                            onMouseLeave={() => setHoveredCategoryIdx(null)}
                            onClick={(data) => {
                              const catName = data.payload?.category_name as string;
                              setSelectedCategoryFilter((prev) =>
                                prev === catName ? null : catName,
                              );
                            }}
                          >
                            {valueSummary.by_category.map((cat, index) => (
                              <Cell
                                key={`cat-cell-${index}`}
                                fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                                stroke={
                                  selectedCategoryFilter === cat.category_name
                                    ? "#ffffff"
                                    : hoveredCategoryIdx === index
                                      ? "#c084fc"
                                      : "rgba(0,0,0,0.4)"
                                }
                                strokeWidth={
                                  selectedCategoryFilter === cat.category_name ||
                                  hoveredCategoryIdx === index
                                    ? 3
                                    : 2
                                }
                                className="transition-all duration-300 cursor-pointer"
                              />
                            ))}
                          </Pie>
                          <Tooltip content={<CustomChartTooltip />} />
                        </PieChart>
                      </ResponsiveContainer>

                      {/* Dynamic Center Metric Readout */}
                      <div className="absolute pointer-events-none text-center flex flex-col items-center justify-center max-w-[130px]">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-purple-300 truncate w-full">
                          {donutCenterReadout.label}
                        </span>
                        <span className="text-base font-bold font-mono text-white leading-tight mt-0.5">
                          {donutCenterReadout.value}
                        </span>
                        <span className="text-[10px] text-white/50 truncate w-full mt-0.5">
                          {donutCenterReadout.sub}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Interactive Legend List */}
                  <div className="mt-4 grid grid-cols-2 gap-2 max-h-32 overflow-y-auto pr-1">
                    {valueSummary?.by_category.map((cat, idx) => (
                      <div
                        key={cat.category_name}
                        onClick={() =>
                          setSelectedCategoryFilter((prev) =>
                            prev === cat.category_name ? null : cat.category_name,
                          )
                        }
                        onMouseEnter={() => setHoveredCategoryIdx(idx)}
                        onMouseLeave={() => setHoveredCategoryIdx(null)}
                        className={`flex items-center justify-between text-xs p-1.5 rounded-xl border transition-all cursor-pointer ${
                          selectedCategoryFilter === cat.category_name
                            ? "bg-purple-600/30 border-purple-400 shadow-[0_0_12px_rgba(168,85,247,0.3)]"
                            : hoveredCategoryIdx === idx
                              ? "bg-white/15 border-white/30"
                              : "bg-white/5 border-white/5 hover:border-white/10"
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <span
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{
                              backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length],
                            }}
                          />
                          <span className="truncate text-white/90">{cat.category_name}</span>
                        </div>
                        <span className="font-mono text-purple-300 shrink-0 ml-2">
                          {cat.percentage}%
                        </span>
                      </div>
                    ))}
                  </div>
                </GlassCard>

                {/* Warehouse Holdings Bar Chart */}
                <GlassCard className="p-6 border-white/10 flex flex-col">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Warehouse className="w-5 h-5 text-sky-400" />
                      <h3 className="font-semibold text-white text-sm">
                        Valuation by Storage Warehouse
                      </h3>
                    </div>
                    <GlassBadge variant="neutral">
                      {valueSummary?.by_warehouse.length || 0} Hubs
                    </GlassBadge>
                  </div>

                  {!valueSummary?.by_warehouse.length ? (
                    <div className="h-64 flex items-center justify-center text-xs text-white/40">
                      No warehouse stock data available
                    </div>
                  ) : (
                    <div className="h-72 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={valueSummary.by_warehouse}
                          margin={{ top: 10, right: 10, left: 10, bottom: 20 }}
                        >
                          <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="rgba(255,255,255,0.06)"
                            vertical={false}
                          />
                          <XAxis
                            dataKey="warehouse_name"
                            stroke="rgba(255,255,255,0.4)"
                            fontSize={11}
                            tickLine={false}
                          />
                          <YAxis
                            stroke="rgba(255,255,255,0.4)"
                            fontSize={11}
                            tickLine={false}
                            tickFormatter={(val) => `₹${val.toLocaleString()}`}
                          />
                          <Tooltip content={<CustomChartTooltip />} />
                          <Bar dataKey="total_value" fill="#38bdf8" radius={[6, 6, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Warehouse Stats Footer */}
                  <div className="mt-4 grid grid-cols-2 gap-2">
                    {valueSummary?.by_warehouse.map((wh) => (
                      <div
                        key={wh.warehouse_id}
                        className="p-2 rounded-xl bg-white/5 border border-white/5 text-xs font-mono hover:border-sky-400/30 transition-colors"
                      >
                        <div className="text-white/60 text-[11px] truncate">
                          {wh.warehouse_name}
                        </div>
                        <div className="text-white font-bold">
                          ₹{wh.total_value.toLocaleString()}
                        </div>
                        <div className="text-sky-400 text-[10px]">
                          {wh.total_units} units ({wh.batch_count} batches)
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </div>

              {/* ROW 2: Top 10 Capital Products + Stock Health Bands */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top Products by Capital with Interactive Filtering */}
                <GlassCard className="p-6 border-white/10">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Layers className="w-5 h-5 text-amber-400" />
                      <h3 className="font-semibold text-white text-sm">
                        Top 10 Products by Capital Tied Up
                      </h3>
                    </div>
                    <div className="flex items-center gap-2">
                      {selectedCategoryFilter && (
                        <span className="text-[10px] text-amber-400 font-mono">
                          Category: {selectedCategoryFilter}
                        </span>
                      )}
                      <span className="text-xs text-white/50 font-mono">Σ Top Value</span>
                    </div>
                  </div>

                  {!filteredTopProducts.length ? (
                    <div className="py-12 text-center text-xs text-white/40">
                      No matching product inventory records
                    </div>
                  ) : (
                    <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                      {filteredTopProducts.map((item, idx) => (
                        <div
                          key={item.product_id}
                          onClick={() => setSelectedCostSku(item.sku)}
                          className={`flex items-center justify-between p-2.5 rounded-xl border transition-all cursor-pointer ${
                            selectedCostSku === item.sku
                              ? "bg-purple-500/20 border-purple-400/50 shadow-[0_0_15px_rgba(168,85,247,0.2)]"
                              : "bg-white/5 border-white/5 hover:border-white/15"
                          }`}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <span className="w-6 h-6 rounded-lg bg-neutral-900 border border-white/10 text-purple-400 text-xs font-mono font-bold flex items-center justify-center shrink-0">
                              #{idx + 1}
                            </span>
                            <div className="min-w-0">
                              <div className="font-semibold text-white text-xs truncate">
                                {item.name}
                              </div>
                              <div className="text-[10px] text-white/50 font-mono truncate">
                                {item.sku} • {item.category_name}
                              </div>
                            </div>
                          </div>

                          <div className="text-right shrink-0 ml-3">
                            <div className="font-mono font-bold text-xs text-amber-300">
                              ₹{item.total_value.toLocaleString()}
                            </div>
                            <div className="text-[10px] text-white/50 font-mono">
                              {item.total_on_hand} {item.base_uom_name} @ ₹{item.cost_price}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </GlassCard>

                {/* Stock Health & Reorder Distribution */}
                <GlassCard className="p-6 border-white/10 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        <h3 className="font-semibold text-white text-sm">
                          Stock Health & Reorder Thresholds
                        </h3>
                      </div>
                      <span className="text-xs text-white/50 font-mono">
                        {healthDist?.total_products || 0} SKUs
                      </span>
                    </div>

                    {/* Multi-segmented Progress Bar */}
                    <div className="w-full h-4 rounded-full bg-neutral-900 overflow-hidden flex border border-white/10 mb-6">
                      <div
                        style={{
                          width: `${
                            healthDist?.total_products
                              ? ((healthDist.healthy_count || 0) / healthDist.total_products) * 100
                              : 0
                          }%`,
                        }}
                        className="h-full bg-emerald-500 transition-all duration-500"
                        title={`Healthy: ${healthDist?.healthy_count || 0}`}
                      />
                      <div
                        style={{
                          width: `${
                            healthDist?.total_products
                              ? ((healthDist.low_count || 0) / healthDist.total_products) * 100
                              : 0
                          }%`,
                        }}
                        className="h-full bg-amber-500 transition-all duration-500"
                        title={`Low: ${healthDist?.low_count || 0}`}
                      />
                      <div
                        style={{
                          width: `${
                            healthDist?.total_products
                              ? ((healthDist.critical_count || 0) / healthDist.total_products) * 100
                              : 0
                          }%`,
                        }}
                        className="h-full bg-rose-500 transition-all duration-500"
                        title={`Critical: ${healthDist?.critical_count || 0}`}
                      />
                      <div
                        style={{
                          width: `${
                            healthDist?.total_products
                              ? ((healthDist.out_of_stock_count || 0) / healthDist.total_products) *
                                100
                              : 0
                          }%`,
                        }}
                        className="h-full bg-neutral-600 transition-all duration-500"
                        title={`Out of Stock: ${healthDist?.out_of_stock_count || 0}`}
                      />
                    </div>

                    {/* Health Cards */}
                    <div className="grid grid-cols-2 gap-3">
                      {healthDist?.bands.map((band) => {
                        let colorClass = "border-emerald-500/20 text-emerald-400";
                        if (band.status === "low") {
                          colorClass = "border-amber-500/20 text-amber-400";
                        } else if (band.status === "critical") {
                          colorClass = "border-rose-500/20 text-rose-400";
                        } else if (band.status === "out_of_stock") {
                          colorClass = "border-neutral-700 text-neutral-400";
                        }

                        return (
                          <div
                            key={band.status}
                            className={`p-3 rounded-xl bg-white/5 border ${colorClass} space-y-1`}
                          >
                            <div className="flex justify-between items-center text-xs font-semibold">
                              <span>{band.label}</span>
                              <span className="font-mono">{band.percentage}%</span>
                            </div>
                            <div className="text-xl font-bold font-mono text-white">
                              {band.count}{" "}
                              <span className="text-xs font-sans font-normal text-white/50">
                                SKUs
                              </span>
                            </div>
                            <div className="text-[10px] text-white/50 truncate">
                              {band.description}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-white/60">
                    <span>Thresholds based on Step 5.3 rules</span>
                    <a
                      href="/admin/inventory"
                      className="text-purple-400 hover:text-purple-300 flex items-center gap-1 font-medium transition-colors"
                    >
                      Manage Inventory <ArrowUpRight className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </GlassCard>
              </div>

              {/* ROW 3: Expiry Timeline Horizon */}
              <GlassCard className="p-6 border-white/10">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-purple-400" />
                    <h3 className="font-semibold text-white text-sm">
                      Forward-Looking Batch Expiry Horizon
                    </h3>
                  </div>
                  {expiryTimeline && expiryTimeline.total_expiring_soon_count > 0 && (
                    <GlassBadge variant="error">
                      {expiryTimeline.total_expiring_soon_count} Batches Expiring (₹
                      {expiryTimeline.total_expiring_soon_value.toLocaleString()})
                    </GlassBadge>
                  )}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {expiryTimeline?.windows.map((w) => {
                    let badgeVariant: "error" | "warning" | "success" | "neutral" | "accent" =
                      "neutral";
                    if (w.window_key === "expired") badgeVariant = "error";
                    else if (w.window_key === "this_week") badgeVariant = "error";
                    else if (w.window_key === "this_month") badgeVariant = "warning";
                    else if (w.window_key === "next_3_months") badgeVariant = "accent";
                    else if (w.window_key === "later") badgeVariant = "success";

                    return (
                      <div
                        key={w.window_key}
                        className="p-3 rounded-xl bg-white/5 border border-white/5 flex flex-col justify-between space-y-2 hover:border-white/20 transition-all duration-300"
                      >
                        <div className="flex justify-between items-start">
                          <span className="text-[11px] font-semibold text-white/80">{w.label}</span>
                          <GlassBadge variant={badgeVariant}>{w.batch_count}</GlassBadge>
                        </div>

                        <div>
                          <div className="text-base font-bold font-mono text-white">
                            ₹{w.total_value.toLocaleString()}
                          </div>
                          <div className="text-[10px] text-white/50 font-mono">
                            {w.total_quantity} units
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </GlassCard>
            </div>
          )}

          {/* ============================================================ */}
          {/* SECTION 2: PURCHASING SPEND & TREND INTELLIGENCE (Step 6.2)  */}
          {/* ============================================================ */}
          {(activeTab === "all" || activeTab === "spend") && (
            <div className="space-y-6 pt-6 border-t border-white/10">
              {/* Header & Controls */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                    <Receipt className="w-5 h-5 text-indigo-400" />
                    Purchasing Spend & Cost Trend Intelligence
                  </h2>
                  <p className="text-xs text-white/50 mt-0.5">
                    Visual procurement trends, supplier concentration, and product cost creep over
                    time.
                  </p>
                </div>

                {/* Range Selector */}
                <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-neutral-900/80 border border-white/10">
                  {[6, 12, 24].map((m) => (
                    <button
                      key={m}
                      onClick={() => setSpendMonths(m)}
                      className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                        spendMonths === m
                          ? "bg-purple-600 text-white shadow-lg shadow-purple-600/30"
                          : "text-white/60 hover:text-white hover:bg-white/5"
                      }`}
                    >
                      {m}M Horizon
                    </button>
                  ))}
                </div>
              </div>

              {/* SPEND ROW 1: 12-Month Spend Trend Area Chart */}
              <GlassCard className="p-6 border-white/10 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <LineChartIcon className="w-5 h-5 text-indigo-400" />
                    <div>
                      <h3 className="font-semibold text-white text-sm">
                        Procurement Spend Trend ({spendMonths} Months)
                      </h3>
                      <span className="text-[11px] text-white/50">
                        Total Period Spend: ₹
                        {(spendTrend?.total_period_spend || 0).toLocaleString()} • Avg: ₹
                        {(spendTrend?.avg_monthly_spend || 0).toLocaleString()}/mo
                      </span>
                    </div>
                  </div>
                  <GlassBadge variant={spendTrend?.total_period_spend ? "success" : "neutral"}>
                    {spendTrend?.total_period_spend ? "Active Spend" : "Pre-Phase 6 Empty State"}
                  </GlassBadge>
                </div>

                {/* Chart or Clean Empty State */}
                {!spendTrend?.total_period_spend ? (
                  <EmptySpendState
                    title="No Purchase Order Spend Data Yet"
                    description="Monthly spend on received stock will populate here automatically once purchase orders are received in Phase 6."
                  />
                ) : (
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={spendTrend.monthly_trend}
                        margin={{ top: 10, right: 10, left: 10, bottom: 20 }}
                      >
                        <defs>
                          <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="rgba(255,255,255,0.06)"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="label"
                          stroke="rgba(255,255,255,0.4)"
                          fontSize={11}
                          tickLine={false}
                        />
                        <YAxis
                          stroke="rgba(255,255,255,0.4)"
                          fontSize={11}
                          tickLine={false}
                          tickFormatter={(val) => `₹${val.toLocaleString()}`}
                        />
                        <Tooltip content={<CustomChartTooltip />} />
                        <Area
                          type="monotone"
                          dataKey="total_spend"
                          stroke="#8b5cf6"
                          strokeWidth={3}
                          fillOpacity={1}
                          fill="url(#spendGradient)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </GlassCard>

              {/* SPEND ROW 2: Spend by Supplier + Spend by Category */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Spend by Supplier */}
                <GlassCard className="p-6 border-white/10 flex flex-col">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Building2 className="w-5 h-5 text-emerald-400" />
                      <h3 className="font-semibold text-white text-sm">
                        Purchasing Spend by Supplier
                      </h3>
                    </div>
                    <GlassBadge variant="neutral">
                      {spendBySupplier?.suppliers.length || 0} Vendors
                    </GlassBadge>
                  </div>

                  {!spendBySupplier?.suppliers.length || !spendBySupplier.total_spend ? (
                    <EmptySpendState
                      title="No Supplier Procurement Records"
                      description="Supplier spend rankings and volume allocations will populate once vendor purchase orders are created."
                    />
                  ) : (
                    <div className="space-y-4">
                      <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={spendBySupplier.suppliers}
                            layout="vertical"
                            margin={{ top: 10, right: 10, left: 20, bottom: 10 }}
                          >
                            <CartesianGrid
                              strokeDasharray="3 3"
                              stroke="rgba(255,255,255,0.06)"
                              horizontal={false}
                            />
                            <XAxis
                              type="number"
                              stroke="rgba(255,255,255,0.4)"
                              fontSize={11}
                              tickLine={false}
                              tickFormatter={(val) => `₹${val.toLocaleString()}`}
                            />
                            <YAxis
                              type="category"
                              dataKey="supplier_name"
                              stroke="rgba(255,255,255,0.4)"
                              fontSize={11}
                              tickLine={false}
                              width={100}
                            />
                            <Tooltip content={<CustomChartTooltip />} />
                            <Bar dataKey="total_spend" fill="#10b981" radius={[0, 6, 6, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>

                      <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto pr-1">
                        {spendBySupplier.suppliers.map((sup) => (
                          <div
                            key={sup.supplier_id}
                            className="flex items-center justify-between p-2 rounded-xl bg-white/5 border border-white/5 text-xs font-mono"
                          >
                            <div className="truncate text-white/80">{sup.supplier_name}</div>
                            <span className="font-bold text-emerald-400 ml-2">
                              ₹{sup.total_spend.toLocaleString()} ({sup.percentage}%)
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </GlassCard>

                {/* Spend by Category */}
                <GlassCard className="p-6 border-white/10 flex flex-col">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Tag className="w-5 h-5 text-amber-400" />
                      <h3 className="font-semibold text-white text-sm">
                        Purchasing Spend by Category
                      </h3>
                    </div>
                    <GlassBadge variant="neutral">
                      {spendByCategory?.categories.length || 0} Categories
                    </GlassBadge>
                  </div>

                  {!spendByCategory?.categories.length || !spendByCategory.total_spend ? (
                    <EmptySpendState
                      title="No Category Spend Breakdown"
                      description="Category capital flows will automatically aggregate here as purchase order items are processed."
                    />
                  ) : (
                    <div className="space-y-4">
                      <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={spendByCategory.categories}
                              dataKey="total_spend"
                              nameKey="category_name"
                              cx="50%"
                              cy="50%"
                              innerRadius={55}
                              outerRadius={85}
                              paddingAngle={4}
                            >
                              {spendByCategory.categories.map((_, index) => (
                                <Cell
                                  key={`spend-cat-cell-${index}`}
                                  fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                                  stroke="rgba(0,0,0,0.4)"
                                  strokeWidth={2}
                                />
                              ))}
                            </Pie>
                            <Tooltip content={<CustomChartTooltip />} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>

                      <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto pr-1">
                        {spendByCategory.categories.map((cat, idx) => (
                          <div
                            key={cat.category_name}
                            className="flex items-center justify-between p-2 rounded-xl bg-white/5 border border-white/5 text-xs font-mono"
                          >
                            <div className="flex items-center gap-2 truncate">
                              <span
                                className="w-2.5 h-2.5 rounded-full shrink-0"
                                style={{
                                  backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length],
                                }}
                              />
                              <span className="truncate text-white/80">{cat.category_name}</span>
                            </div>
                            <span className="font-bold text-amber-400 ml-2">{cat.percentage}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </GlassCard>
              </div>

              {/* SPEND ROW 3: Average Product Cost Evolution Tracker */}
              <GlassCard className="p-6 border-white/10">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-400" />
                    <div>
                      <h3 className="font-semibold text-white text-sm">
                        Product Cost Price Evolution & Price Creep
                      </h3>
                      <p className="text-xs text-white/50">
                        Track supplier unit cost movements against initial catalog baseline.
                      </p>
                    </div>
                  </div>

                  {/* Product Selector */}
                  {avgCostTrend && avgCostTrend.products.length > 0 && (
                    <div className="flex items-center gap-2">
                      <label
                        htmlFor="product-sku-select"
                        className="text-xs text-white/60 font-medium shrink-0"
                      >
                        Inspect SKU:
                      </label>
                      <select
                        id="product-sku-select"
                        value={selectedCostSku || activeProductCost?.sku || ""}
                        onChange={(e) => setSelectedCostSku(e.target.value)}
                        className="bg-neutral-900 border border-white/20 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      >
                        {avgCostTrend.products.map((p) => (
                          <option key={p.product_id} value={p.sku}>
                            {p.sku} — {p.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>

                {!activeProductCost ? (
                  <div className="py-12 text-center text-xs text-white/40">
                    No active product cost history available.
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Product Cost Header Card */}
                    <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-white/5 border border-white/10">
                      <div>
                        <div className="text-xs text-white/50 font-mono">
                          {activeProductCost.sku}
                        </div>
                        <div className="text-base font-bold text-white">
                          {activeProductCost.name}
                        </div>
                      </div>

                      <div className="flex items-center gap-4 text-xs font-mono">
                        <div>
                          <span className="text-white/50 block text-[10px]">Current Cost</span>
                          <span className="text-white font-bold text-sm">
                            ₹{activeProductCost.current_cost_price}
                          </span>
                        </div>

                        <div>
                          <span className="text-white/50 block text-[10px]">Price Creep</span>
                          <GlassBadge
                            variant={
                              activeProductCost.pct_change > 0
                                ? "error"
                                : activeProductCost.pct_change < 0
                                  ? "success"
                                  : "neutral"
                            }
                          >
                            {activeProductCost.pct_change > 0 ? "+" : ""}
                            {activeProductCost.pct_change}%
                          </GlassBadge>
                        </div>

                        <div>
                          <span className="text-white/50 block text-[10px]">Recorded Points</span>
                          <span className="text-purple-300 font-bold">
                            {activeProductCost.cost_history.length} Points
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Cost Movement Chart (Flat line or Historical Points) */}
                    <div className="h-64 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                          data={activeProductCost.cost_history.map((pt) => ({
                            date: pt.recorded_at.split("T")[0],
                            cost_price: pt.cost_price,
                            source: pt.source,
                          }))}
                          margin={{ top: 10, right: 10, left: 10, bottom: 20 }}
                        >
                          <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="rgba(255,255,255,0.06)"
                            vertical={false}
                          />
                          <XAxis
                            dataKey="date"
                            stroke="rgba(255,255,255,0.4)"
                            fontSize={11}
                            tickLine={false}
                          />
                          <YAxis
                            stroke="rgba(255,255,255,0.4)"
                            fontSize={11}
                            tickLine={false}
                            domain={["dataMin - 10", "dataMax + 10"]}
                            tickFormatter={(val) => `₹${val}`}
                          />
                          <Tooltip content={<CustomChartTooltip />} />
                          <Line
                            type="monotone"
                            dataKey="cost_price"
                            stroke="#c084fc"
                            strokeWidth={3}
                            dot={{ r: 5, fill: "#c084fc", stroke: "#18181b", strokeWidth: 2 }}
                            activeDot={{ r: 7, fill: "#a855f7" }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-white/50">
                      <Info className="w-4 h-4 text-purple-400 shrink-0" />
                      <span>
                        {activeProductCost.cost_history.length === 1
                          ? "Single baseline cost recorded. Chart will plot future vendor price adjustments as POs are received."
                          : `Showing historical cost price adjustments across ${activeProductCost.cost_history.length} transactions.`}
                      </span>
                    </div>
                  </div>
                )}
              </GlassCard>
            </div>
          )}
        </div>
      )}
    </>
  );

  return (
    <AppLayout>
      <DashboardTemplate
        title="Stock Valuation & Purchasing Intelligence"
        description="Comprehensive inventory capital metrics, warehouse allocations, batch expiry, and 12-month purchasing spend trends."
        customKpiSlot={kpiCardsContent}
        mainContent={mainDashboardContent}
      />
    </AppLayout>
  );
}
