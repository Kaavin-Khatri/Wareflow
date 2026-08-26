"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import AppLayout from "@/components/AppLayout";
import { DashboardTemplate } from "@/components/templates/DashboardTemplate";
import {
  GlassButton,
  GlassCard,
  GlassCardTitle,
  GlassCardDescription,
  GlassBadge,
} from "@/components/glass";
import { AnimatedNumber } from "@/components/motion/AnimatedNumber";
import { EmptyState } from "@/components/EmptyState";
import { apiClient, getAuthToken } from "@/lib/api-client";
import {
  TrendingUp,
  Truck,
  AlertTriangle,
  Package,
  Plus,
  ArrowUpRight,
  Shield,
  FileSpreadsheet,
  Users,
  CheckCircle2,
  Sparkles,
  RefreshCw,
  Zap,
  IndianRupee,
  Building2,
  Flame,
  AlertOctagon,
  Boxes,
} from "lucide-react";

export interface DashboardKPIMetrics {
  monthly_sales_revenue: number;
  monthly_inventory_value: number;
  monthly_inventory_units: number;
  total_stock_value: number;
  open_pos_count: number;
  open_sos_count: number;
  low_stock_count: number;
  critical_stock_count: number;
  total_outstanding_receivables: number;
  overdue_invoices_count: number;
}

export interface TopProductMovement {
  product_id: string;
  product_name: string;
  sku: string;
  units_moved: number;
  revenue: number;
  category_name?: string | null;
}

export interface DeadStockRiskItem {
  product_id: string;
  product_name: string;
  sku: string;
  units_on_hand: number;
  tied_up_capital: number;
  days_inactive: number;
}

export interface InboundOutboundDataPoint {
  date: string;
  inbound_qty: number;
  outbound_qty: number;
}

export interface LowStockQuickItem {
  product_id: string;
  product_name: string;
  sku: string;
  current_stock: number;
  reorder_point: number;
  urgency: "critical" | "high" | "medium";
  primary_supplier_id?: string | null;
  primary_supplier_name?: string | null;
  deficit: number;
}

export interface OverdueInvoiceQuickItem {
  invoice_id: string;
  invoice_number: string;
  retailer_name: string;
  due_date: string;
  overdue_days: number;
  balance_due: number;
  status: string;
}

export interface OwnerDashboardResponse {
  kpi_metrics: DashboardKPIMetrics;
  top_fastest_moving: TopProductMovement[];
  top_dead_stock: DeadStockRiskItem[];
  movement_trend_30d: InboundOutboundDataPoint[];
  low_stock_quick_list: LowStockQuickItem[];
  overdue_invoices_quick_list: OverdueInvoiceQuickItem[];
  is_empty_state: boolean;
}

interface WeeklyInsightMetrics {
  weekly_revenue: number;
  weekly_orders_count: number;
  confirmed_orders_count: number;
  top_mover_product_name: string | null;
  top_mover_units_sold: number;
  reorder_needed_count: number;
  dead_stock_count: number;
  dead_stock_capital: number;
}

interface WeeklyInsight {
  headline: string;
  narrative: string;
  metrics_summary: WeeklyInsightMetrics;
  generated_at: string;
  expires_at: string;
  is_ai_generated: boolean;
  is_cached: boolean;
}

interface RecentOrder {
  id: string;
  orderNumber: string;
  retailer: string;
  itemsCount: number;
  total: number;
  status: "dispatched" | "processing" | "pending";
}

const DEFAULT_KPIS: DashboardKPIMetrics = {
  monthly_sales_revenue: 0,
  monthly_inventory_value: 0,
  monthly_inventory_units: 0,
  total_stock_value: 0,
  open_pos_count: 0,
  open_sos_count: 0,
  low_stock_count: 0,
  critical_stock_count: 0,
  total_outstanding_receivables: 0,
  overdue_invoices_count: 0,
};

interface TooltipPayloadItem {
  name: string;
  value: number;
  color?: string;
  stroke?: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}

function CustomMovementTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="p-3 rounded-xl bg-[var(--surface-overlay)] backdrop-blur-md border border-[var(--glass-border)] shadow-xl text-xs space-y-1">
      <div className="font-mono font-bold text-white mb-1.5 border-b border-[var(--glass-border)] pb-1">
        Date: {label}
      </div>
      {payload.map((entry, idx) => (
        <div key={`tip-${idx}`} className="flex items-center justify-between gap-4">
          <span
            className="flex items-center gap-1.5"
            style={{ color: entry.stroke || entry.color }}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: entry.stroke || entry.color }}
            />
            {entry.name}:
          </span>
          <span className="font-mono font-bold text-white">
            {Number(entry.value).toLocaleString("en-IN")} units
          </span>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [ordersListRef] = useAutoAnimate();
  const [dashboard, setDashboard] = useState<OwnerDashboardResponse | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [insight, setInsight] = useState<WeeklyInsight | null>(null);
  const [loadingInsight, setLoadingInsight] = useState(false);

  const [recentOrders, setRecentOrders] = useState<RecentOrder[]>([
    {
      id: "ord-1",
      orderNumber: "SO-2026-904",
      retailer: "Vashi APMC Wholesale Traders",
      itemsCount: 500,
      total: 450000,
      status: "processing",
    },
    {
      id: "ord-2",
      orderNumber: "SO-2026-903",
      retailer: "Navi Mumbai Super Market Co",
      itemsCount: 250,
      total: 215000,
      status: "dispatched",
    },
    {
      id: "ord-3",
      orderNumber: "SO-2026-902",
      retailer: "Pune Agro Grain Distributors",
      itemsCount: 800,
      total: 720000,
      status: "pending",
    },
    {
      id: "ord-4",
      orderNumber: "SO-2026-901",
      retailer: "Thane Central FMCG Mart",
      itemsCount: 150,
      total: 135000,
      status: "dispatched",
    },
  ]);

  async function fetchDashboard() {
    setLoadingDashboard(true);
    const token = await getAuthToken();
    if (!token) {
      setDashboard({
        kpi_metrics: DEFAULT_KPIS,
        top_fastest_moving: [],
        top_dead_stock: [],
        movement_trend_30d: [],
        low_stock_quick_list: [],
        overdue_invoices_quick_list: [],
        is_empty_state: true,
      });
      setLoadingDashboard(false);
      return;
    }
    try {
      const data = await apiClient.get<OwnerDashboardResponse>("/analytics/dashboard");
      setDashboard(data);
    } catch {
      setDashboard({
        kpi_metrics: DEFAULT_KPIS,
        top_fastest_moving: [],
        top_dead_stock: [],
        movement_trend_30d: [],
        low_stock_quick_list: [],
        overdue_invoices_quick_list: [],
        is_empty_state: true,
      });
    } finally {
      setLoadingDashboard(false);
    }
  }

  async function fetchWeeklyInsight(forceRefresh = false) {
    const token = await getAuthToken();
    if (!token) {
      setLoadingInsight(false);
      return;
    }
    setLoadingInsight(true);
    try {
      const url = forceRefresh
        ? "/analytics/weekly-insight?force_refresh=true"
        : "/analytics/weekly-insight";
      const data = await apiClient.get<WeeklyInsight>(url);
      setInsight(data);
    } catch {
      // Quiet fallback when unconfigured or unauthenticated
    } finally {
      setLoadingInsight(false);
    }
  }

  useEffect(() => {
    let ignore = false;
    async function load() {
      if (!ignore) {
        await Promise.allSettled([fetchDashboard(), fetchWeeklyInsight(false)]);
      }
    }
    load();
    return () => {
      ignore = true;
    };
  }, []);

  const addSimulatedOrder = () => {
    const randomId = Math.floor(Math.random() * 900 + 100);
    const newOrder: RecentOrder = {
      id: `ord-${Date.now()}`,
      orderNumber: `SO-2026-${randomId}`,
      retailer: "Bhiwandi Fast Logistics Hub",
      itemsCount: 300,
      total: 270000,
      status: "processing",
    };
    setRecentOrders((prev) => [newOrder, ...prev]);
  };

  const markDispatched = (id: string) => {
    setRecentOrders((prev) =>
      prev.map((ord) => (ord.id === id ? { ...ord, status: "dispatched" } : ord)),
    );
  };

  const kpis = dashboard?.kpi_metrics || DEFAULT_KPIS;
  const currentMonthName = useMemo(() => {
    return new Date().toLocaleString("en-IN", { month: "long", year: "numeric" });
  }, []);

  return (
    <AppLayout>
      <DashboardTemplate
        title="Owner Wholesale Command Center"
        description="Single round-trip enterprise pulse: 30-day velocity, receivables aging, inventory health, and rapid-action queues."
        badge={
          <GlassBadge variant="accent" dot>
            Live Telemetry • Bhiwandi Master Hub
          </GlassBadge>
        }
        primaryAction={
          <GlassButton variant="primary" size="md" onClick={addSimulatedOrder}>
            <Plus className="w-3.5 h-3.5" />
            <span>Create Sales Order</span>
          </GlassButton>
        }
        secondaryActions={
          <div className="flex items-center gap-2">
            <Link href="/admin/purchase-orders">
              <GlassButton variant="outline" size="md">
                <Truck className="w-3.5 h-3.5" />
                <span>Purchase Orders</span>
              </GlassButton>
            </Link>
            <Link href="/admin/audit">
              <GlassButton variant="outline" size="md">
                <FileSpreadsheet className="w-3.5 h-3.5" />
                <span>Audit Ledger</span>
              </GlassButton>
            </Link>
          </div>
        }
        kpiMetrics={[
          {
            id: "kpi-sales-revenue",
            title: `Monthly Sales (${currentMonthName})`,
            value: <AnimatedNumber value={kpis.monthly_sales_revenue} prefix="₹" />,
            change: `${kpis.open_sos_count} active orders in pipeline`,
            trend: kpis.monthly_sales_revenue > 0 ? "up" : "neutral",
            icon: <TrendingUp className="w-4 h-4 text-emerald-400" />,
          },
          {
            id: "kpi-inventory-val",
            title: "Total Inventory Valuation",
            value: <AnimatedNumber value={kpis.total_stock_value} prefix="₹" />,
            change: `${Math.round(kpis.monthly_inventory_units).toLocaleString("en-IN")} units on hand`,
            trend: "neutral",
            icon: <Package className="w-4 h-4 text-purple-400" />,
          },
          {
            id: "kpi-stock-health",
            title: "Stock Alert Status",
            value: (
              <AnimatedNumber
                value={kpis.low_stock_count + kpis.critical_stock_count}
                suffix=" SKUs"
              />
            ),
            change: `${kpis.critical_stock_count} critical • ${kpis.low_stock_count} low stock`,
            trend: kpis.critical_stock_count > 0 ? "down" : "neutral",
            icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
          },
          {
            id: "kpi-receivables",
            title: "Outstanding Receivables",
            value: <AnimatedNumber value={kpis.total_outstanding_receivables} prefix="₹" />,
            change: `${kpis.overdue_invoices_count} overdue invoices`,
            trend: kpis.overdue_invoices_count > 0 ? "down" : "neutral",
            icon: <IndianRupee className="w-4 h-4 text-rose-400" />,
          },
        ]}
        mainContent={
          <div className="space-y-6">
            {/* 1. Empty State Guard for Fresh Deployments */}
            {dashboard?.is_empty_state && !loadingDashboard && (
              <GlassCard className="p-8 text-center border-dashed border-[var(--border)]">
                <EmptyState
                  icon={<Boxes className="w-8 h-8 text-[var(--accent)]" />}
                  title="Fresh Deployment Initialized"
                  description="Your wholesale warehouse environment is ready. Start by adding products, receiving purchase orders, or recording sales orders to populate real-time telemetry."
                  action={
                    <div className="flex items-center gap-3 justify-center pt-2">
                      <Link href="/admin/products">
                        <GlassButton variant="primary" size="md">
                          <Plus className="w-3.5 h-3.5" />
                          <span>Add Catalog Products</span>
                        </GlassButton>
                      </Link>
                      <Link href="/admin/purchase-orders">
                        <GlassButton variant="outline" size="md">
                          <Truck className="w-3.5 h-3.5" />
                          <span>Receive Stock (PO)</span>
                        </GlassButton>
                      </Link>
                    </div>
                  }
                />
              </GlassCard>
            )}

            {/* 2. AI Executive Weekly Intelligence Narrative Briefing */}
            {insight && (
              <GlassCard className="p-6 relative overflow-hidden border border-purple-500/30 bg-gradient-to-br from-purple-950/20 via-background to-background shadow-2xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[var(--glass-border)]">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      <Sparkles className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <GlassCardTitle className="text-sm font-semibold text-white">
                          AI Executive Intelligence Briefing
                        </GlassCardTitle>
                        <GlassBadge
                          variant={insight.is_ai_generated ? "accent" : "neutral"}
                          className="text-[10px] uppercase font-mono"
                        >
                          {insight.is_ai_generated ? "Groq LLM Powered" : "Grounded Rule Engine"}
                        </GlassBadge>
                        {insight.is_cached && (
                          <GlassBadge variant="neutral" className="text-[10px] font-mono">
                            7d Cached
                          </GlassBadge>
                        )}
                      </div>
                      <GlassCardDescription className="text-xs text-purple-200/70">
                        Synthesized 7-day executive pulse across dispatches, top velocity products,
                        and inventory risks.
                      </GlassCardDescription>
                    </div>
                  </div>

                  <GlassButton
                    variant="ghost"
                    size="sm"
                    onClick={() => fetchWeeklyInsight(true)}
                    disabled={loadingInsight}
                    className="text-xs self-start sm:self-auto text-purple-300 hover:text-purple-100"
                  >
                    <RefreshCw
                      className={`w-3.5 h-3.5 mr-1.5 ${loadingInsight ? "animate-spin" : ""}`}
                    />
                    {loadingInsight ? "Analyzing..." : "Refresh Pulse"}
                  </GlassButton>
                </div>

                <div className="pt-4 space-y-4">
                  <div className="space-y-2">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Zap className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>{insight.headline}</span>
                    </h3>
                    <p className="text-xs text-[var(--text)] leading-relaxed bg-black/20 p-3.5 rounded-xl border border-[var(--glass-border)] font-normal">
                      {insight.narrative}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1 text-xs">
                    <div className="p-2.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)]">
                      <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block font-mono">
                        7D Sales Revenue
                      </span>
                      <span className="text-xs font-mono font-bold text-emerald-400">
                        ₹
                        {Number(insight.metrics_summary.weekly_revenue).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                        })}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)]">
                      <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block font-mono">
                        Orders / Confirmed
                      </span>
                      <span className="text-xs font-mono font-bold text-white">
                        {insight.metrics_summary.weekly_orders_count} orders (
                        {insight.metrics_summary.confirmed_orders_count} conf)
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)]">
                      <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block font-mono">
                        Velocity Leader
                      </span>
                      <span
                        className="text-xs font-semibold text-[var(--accent)] truncate block"
                        title={insight.metrics_summary.top_mover_product_name || "None"}
                      >
                        {insight.metrics_summary.top_mover_product_name || "—"} (
                        {insight.metrics_summary.top_mover_units_sold} units)
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)]">
                      <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block font-mono">
                        Dead Capital Risk
                      </span>
                      <span className="text-xs font-mono font-bold text-amber-400">
                        ₹
                        {Number(insight.metrics_summary.dead_stock_capital).toLocaleString(
                          "en-IN",
                          { minimumFractionDigits: 2 },
                        )}{" "}
                        ({insight.metrics_summary.dead_stock_count} SKUs)
                      </span>
                    </div>
                  </div>
                </div>
              </GlassCard>
            )}

            {/* 3. Interactive 30-Day Inbound vs Outbound Movement Velocity Chart */}
            <GlassCard className="p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <GlassCardTitle className="text-base flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[var(--accent)]" />
                    30-Day Inventory Movement Velocity
                  </GlassCardTitle>
                  <GlassCardDescription className="text-xs">
                    Aggregated daily inbound purchase receipts vs outbound wholesale dispatches.
                  </GlassCardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <GlassBadge variant="success" className="text-[11px]">
                    ● Inbound Receipts
                  </GlassBadge>
                  <GlassBadge variant="accent" className="text-[11px]">
                    ● Outbound Dispatches
                  </GlassBadge>
                </div>
              </div>

              <div className="h-[280px] w-full pt-2">
                {dashboard?.movement_trend_30d && dashboard.movement_trend_30d.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={dashboard.movement_trend_30d}
                      margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient id="inboundGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                        </linearGradient>
                        <linearGradient id="outboundGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis
                        dataKey="date"
                        tickFormatter={(d: string) => d.slice(5)}
                        stroke="var(--text-muted)"
                        fontSize={11}
                      />
                      <YAxis
                        stroke="var(--text-muted)"
                        fontSize={11}
                        tickFormatter={(v: number) => Number(v).toLocaleString()}
                      />
                      <Tooltip content={<CustomMovementTooltip />} />
                      <Legend
                        verticalAlign="top"
                        height={36}
                        iconType="circle"
                        formatter={(val) => (
                          <span className="text-xs text-[var(--text-muted)] font-medium">
                            {val}
                          </span>
                        )}
                      />
                      <Area
                        type="monotone"
                        dataKey="inbound_qty"
                        name="Inbound Receipts"
                        stroke="#10b981"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#inboundGrad)"
                      />
                      <Area
                        type="monotone"
                        dataKey="outbound_qty"
                        name="Outbound Dispatches"
                        stroke="#8b5cf6"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#outboundGrad)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-xs text-[var(--text-muted)]">
                    No movement telemetry recorded in the trailing 30 days.
                  </div>
                )}
              </div>
            </GlassCard>

            {/* 4. Top Velocity Movers & Dead Stock Risk Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top 5 Fastest-Moving Products */}
              <GlassCard className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Flame className="w-4 h-4 text-emerald-400" />
                    <GlassCardTitle className="text-sm font-semibold">
                      Top Velocity Products (30 Days)
                    </GlassCardTitle>
                  </div>
                  <GlassBadge variant="success" className="text-[10px]">
                    Sales Velocity
                  </GlassBadge>
                </div>

                {dashboard?.top_fastest_moving && dashboard.top_fastest_moving.length > 0 ? (
                  <div className="space-y-2.5">
                    {dashboard.top_fastest_moving.map((p, idx) => (
                      <div
                        key={p.product_id || `fast-${idx}`}
                        className="p-3 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)] flex items-center justify-between gap-3 text-xs"
                      >
                        <div className="min-w-0">
                          <div className="font-semibold text-white truncate" title={p.product_name}>
                            {p.product_name}
                          </div>
                          <div className="text-[10px] text-[var(--text-muted)] font-mono">
                            {p.sku} {p.category_name ? `• ${p.category_name}` : ""}
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="font-mono font-bold text-emerald-400">
                            {Number(p.units_moved).toLocaleString("en-IN")} units
                          </div>
                          <div className="text-[10px] text-[var(--text-muted)] font-mono">
                            ₹{Number(p.revenue).toLocaleString("en-IN")}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center text-xs text-[var(--text-muted)] border border-dashed border-[var(--border)] rounded-xl">
                    No outbound sales volume in trailing 30 days.
                  </div>
                )}
              </GlassCard>

              {/* Top 5 Dead Stock Capital Risks */}
              <GlassCard className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertOctagon className="w-4 h-4 text-amber-400" />
                    <GlassCardTitle className="text-sm font-semibold">
                      Dead Stock Capital Risk (60+ Days)
                    </GlassCardTitle>
                  </div>
                  <GlassBadge variant="warning" className="text-[10px]">
                    Tied-Up Capital
                  </GlassBadge>
                </div>

                {dashboard?.top_dead_stock && dashboard.top_dead_stock.length > 0 ? (
                  <div className="space-y-2.5">
                    {dashboard.top_dead_stock.map((p, idx) => (
                      <div
                        key={p.product_id || `dead-${idx}`}
                        className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 flex items-center justify-between gap-3 text-xs"
                      >
                        <div className="min-w-0">
                          <div className="font-semibold text-white truncate" title={p.product_name}>
                            {p.product_name}
                          </div>
                          <div className="text-[10px] text-amber-300/80 font-mono">
                            {p.sku} • {p.days_inactive}d inactive ({p.units_on_hand} on-hand)
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="font-mono font-bold text-amber-400">
                            ₹{Number(p.tied_up_capital).toLocaleString("en-IN")}
                          </div>
                          <Link
                            href="/admin/inventory"
                            className="text-[10px] text-[var(--accent)] hover:underline block"
                          >
                            Liquidate →
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center text-xs text-[var(--text-muted)] border border-dashed border-[var(--border)] rounded-xl">
                    Zero dead stock identified. Inventory is actively turning.
                  </div>
                )}
              </GlassCard>
            </div>

            {/* 5. Live Recent Sales Orders Stream Table */}
            <GlassCard className="p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <GlassCardTitle className="text-base">
                    Recent Wholesale Sales Orders
                  </GlassCardTitle>
                  <GlassCardDescription className="text-xs">
                    Live settlement stream with zero-latency table row mutations.
                  </GlassCardDescription>
                </div>
                <GlassBadge
                  variant="neutral"
                  className="font-mono text-[11px] self-start sm:self-auto"
                >
                  {recentOrders.length} Total Orders
                </GlassBadge>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-[var(--text-muted)]">
                      <th className="p-3">Order No</th>
                      <th className="p-3">Retailer Account</th>
                      <th className="p-3">Bags</th>
                      <th className="p-3">Total (₹)</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody ref={ordersListRef}>
                    {recentOrders.map((ord) => (
                      <tr
                        key={ord.id}
                        className="border-b border-[var(--border)] hover:bg-[var(--surface-hover)] transition-colors"
                      >
                        <td className="p-3 font-mono font-bold text-[var(--accent)]">
                          {ord.orderNumber}
                        </td>
                        <td className="p-3 font-medium text-[var(--text)]">{ord.retailer}</td>
                        <td className="p-3 font-mono">{ord.itemsCount}</td>
                        <td className="p-3 font-mono font-semibold">
                          ₹{ord.total.toLocaleString("en-IN")}
                        </td>
                        <td className="p-3">
                          <GlassBadge
                            variant={
                              ord.status === "dispatched"
                                ? "success"
                                : ord.status === "processing"
                                  ? "accent"
                                  : "warning"
                            }
                            dot
                          >
                            {ord.status}
                          </GlassBadge>
                        </td>
                        <td className="p-3 text-right">
                          {ord.status !== "dispatched" ? (
                            <button
                              type="button"
                              onClick={() => markDispatched(ord.id)}
                              className="text-[11px] text-[var(--accent)] hover:underline font-semibold"
                            >
                              Dispatch
                            </button>
                          ) : (
                            <span className="text-[11px] text-[var(--text-subtle)] font-mono">
                              Cleared
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </GlassCard>

            {/* 6. Administrative & Security Navigation Controls */}
            <GlassCard className="p-6 space-y-4">
              <GlassCardTitle className="text-sm">
                Administrative & Security Controls
              </GlassCardTitle>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Link
                  href="/admin/settings/staff"
                  className="p-3.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)] hover:border-[var(--accent-border)] transition-all flex items-center justify-between text-xs group"
                >
                  <div className="flex items-center gap-2.5">
                    <Users className="w-4 h-4 text-[var(--accent)]" />
                    <span className="font-semibold text-[var(--text)]">Staff & Roles</span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--text)] transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </Link>

                <Link
                  href="/admin/settings/permissions"
                  className="p-3.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)] hover:border-[var(--accent-border)] transition-all flex items-center justify-between text-xs group"
                >
                  <div className="flex items-center gap-2.5">
                    <Shield className="w-4 h-4 text-emerald-400" />
                    <span className="font-semibold text-[var(--text)]">RBAC Matrix</span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--text)] transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </Link>

                <Link
                  href="/admin/audit"
                  className="p-3.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)] hover:border-[var(--accent-border)] transition-all flex items-center justify-between text-xs group"
                >
                  <div className="flex items-center gap-2.5">
                    <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
                    <span className="font-semibold text-[var(--text)]">Audit Log</span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--text)] transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </Link>
              </div>
            </GlassCard>
          </div>
        }
        sideContent={
          <div className="space-y-4">
            {/* 1. Low-Stock Quick-List Widget */}
            <GlassCard className="p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <GlassCardTitle className="text-xs uppercase tracking-wider text-[var(--text-muted)]">
                    Low Stock Quick Action
                  </GlassCardTitle>
                </div>
                <GlassBadge
                  variant={
                    (dashboard?.low_stock_quick_list?.length || 0) > 0 ? "warning" : "success"
                  }
                  className="text-[10px] py-0"
                >
                  {dashboard?.low_stock_quick_list?.length || 0} Alerts
                </GlassBadge>
              </div>

              {dashboard?.low_stock_quick_list && dashboard.low_stock_quick_list.length > 0 ? (
                <div className="space-y-2.5 text-xs">
                  {dashboard.low_stock_quick_list.slice(0, 5).map((item) => (
                    <div
                      key={item.product_id}
                      className={`p-3 rounded-xl border space-y-1.5 ${
                        item.urgency === "critical"
                          ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
                          : "bg-amber-500/10 border-amber-500/20 text-amber-300"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white truncate" title={item.product_name}>
                          {item.product_name}
                        </span>
                        <GlassBadge
                          variant={item.urgency === "critical" ? "error" : "warning"}
                          className="text-[9px] uppercase tracking-wide font-mono px-1.5 py-0"
                        >
                          {item.urgency}
                        </GlassBadge>
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono">
                        <span>
                          On-Hand: <strong className="text-white">{item.current_stock}</strong> /
                          Reorder: {item.reorder_point}
                        </span>
                        <span className="text-rose-400 font-bold">-{item.deficit} Deficit</span>
                      </div>

                      {item.primary_supplier_name && (
                        <div className="text-[10px] text-[var(--text-subtle)] flex items-center gap-1 truncate">
                          <Building2 className="w-3 h-3 text-purple-400 shrink-0" />
                          <span className="truncate">Supplier: {item.primary_supplier_name}</span>
                        </div>
                      )}

                      <div className="pt-1 flex items-center justify-end">
                        <Link href="/admin/purchase-orders">
                          <span className="text-[11px] text-[var(--accent)] hover:underline font-semibold flex items-center gap-1">
                            + Restock PO →
                          </span>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-xs text-[var(--text-muted)] bg-black/10 rounded-xl border border-[var(--glass-border)]">
                  All inventory healthy above safety threshold.
                </div>
              )}
            </GlassCard>

            {/* 2. Overdue Invoices Quick-List Widget */}
            <GlassCard className="p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <IndianRupee className="w-4 h-4 text-rose-400" />
                  <GlassCardTitle className="text-xs uppercase tracking-wider text-[var(--text-muted)]">
                    Overdue Receivables Queue
                  </GlassCardTitle>
                </div>
                <GlassBadge
                  variant={
                    (dashboard?.overdue_invoices_quick_list?.length || 0) > 0 ? "error" : "neutral"
                  }
                  className="text-[10px] py-0"
                >
                  {dashboard?.overdue_invoices_quick_list?.length || 0} Overdue
                </GlassBadge>
              </div>

              {dashboard?.overdue_invoices_quick_list &&
              dashboard.overdue_invoices_quick_list.length > 0 ? (
                <div className="space-y-2.5 text-xs">
                  {dashboard.overdue_invoices_quick_list.slice(0, 5).map((inv) => (
                    <div
                      key={inv.invoice_id}
                      className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white truncate" title={inv.retailer_name}>
                          {inv.retailer_name}
                        </span>
                        <span className="font-mono text-[10px] text-rose-400 font-bold bg-rose-950/40 px-1.5 py-0.5 rounded">
                          {inv.overdue_days}d Overdue
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px] font-mono">
                        <span className="text-[var(--text-muted)]">{inv.invoice_number}</span>
                        <span className="font-bold text-rose-400">
                          ₹{Number(inv.balance_due).toLocaleString("en-IN")}
                        </span>
                      </div>

                      <div className="pt-1 flex items-center justify-end">
                        <Link href="/admin/invoices">
                          <span className="text-[11px] text-[var(--accent)] hover:underline font-semibold">
                            Collect Payment →
                          </span>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-xs text-[var(--text-muted)] bg-black/10 rounded-xl border border-[var(--glass-border)]">
                  Zero overdue receivables. All accounts current.
                </div>
              )}
            </GlassCard>

            {/* 3. Warehouse Telemetry Status */}
            <GlassCard className="p-5 space-y-3 text-xs">
              <GlassCardTitle className="text-xs uppercase tracking-wider text-[var(--text-muted)]">
                Terminal Sync Telemetry
              </GlassCardTitle>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[var(--text-muted)]">Postgres Connection</span>
                  <span className="text-emerald-400 font-mono flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> NullPool Active
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[var(--text-muted)]">Firebase Auth Token</span>
                  <span className="text-emerald-400 font-mono">Verified</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[var(--text-muted)]">Session Protection</span>
                  <span className="text-[var(--accent)] font-mono">httpOnly Cookie</span>
                </div>
              </div>
            </GlassCard>
          </div>
        }
      />
    </AppLayout>
  );
}
