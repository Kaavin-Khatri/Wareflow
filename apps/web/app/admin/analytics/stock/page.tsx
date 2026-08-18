"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassBadge } from "@/components/glass/GlassBadge";
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
} from "recharts";

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
      </div>
    );
  }
  return null;
}

export default function StockAnalyticsPage() {
  const [valueSummary, setValueSummary] = useState<StockValueSummary | null>(null);
  const [healthDist, setHealthDist] = useState<StockHealthDistribution | null>(null);
  const [topProducts, setTopProducts] = useState<TopProductsResponse | null>(null);
  const [expiryTimeline, setExpiryTimeline] = useState<ExpiryTimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    async function loadAnalytics() {
      try {
        setLoading(true);
        setError(null);
        const [valData, healthData, topData, expData] = await Promise.all([
          apiClient.get<StockValueSummary>("/analytics/stock/value-summary"),
          apiClient.get<StockHealthDistribution>("/analytics/stock/health-distribution"),
          apiClient.get<TopProductsResponse>("/analytics/stock/top-value-products?limit=10"),
          apiClient.get<ExpiryTimelineResponse>("/analytics/stock/expiry-timeline"),
        ]);

        if (!ignore) {
          setValueSummary(valData);
          setHealthDist(healthData);
          setTopProducts(topData);
          setExpiryTimeline(expData);
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
  }, []);

  const kpiCardsContent = (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* KPI 1: Total Valuation */}
      <GlassCard className="p-4 border-purple-500/20 bg-purple-500/5 relative overflow-hidden">
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
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center shrink-0">
            <TrendingUp className="w-5 h-5 text-purple-400" />
          </div>
        </div>
      </GlassCard>

      {/* KPI 2: Total Units On-Hand */}
      <GlassCard className="p-4 border-white/10 relative overflow-hidden">
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
          <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0">
            <Boxes className="w-5 h-5 text-white/70" />
          </div>
        </div>
      </GlassCard>

      {/* KPI 3: Healthy Stock Ratio */}
      <GlassCard className="p-4 border-emerald-500/20 bg-emerald-500/5 relative overflow-hidden">
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
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
        </div>
      </GlassCard>

      {/* KPI 4: Action Required (Low & Critical & Out) */}
      <GlassCard className="p-4 border-rose-500/20 bg-rose-500/5 relative overflow-hidden">
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
          <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5 text-rose-400" />
          </div>
        </div>
      </GlassCard>
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
        <div className="py-24 text-center text-sm text-white/40">
          Calculating live inventory valuations and distributions...
        </div>
      ) : (
        <div className="space-y-6">
          {/* ROW 1: Donut (Category) + Bar (Warehouse) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Category Composition Donut */}
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
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={valueSummary.by_category}
                        dataKey="total_value"
                        nameKey="category_name"
                        cx="50%"
                        cy="50%"
                        innerRadius={65}
                        outerRadius={95}
                        paddingAngle={4}
                      >
                        {valueSummary.by_category.map((_, index) => (
                          <Cell
                            key={`cat-cell-${index}`}
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
              )}

              {/* Legend list */}
              <div className="mt-4 grid grid-cols-2 gap-2 max-h-32 overflow-y-auto pr-1">
                {valueSummary?.by_category.map((cat, idx) => (
                  <div
                    key={cat.category_name}
                    className="flex items-center justify-between text-xs p-1.5 rounded-lg bg-white/5 border border-white/5"
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
                    className="p-2 rounded-xl bg-white/5 border border-white/5 text-xs font-mono"
                  >
                    <div className="text-white/60 text-[11px] truncate">{wh.warehouse_name}</div>
                    <div className="text-white font-bold">₹{wh.total_value.toLocaleString()}</div>
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
            {/* Top Products by Capital */}
            <GlassCard className="p-6 border-white/10">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Layers className="w-5 h-5 text-amber-400" />
                  <h3 className="font-semibold text-white text-sm">
                    Top 10 Products by Capital Tied Up
                  </h3>
                </div>
                <span className="text-xs text-white/50 font-mono">Σ Top Value</span>
              </div>

              {!topProducts?.by_value.length ? (
                <div className="py-12 text-center text-xs text-white/40">
                  No active product inventory records
                </div>
              ) : (
                <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                  {topProducts.by_value.map((item, idx) => (
                    <div
                      key={item.product_id}
                      className="flex items-center justify-between p-2.5 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors"
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
                          ? ((healthDist.out_of_stock_count || 0) / healthDist.total_products) * 100
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
                          <span className="text-xs font-sans font-normal text-white/50">SKUs</span>
                        </div>
                        <div className="text-[10px] text-white/50 truncate">{band.description}</div>
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
                    className="p-3 rounded-xl bg-white/5 border border-white/5 flex flex-col justify-between space-y-2"
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
    </>
  );

  return (
    <AppLayout>
      <DashboardTemplate
        title="Stock Valuation & Composition Analytics"
        description="Real-time balance valuation, capital concentration by category, warehouse holdings, and batch expiry horizons."
        customKpiSlot={kpiCardsContent}
        mainContent={mainDashboardContent}
      />
    </AppLayout>
  );
}
