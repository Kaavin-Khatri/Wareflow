"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAutoAnimate } from "@formkit/auto-animate/react";
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
import { apiClient } from "@/lib/api-client";
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
  Clock,
  Sparkles,
  RefreshCw,
  Zap,
} from "lucide-react";

interface RecentOrder {
  id: string;
  orderNumber: string;
  retailer: string;
  itemsCount: number;
  total: number;
  status: "dispatched" | "processing" | "pending";
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

export default function DashboardPage() {
  const [ordersListRef] = useAutoAnimate();
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

  async function fetchWeeklyInsight(forceRefresh = false) {
    setLoadingInsight(true);
    try {
      const url = forceRefresh
        ? "/analytics/weekly-insight?force_refresh=true"
        : "/analytics/weekly-insight";
      const data = await apiClient.get<WeeklyInsight>(url);
      setInsight(data);
    } catch (err) {
      console.warn("Weekly insight unavailable or API unconfigured:", err);
    } finally {
      setLoadingInsight(false);
    }
  }

  useEffect(() => {
    let ignore = false;
    async function load() {
      if (!ignore) {
        await fetchWeeklyInsight(false);
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

  return (
    <AppLayout>
      <DashboardTemplate
        title="Wholesale Command Center"
        description="Real-time stock ledger, dispatch velocity, and automated reorder triggers across all distribution terminals."
        badge={
          <GlassBadge variant="accent" dot>
            Live Telemetry • Bhiwandi Hub #1
          </GlassBadge>
        }
        primaryAction={
          <GlassButton variant="primary" size="md" onClick={addSimulatedOrder}>
            <Plus className="w-3.5 h-3.5" />
            <span>Create Sales Order</span>
          </GlassButton>
        }
        secondaryActions={
          <Link href="/admin/audit">
            <GlassButton variant="outline" size="md">
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>Audit Ledger</span>
            </GlassButton>
          </Link>
        }
        kpiMetrics={[
          {
            id: "kpi-revenue",
            title: "Daily Wholesale Revenue",
            value: <AnimatedNumber value={845200} prefix="₹" />,
            change: "+18.4% vs yesterday",
            trend: "up",
            icon: <TrendingUp className="w-4 h-4" />,
          },
          {
            id: "kpi-dispatches",
            title: "Active Vehicle Runs",
            value: <AnimatedNumber value={38} suffix=" Orders" />,
            change: "4 trucks en-route",
            trend: "neutral",
            icon: <Truck className="w-4 h-4" />,
          },
          {
            id: "kpi-low-stock",
            title: "Low Stock Alerts",
            value: <AnimatedNumber value={4} suffix=" SKUs" />,
            change: "2 POs drafted",
            trend: "down",
            icon: <AlertTriangle className="w-4 h-4 text-amber-500" />,
          },
          {
            id: "kpi-inventory",
            title: "Warehouse Bags in Stock",
            value: <AnimatedNumber value={14820} suffix=" bags" />,
            change: "98.2% capacity",
            trend: "up",
            icon: <Package className="w-4 h-4" />,
          },
        ]}
        mainContent={
          <div className="space-y-6">
            {/* AI Owner Weekly Intelligence Narrative Briefing */}
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
                        Synthesized 7-day executive pulse across dispatches, top velocity products, and inventory risks.
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
                  {/* Headline & 2-3 sentence grounded narrative */}
                  <div className="space-y-2">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Zap className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>{insight.headline}</span>
                    </h3>
                    <p className="text-xs text-[var(--text)] leading-relaxed bg-black/20 p-3.5 rounded-xl border border-[var(--glass-border)] font-normal">
                      {insight.narrative}
                    </p>
                  </div>

                  {/* Grounded Underlying Metrics Strip */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1 text-xs">
                    <div className="p-2.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)]">
                      <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block font-mono">
                        7D Sales Revenue
                      </span>
                      <span className="text-xs font-mono font-bold text-emerald-400">
                        ₹{Number(insight.metrics_summary.weekly_revenue).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)]">
                      <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block font-mono">
                        Orders / Confirmed
                      </span>
                      <span className="text-xs font-mono font-bold text-white">
                        {insight.metrics_summary.weekly_orders_count} orders ({insight.metrics_summary.confirmed_orders_count} conf)
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)]">
                      <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block font-mono">
                        Velocity Leader
                      </span>
                      <span className="text-xs font-semibold text-[var(--accent)] truncate block" title={insight.metrics_summary.top_mover_product_name || "None"}>
                        {insight.metrics_summary.top_mover_product_name || "—"} ({insight.metrics_summary.top_mover_units_sold} units)
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)]">
                      <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block font-mono">
                        Dead Capital Risk
                      </span>
                      <span className="text-xs font-mono font-bold text-amber-400">
                        ₹{Number(insight.metrics_summary.dead_stock_capital).toLocaleString("en-IN", { minimumFractionDigits: 2 })} ({insight.metrics_summary.dead_stock_count} SKUs)
                      </span>
                    </div>
                  </div>
                </div>
              </GlassCard>
            )}

            {/* Live Orders Table with AutoAnimate */}
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

            {/* Quick Admin Navigation Shortcuts */}
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
            {/* Urgent Operations Alert Queue */}
            <GlassCard className="p-5 space-y-3">
              <div className="flex items-center justify-between">
                <GlassCardTitle className="text-xs uppercase tracking-wider text-[var(--text-muted)]">
                  Urgent Operations Queue
                </GlassCardTitle>
                <GlassBadge variant="warning" className="text-[10px] py-0">
                  2 Pending
                </GlassBadge>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-amber-400" />
                    Reorder Basmati Export 25kg
                  </div>
                  <p className="text-[11px] text-amber-200/80">
                    Warehouse 1 balance down to 120 bags. Draft PO #894 awaiting approval.
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-violet-500/10 border border-violet-500/20 text-[var(--accent)] space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <Truck className="w-3.5 h-3.5" />
                    Dispatch Truck MH-04-AB-1290
                  </div>
                  <p className="text-[11px] text-[var(--text-muted)]">
                    Route: Bhiwandi Central → APMC Terminal #4.
                  </p>
                </div>
              </div>
            </GlassCard>

            {/* Warehouse Telemetry Status */}
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
