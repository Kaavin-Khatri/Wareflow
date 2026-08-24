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
  TrendingUp,
  Package,
  Store,
  Tags,
  Search,
  ArrowUpDown,
  RefreshCw,
  IndianRupee,
  Percent,
  Calendar,
  Layers,
  ArrowUpRight,
} from "lucide-react";

// --- Types ---
export interface ProfitabilityItem {
  id: string;
  name: string;
  secondary_info: string | null;
  badge: string | null;
  units_sold: number;
  orders_count: number;
  total_revenue: number;
  total_cost: number;
  gross_margin_inr: number;
  gross_margin_pct: number;
}

export interface ProfitabilitySummary {
  total_revenue: number;
  total_cost: number;
  total_gross_margin_inr: number;
  overall_margin_pct: number;
  total_units_sold: number;
  total_orders: number;
}

export interface ProfitabilityResponse {
  group_by: string;
  period: string;
  summary: ProfitabilitySummary;
  items: ProfitabilityItem[];
  generated_at: string;
}

type GroupByOption = "product" | "category" | "retailer";
type PeriodOption = "7d" | "30d" | "90d" | "12m" | "all";

export default function ProfitabilityAnalyticsPage() {
  const [groupBy, setGroupBy] = useState<GroupByOption>("product");
  const [period, setPeriod] = useState<PeriodOption>("30d");
  const [data, setData] = useState<ProfitabilityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<keyof ProfitabilityItem>("gross_margin_inr");
  const [sortAsc, setSortAsc] = useState(false);

  // Fetch profitability data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<ProfitabilityResponse>(
        `/analytics/profitability?group_by=${groupBy}&period=${period}`
      );
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to load profitability metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [groupBy, period]);

  // Filter & sort rows
  const filteredAndSortedItems = useMemo(() => {
    if (!data?.items) return [];

    let filtered = data.items.filter((item) => {
      const q = searchQuery.toLowerCase().trim();
      if (!q) return true;
      return (
        item.name.toLowerCase().includes(q) ||
        (item.secondary_info && item.secondary_info.toLowerCase().includes(q)) ||
        (item.badge && item.badge.toLowerCase().includes(q))
      );
    });

    return filtered.sort((a, b) => {
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
  }, [data?.items, searchQuery, sortField, sortAsc]);

  const handleSort = (field: keyof ProfitabilityItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const getDimensionIcon = () => {
    switch (groupBy) {
      case "category":
        return <Tags className="w-4 h-4" />;
      case "retailer":
        return <Store className="w-4 h-4" />;
      default:
        return <Package className="w-4 h-4" />;
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6 pb-12">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <TrendingUp className="w-5 h-5" />
              </div>
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-[var(--text)]">
                Profitability & Margin Analytics
              </h1>
            </div>
            <p className="text-xs md:text-sm text-[var(--text-muted)] mt-1">
              Gross margins weighted by actual units sold and tier-adjusted wholesale pricing.
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

        {/* Group By & Period Controls Bar */}
        <GlassCard className="p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Dimension Toggle Pills */}
          <div className="flex items-center gap-1.5 bg-[var(--surface-overlay)] p-1 rounded-xl border border-[var(--glass-border)]">
            <span className="text-[11px] font-semibold text-[var(--text-subtle)] px-2 uppercase font-mono">
              Group By:
            </span>
            {(["product", "category", "retailer"] as GroupByOption[]).map((opt) => (
              <button
                key={opt}
                type="button"
                onClick={() => setGroupBy(opt)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all flex items-center gap-1.5 ${
                  groupBy === opt
                    ? "bg-[var(--accent)] text-white shadow-[0_0_12px_var(--accent-glow)]"
                    : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]"
                }`}
              >
                {opt === "product" && <Package className="w-3.5 h-3.5" />}
                {opt === "category" && <Tags className="w-3.5 h-3.5" />}
                {opt === "retailer" && <Store className="w-3.5 h-3.5" />}
                <span>{opt}</span>
              </button>
            ))}
          </div>

          {/* Period Selector Tabs */}
          <div className="flex items-center gap-1 bg-[var(--surface-overlay)] p-1 rounded-xl border border-[var(--glass-border)]">
            <Calendar className="w-3.5 h-3.5 text-[var(--text-muted)] ml-2 mr-1" />
            {(
              [
                { id: "7d", label: "7 Days" },
                { id: "30d", label: "30 Days" },
                { id: "90d", label: "90 Days" },
                { id: "12m", label: "1 Year" },
                { id: "all", label: "All Time" },
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

        {/* Top KPI Metrics Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
          {/* Total Revenue */}
          <GlassCard className="p-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider font-mono">
                Total Revenue
              </span>
              <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <IndianRupee className="w-4 h-4" />
              </div>
            </div>
            <div className="text-xl md:text-2xl font-black text-[var(--text)] mt-2 font-mono">
              ₹
              <AnimatedNumber value={data?.summary?.total_revenue || 0} />
            </div>
            <div className="text-[11px] text-[var(--text-subtle)] mt-1 flex items-center gap-1">
              <span>{data?.summary?.total_units_sold || 0} total units sold</span>
            </div>
          </GlassCard>

          {/* Total Procurement Cost */}
          <GlassCard className="p-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider font-mono">
                Total Cost (COGS)
              </span>
              <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Package className="w-4 h-4" />
              </div>
            </div>
            <div className="text-xl md:text-2xl font-black text-[var(--text)] mt-2 font-mono">
              ₹
              <AnimatedNumber value={data?.summary?.total_cost || 0} />
            </div>
            <div className="text-[11px] text-[var(--text-subtle)] mt-1">
              <span>Weighted supplier acquisition cost</span>
            </div>
          </GlassCard>

          {/* Total Gross Profit INR */}
          <GlassCard className="p-4 relative overflow-hidden border-emerald-500/30 bg-emerald-950/10">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider font-mono">
                Gross Profit (₹)
              </span>
              <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>
            <div className="text-xl md:text-2xl font-black text-emerald-400 mt-2 font-mono">
              ₹
              <AnimatedNumber value={data?.summary?.total_gross_margin_inr || 0} />
            </div>
            <div className="text-[11px] text-emerald-500/80 mt-1">
              <span>Revenue minus Cost of Goods</span>
            </div>
          </GlassCard>

          {/* Overall Margin % */}
          <GlassCard className="p-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider font-mono">
                Blended Margin %
              </span>
              <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Percent className="w-4 h-4" />
              </div>
            </div>
            <div className="text-xl md:text-2xl font-black text-[var(--text)] mt-2 font-mono">
              <AnimatedNumber value={data?.summary?.overall_margin_pct || 0} />%
            </div>
            <div className="text-[11px] text-[var(--text-subtle)] mt-1">
              <span>Gross profit / total revenue</span>
            </div>
          </GlassCard>
        </div>

        {/* Data Table Section */}
        <GlassCard className="p-0 overflow-hidden">
          {/* Table Header & Search Filter */}
          <div className="p-4 border-b border-[var(--glass-border)] flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-[var(--surface-overlay)] text-[var(--text-muted)]">
                {getDimensionIcon()}
              </div>
              <h2 className="text-sm font-bold text-[var(--text)] capitalize">
                Profitability Breakdown by {groupBy}
              </h2>
              <GlassBadge variant="neutral" className="text-[10px] font-mono">
                {filteredAndSortedItems.length} records
              </GlassBadge>
            </div>

            {/* Search Input */}
            <div className="relative max-w-xs w-full">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
              <input
                type="text"
                placeholder={`Search ${groupBy} name or details...`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[var(--surface-overlay)] border border-[var(--glass-border)] text-xs text-[var(--text)] placeholder:text-[var(--text-subtle)] focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
          </div>

          {/* Table Container */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[var(--glass-border)] bg-[var(--surface-overlay)]/50 text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider font-mono">
                  <th
                    className="p-3.5 cursor-pointer hover:text-[var(--text)] select-none"
                    onClick={() => handleSort("name")}
                  >
                    <div className="flex items-center gap-1">
                      <span>{groupBy.toUpperCase()}</span>
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
                    onClick={() => handleSort("total_revenue")}
                  >
                    <div className="flex items-center gap-1">
                      <span>REVENUE (₹)</span>
                      <ArrowUpDown className="w-3 h-3 opacity-60" />
                    </div>
                  </th>
                  <th
                    className="p-3.5 cursor-pointer hover:text-[var(--text)] select-none"
                    onClick={() => handleSort("total_cost")}
                  >
                    <div className="flex items-center gap-1">
                      <span>COST (₹)</span>
                      <ArrowUpDown className="w-3 h-3 opacity-60" />
                    </div>
                  </th>
                  <th
                    className="p-3.5 cursor-pointer hover:text-[var(--text)] select-none"
                    onClick={() => handleSort("gross_margin_inr")}
                  >
                    <div className="flex items-center gap-1">
                      <span>GROSS PROFIT (₹)</span>
                      <ArrowUpDown className="w-3 h-3 opacity-60" />
                    </div>
                  </th>
                  <th
                    className="p-3.5 cursor-pointer hover:text-[var(--text)] select-none"
                    onClick={() => handleSort("gross_margin_pct")}
                  >
                    <div className="flex items-center gap-1">
                      <span>MARGIN %</span>
                      <ArrowUpDown className="w-3 h-3 opacity-60" />
                    </div>
                  </th>
                  <th className="p-3.5 text-right">MARGIN VISUAL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--glass-border)]">
                {loading ? (
                  Array.from({ length: 5 }).map((_, idx) => (
                    <tr key={idx} className="animate-pulse">
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-40 mb-1" />
                        <div className="h-3 bg-[var(--surface-hover)] rounded w-24" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-16" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-20" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-20" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-20" />
                      </td>
                      <td className="p-3.5">
                        <div className="h-4 bg-[var(--surface-hover)] rounded w-12" />
                      </td>
                      <td className="p-3.5 text-right">
                        <div className="h-2 bg-[var(--surface-hover)] rounded w-24 ml-auto" />
                      </td>
                    </tr>
                  ))
                ) : filteredAndSortedItems.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center">
                      <EmptyState
                        title="No Sales or Profitability Data"
                        description="No orders have been recorded in the selected period. Adjust your date filter or create sales orders."
                        icon={<TrendingUp className="w-8 h-8 text-[var(--text-muted)]" />}
                      />
                    </td>
                  </tr>
                ) : (
                  filteredAndSortedItems.map((item) => {
                    const isPositive = item.gross_margin_inr >= 0;
                    return (
                      <tr
                        key={item.id}
                        className="hover:bg-[var(--surface-hover)]/40 transition-colors"
                      >
                        {/* Name & Details */}
                        <td className="p-3.5">
                          <div className="font-semibold text-[var(--text)] flex items-center gap-2">
                            <span>{item.name}</span>
                            {item.badge && (
                              <GlassBadge
                                variant={
                                  item.badge.toLowerCase().includes("gold")
                                    ? "warning"
                                    : item.badge.toLowerCase().includes("category")
                                      ? "accent"
                                      : "neutral"
                                }
                                className="text-[9px] px-1.5 py-0 uppercase"
                              >
                                {item.badge}
                              </GlassBadge>
                            )}
                          </div>
                          {item.secondary_info && (
                            <div className="text-[11px] text-[var(--text-muted)] font-mono mt-0.5">
                              {item.secondary_info}
                            </div>
                          )}
                        </td>

                        {/* Units Sold & Orders */}
                        <td className="p-3.5 font-mono">
                          <div className="font-bold text-[var(--text)]">
                            {item.units_sold.toLocaleString()}
                          </div>
                          <div className="text-[10px] text-[var(--text-subtle)]">
                            {item.orders_count} orders
                          </div>
                        </td>

                        {/* Revenue */}
                        <td className="p-3.5 font-mono font-semibold text-[var(--text)]">
                          ₹{item.total_revenue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </td>

                        {/* Cost */}
                        <td className="p-3.5 font-mono text-[var(--text-muted)]">
                          ₹{item.total_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </td>

                        {/* Gross Profit INR */}
                        <td className="p-3.5 font-mono font-bold">
                          <span className={isPositive ? "text-emerald-400" : "text-rose-400"}>
                            ₹{item.gross_margin_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                          </span>
                        </td>

                        {/* Margin % */}
                        <td className="p-3.5 font-mono font-bold">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] ${
                              item.gross_margin_pct >= 20
                                ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/20"
                                : item.gross_margin_pct >= 10
                                  ? "bg-blue-500/15 text-blue-300 border border-blue-500/20"
                                  : item.gross_margin_pct > 0
                                    ? "bg-amber-500/15 text-amber-300 border border-amber-500/20"
                                    : "bg-rose-500/15 text-rose-300 border border-rose-500/20"
                            }`}
                          >
                            {item.gross_margin_pct}%
                          </span>
                        </td>

                        {/* Visual Progress Bar */}
                        <td className="p-3.5 text-right">
                          <div className="w-24 ml-auto bg-[var(--surface-overlay)] h-2 rounded-full overflow-hidden border border-[var(--glass-border)]">
                            <div
                              className={`h-full rounded-full ${
                                item.gross_margin_pct >= 20
                                  ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                                  : item.gross_margin_pct >= 10
                                    ? "bg-gradient-to-r from-blue-500 to-cyan-400"
                                    : item.gross_margin_pct > 0
                                      ? "bg-gradient-to-r from-amber-500 to-yellow-400"
                                      : "bg-rose-500"
                              }`}
                              style={{
                                width: `${Math.min(Math.max(item.gross_margin_pct, 0), 100)}%`,
                              }}
                            />
                          </div>
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
