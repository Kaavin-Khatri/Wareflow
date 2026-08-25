"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassButton } from "@/components/glass/GlassButton";
import { AnimatedNumber } from "@/components/motion/AnimatedNumber";
import { EmptyState } from "@/components/EmptyState";
import { apiClient } from "@/lib/api-client";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Package,
  Search,
  ArrowUpDown,
  RefreshCw,
  IndianRupee,
  Calendar,
  Layers,
  ArrowUpRight,
  ExternalLink,
} from "lucide-react";

// --- Types ---
export interface TurnoverItem {
  product_id: string;
  product_name: string;
  sku: string;
  category_name: string | null;
  unit: string;
  current_on_hand: number;
  units_sold: number;
  average_on_hand: number;
  turnover_ratio: number;
  days_of_stock: number;
  turnover_band: "healthy" | "slowing" | "at_risk";
  cost_price: number;
  tied_up_capital: number;
}

export interface TurnoverSummary {
  average_turnover_ratio: number;
  average_days_of_stock: number;
  healthy_count: number;
  slowing_count: number;
  at_risk_count: number;
  total_products: number;
}

export interface TurnoverResponse {
  period: string;
  summary: TurnoverSummary;
  items: TurnoverItem[];
  generated_at: string;
}

type PeriodOption = "7d" | "30d" | "90d" | "12m" | "all";
type BandFilter = "all" | "healthy" | "slowing" | "at_risk";

export default function InventoryTurnoverPage() {
  const [period, setPeriod] = useState<PeriodOption>("30d");
  const [bandFilter, setBandFilter] = useState<BandFilter>("all");
  const [data, setData] = useState<TurnoverResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<keyof TurnoverItem>("turnover_ratio");
  const [sortAsc, setSortAsc] = useState(true); // Default slowest first

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<TurnoverResponse>(`/analytics/turnover?period=${period}`);
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to load inventory turnover analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [period]);

  // Filter & sort
  const filteredAndSortedItems = useMemo(() => {
    if (!data?.items) return [];

    const filtered = data.items.filter((item) => {
      // Band filter
      if (bandFilter !== "all" && item.turnover_band !== bandFilter) {
        return false;
      }
      // Search query
      const q = searchQuery.toLowerCase().trim();
      if (!q) return true;
      return (
        item.product_name.toLowerCase().includes(q) ||
        item.sku.toLowerCase().includes(q) ||
        (item.category_name && item.category_name.toLowerCase().includes(q))
      );
    });

    return [...filtered].sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (typeof aVal === "string") {
        return sortAsc
          ? (aVal as string).localeCompare(bVal as string)
          : (bVal as string).localeCompare(aVal as string);
      }

      aVal = Number(aVal) || 0;
      bVal = Number(bVal) || 0;
      return sortAsc ? aVal - bVal : bVal - aVal;
    });
  }, [data, bandFilter, searchQuery, sortField, sortAsc]);

  const handleSort = (field: keyof TurnoverItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === "turnover_ratio" || field === "days_of_stock");
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6 pb-12">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Activity className="w-5 h-5" />
              </div>
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-[var(--text)]">
                Inventory Turnover & Velocity
              </h1>
            </div>
            <p className="text-xs md:text-sm text-[var(--text-muted)] mt-1">
              Continuous stock velocity ratios and early-warning health banding before stock becomes
              dead.
            </p>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2 flex-wrap">
            <GlassButton
              variant="outline"
              size="sm"
              onClick={fetchData}
              disabled={loading}
              className="h-9 gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </GlassButton>
          </div>
        </div>

        {/* Filter Bar & Period Tabs */}
        <GlassCard className="p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Health Status Tabs */}
          <div className="flex items-center gap-1 bg-[var(--surface-overlay)] p-1 rounded-xl border border-[var(--glass-border)] flex-wrap">
            {(
              [
                { id: "all", label: "All Velocity", count: data?.summary?.total_products },
                { id: "healthy", label: "Healthy (Fast)", count: data?.summary?.healthy_count },
                { id: "slowing", label: "Slowing (Warning)", count: data?.summary?.slowing_count },
                { id: "at_risk", label: "At-Risk (Stagnant)", count: data?.summary?.at_risk_count },
              ] as { id: BandFilter; label: string; count?: number }[]
            ).map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setBandFilter(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                  bandFilter === tab.id
                    ? "bg-[var(--accent)] text-white shadow-[0_0_12px_var(--accent-glow)]"
                    : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]"
                }`}
              >
                <span>{tab.label}</span>
                {typeof tab.count === "number" && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-black/20 font-mono">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Period Selector Tabs */}
          <div className="flex items-center gap-1 bg-[var(--surface-overlay)] p-1 rounded-xl border border-[var(--glass-border)]">
            <Calendar className="w-3.5 h-3.5 text-[var(--text-muted)] ml-2 mr-1" />
            {(
              [
                { id: "7d", label: "7D" },
                { id: "30d", label: "30D" },
                { id: "90d", label: "90D" },
                { id: "12m", label: "1Y" },
                { id: "all", label: "All" },
              ] as { id: PeriodOption; label: string }[]
            ).map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setPeriod(p.id)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                  period === p.id
                    ? "bg-[var(--glass-bg-elevated)] text-[var(--text)] font-bold border border-[var(--glass-border)] shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text)]"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </GlassCard>

        {/* KPI Metrics Row */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
          {/* Mean Turnover Ratio */}
          <GlassCard className="p-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider font-mono">
                Avg Turnover
              </span>
              <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="text-xl md:text-2xl font-black text-[var(--text)] mt-2 font-mono">
              <AnimatedNumber value={data?.summary?.average_turnover_ratio || 0} />x
            </div>
            <div className="text-[11px] text-[var(--text-subtle)] mt-1">
              <span>Catalog velocity index</span>
            </div>
          </GlassCard>

          {/* Mean Days of Stock */}
          <GlassCard className="p-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider font-mono">
                Avg Days of Stock
              </span>
              <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <Calendar className="w-4 h-4" />
              </div>
            </div>
            <div className="text-xl md:text-2xl font-black text-[var(--text)] mt-2 font-mono">
              <AnimatedNumber value={data?.summary?.average_days_of_stock || 0} />d
            </div>
            <div className="text-[11px] text-[var(--text-subtle)] mt-1">
              <span>Avg coverage duration</span>
            </div>
          </GlassCard>

          {/* Healthy Count */}
          <GlassCard className="p-4 relative overflow-hidden border-emerald-500/20 bg-emerald-950/10">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider font-mono">
                Healthy Stock
              </span>
              <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-300">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="text-xl md:text-2xl font-black text-emerald-400 mt-2 font-mono">
              <AnimatedNumber value={data?.summary?.healthy_count || 0} />
            </div>
            <div className="text-[11px] text-emerald-500/80 mt-1">
              <span>Turnover ≥ 1.0x (≤ 30 days)</span>
            </div>
          </GlassCard>

          {/* Slowing Count */}
          <GlassCard className="p-4 relative overflow-hidden border-amber-500/20 bg-amber-950/10">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider font-mono">
                Slowing (Warning)
              </span>
              <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-300">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-xl md:text-2xl font-black text-amber-400 mt-2 font-mono">
              <AnimatedNumber value={data?.summary?.slowing_count || 0} />
            </div>
            <div className="text-[11px] text-amber-500/80 mt-1">
              <span>0.3x - 1.0x (30 - 90 days)</span>
            </div>
          </GlassCard>

          {/* At-Risk Count */}
          <GlassCard className="p-4 relative overflow-hidden border-rose-500/20 bg-rose-950/10 col-span-2 lg:col-span-1">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-rose-400 uppercase tracking-wider font-mono">
                At-Risk Stagnant
              </span>
              <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-300">
                <AlertCircle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-xl md:text-2xl font-black text-rose-400 mt-2 font-mono">
              <AnimatedNumber value={data?.summary?.at_risk_count || 0} />
            </div>
            <div className="text-[11px] text-rose-500/80 mt-1">
              <span>&lt; 0.3x or &gt; 90 days stock</span>
            </div>
          </GlassCard>
        </div>

        {/* Ranked Turnover Table */}
        <GlassCard className="p-0 overflow-hidden">
          {/* Table Header & Search */}
          <div className="p-4 border-b border-[var(--glass-border)] flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-[var(--surface-overlay)] text-[var(--text-muted)]">
                <Package className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-bold text-[var(--text)]">
                Product Inventory Turnover Ranking (Slowest First)
              </h2>
              <GlassBadge variant="neutral" className="text-[10px] font-mono">
                {filteredAndSortedItems.length} items
              </GlassBadge>
            </div>

            {/* Search Input */}
            <div className="relative max-w-xs w-full">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
              <input
                type="text"
                placeholder="Search SKU or product name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[var(--surface-overlay)] border border-[var(--glass-border)] text-xs text-[var(--text)] placeholder:text-[var(--text-subtle)] focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[var(--glass-border)] bg-[var(--surface-overlay)]/50 text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider font-mono">
                  <th
                    className="p-3.5 cursor-pointer hover:text-[var(--text)] select-none"
                    onClick={() => handleSort("product_name")}
                  >
                    <div className="flex items-center gap-1">
                      <span>PRODUCT / SKU</span>
                      <ArrowUpDown className="w-3 h-3 opacity-60" />
                    </div>
                  </th>
                  <th className="p-3.5">CATEGORY</th>
                  <th
                    className="p-3.5 cursor-pointer hover:text-[var(--text)] select-none"
                    onClick={() => handleSort("current_on_hand")}
                  >
                    <div className="flex items-center gap-1">
                      <span>ON-HAND</span>
                      <ArrowUpDown className="w-3 h-3 opacity-60" />
                    </div>
                  </th>
                  <th
                    className="p-3.5 cursor-pointer hover:text-[var(--text)] select-none"
                    onClick={() => handleSort("units_sold")}
                  >
                    <div className="flex items-center gap-1">
                      <span>UNITS SOLD</span>
                      <ArrowUpDown className="w-3 h-3 opacity-60" />
                    </div>
                  </th>
                  <th
                    className="p-3.5 cursor-pointer hover:text-[var(--text)] select-none"
                    onClick={() => handleSort("turnover_ratio")}
                  >
                    <div className="flex items-center gap-1">
                      <span>TURNOVER RATIO</span>
                      <ArrowUpDown className="w-3 h-3 opacity-60" />
                    </div>
                  </th>
                  <th
                    className="p-3.5 cursor-pointer hover:text-[var(--text)] select-none"
                    onClick={() => handleSort("days_of_stock")}
                  >
                    <div className="flex items-center gap-1">
                      <span>DAYS OF STOCK</span>
                      <ArrowUpDown className="w-3 h-3 opacity-60" />
                    </div>
                  </th>
                  <th className="p-3.5">HEALTH BAND</th>
                  <th
                    className="p-3.5 cursor-pointer hover:text-[var(--text)] select-none"
                    onClick={() => handleSort("tied_up_capital")}
                  >
                    <div className="flex items-center gap-1">
                      <span>TIED-UP CAPITAL</span>
                      <ArrowUpDown className="w-3 h-3 opacity-60" />
                    </div>
                  </th>
                  <th className="p-3.5 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--glass-border)]">
                {loading ? (
                  Array.from({ length: 5 }).map((_, idx) => (
                    <tr key={idx} className="animate-pulse">
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-40 mb-1" />
                        <div className="h-3 bg-[var(--surface-hover)] rounded w-20" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-24" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-16" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-16" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-16" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-16" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-5 bg-[var(--surface-hover)] rounded w-20" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-20" />
                      </td>
                      <td className="p-3.5 text-right">
                        <div className="h-7 bg-[var(--surface-hover)] rounded w-16 ml-auto" />
                      </td>
                    </tr>
                  ))
                ) : filteredAndSortedItems.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="p-8 text-center">
                      <EmptyState
                        title="No Products Match Filter"
                        description="No products match the selected velocity health band or search query."
                        icon={<Activity className="w-8 h-8 text-[var(--text-muted)]" />}
                      />
                    </td>
                  </tr>
                ) : (
                  filteredAndSortedItems.map((item) => {
                    const isHealthy = item.turnover_band === "healthy";
                    const isSlowing = item.turnover_band === "slowing";
                    const isAtRisk = item.turnover_band === "at_risk";

                    return (
                      <tr
                        key={item.product_id}
                        className="hover:bg-[var(--surface-hover)]/40 transition-colors"
                      >
                        {/* Name & SKU */}
                        <td className="p-3.5">
                          <div className="font-semibold text-[var(--text)]">
                            {item.product_name}
                          </div>
                          <div className="text-[11px] text-[var(--text-muted)] font-mono mt-0.5">
                            {item.sku}
                          </div>
                        </td>

                        {/* Category */}
                        <td className="p-3.5 text-[var(--text-muted)]">
                          {item.category_name || "Uncategorized"}
                        </td>

                        {/* On Hand */}
                        <td className="p-3.5 font-mono font-bold text-[var(--text)]">
                          {item.current_on_hand.toLocaleString()} {item.unit}
                        </td>

                        {/* Units Sold */}
                        <td className="p-3.5 font-mono text-[var(--text)]">
                          {item.units_sold.toLocaleString()} {item.unit}
                        </td>

                        {/* Turnover Ratio */}
                        <td className="p-3.5 font-mono font-bold">
                          <span
                            className={
                              isHealthy
                                ? "text-emerald-400"
                                : isSlowing
                                  ? "text-amber-400"
                                  : "text-rose-400"
                            }
                          >
                            {item.turnover_ratio}x
                          </span>
                        </td>

                        {/* Days of Stock */}
                        <td className="p-3.5 font-mono font-medium">
                          {item.days_of_stock >= 999 ? (
                            <span className="text-rose-400 font-bold">∞ (Stagnant)</span>
                          ) : (
                            <span
                              className={
                                item.days_of_stock <= 30
                                  ? "text-emerald-400"
                                  : item.days_of_stock <= 90
                                    ? "text-amber-400"
                                    : "text-rose-400"
                              }
                            >
                              {item.days_of_stock} days
                            </span>
                          )}
                        </td>

                        {/* Health Band Badge */}
                        <td className="p-3.5">
                          {isHealthy && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                              <CheckCircle2 className="w-3 h-3" />
                              Healthy
                            </span>
                          )}
                          {isSlowing && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                              <AlertTriangle className="w-3 h-3" />
                              Slowing
                            </span>
                          )}
                          {isAtRisk && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                              <AlertCircle className="w-3 h-3" />
                              At-Risk
                            </span>
                          )}
                        </td>

                        {/* Tied-Up Capital */}
                        <td className="p-3.5 font-mono font-semibold text-[var(--text)]">
                          ₹
                          {item.tied_up_capital.toLocaleString("en-IN", {
                            minimumFractionDigits: 2,
                          })}
                        </td>

                        {/* Action Link */}
                        <td className="p-3.5 text-right">
                          <Link
                            href="/admin/products"
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-[var(--accent)] hover:underline"
                          >
                            <span>Manage</span>
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </GlassCard>
      </div>
    </AppLayout>
  );
}
