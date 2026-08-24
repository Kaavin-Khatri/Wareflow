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
  Store,
  Users,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  Search,
  ArrowUpDown,
  RefreshCw,
  IndianRupee,
  Calendar,
  Phone,
  ArrowUpRight,
} from "lucide-react";

export interface RetailerPerformanceItem {
  retailer_id: string;
  retailer_name: string;
  contact_person: string | null;
  phone: string | null;
  pricing_tier: string;
  total_orders: number;
  total_revenue: number;
  avg_order_value: number;
  last_order_date: string | null;
  days_since_last_order: number;
  avg_order_gap_days: number;
  frequency_trend: string; // 'increasing' | 'steady' | 'decreasing'
  is_churn_risk: boolean;
  churn_risk_reason: string | null;
}

export interface RetailerPerformanceSummary {
  total_retailers: number;
  active_retailers_count: number;
  churn_risk_count: number;
  total_portfolio_revenue_inr: number;
  average_order_value_inr: number;
}

export interface RetailerPerformanceResponse {
  summary: RetailerPerformanceSummary;
  items: RetailerPerformanceItem[];
  generated_at: string;
}

type ChurnFilter = "all" | "churn_risk" | "active" | "increasing";

export default function RetailerPerformancePage() {
  const [data, setData] = useState<RetailerPerformanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState<ChurnFilter>("all");
  const [sortField, setSortField] = useState<keyof RetailerPerformanceItem>("total_revenue");
  const [sortAsc, setSortAsc] = useState(false);

  const fetchPerformance = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get<RetailerPerformanceResponse>(
        "/analytics/retailer-performance"
      );
      setData(res);
    } catch (err: any) {
      console.error("Failed to fetch retailer performance", err);
      setError(err?.message || "Failed to load retailer performance analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformance();
  }, []);

  const handleSort = (field: keyof RetailerPerformanceItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const filteredItems = useMemo(() => {
    if (!data?.items) return [];
    return data.items.filter((item) => {
      if (filter === "churn_risk" && !item.is_churn_risk) return false;
      if (filter === "active" && (item.is_churn_risk || item.total_orders === 0)) return false;
      if (filter === "increasing" && item.frequency_trend !== "increasing") return false;

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const nameMatch = item.retailer_name.toLowerCase().includes(q);
        const contactMatch = item.contact_person?.toLowerCase().includes(q) ?? false;
        const tierMatch = item.pricing_tier.toLowerCase().includes(q);
        if (!nameMatch && !contactMatch && !tierMatch) return false;
      }
      return true;
    }).sort((a, b) => {
      const valA = a[sortField];
      const valB = b[sortField];
      if (valA === null || valA === undefined) return sortAsc ? -1 : 1;
      if (valB === null || valB === undefined) return sortAsc ? 1 : -1;
      if (typeof valA === "number" && typeof valB === "number") {
        return sortAsc ? valA - valB : valB - valA;
      }
      if (typeof valA === "boolean" && typeof valB === "boolean") {
        return sortAsc ? (valA === valB ? 0 : valA ? 1 : -1) : valA === valB ? 0 : valA ? -1 : 1;
      }
      return sortAsc
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [data?.items, filter, searchQuery, sortField, sortAsc]);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  const getTierBadge = (tier: string) => {
    const t = tier.toLowerCase();
    if (t === "gold") return <GlassBadge variant="warning">Gold</GlassBadge>;
    if (t === "silver") return <GlassBadge variant="neutral">Silver</GlassBadge>;
    if (t === "bronze") return <GlassBadge variant="accent">Bronze</GlassBadge>;
    return <GlassBadge variant="neutral">{tier}</GlassBadge>;
  };

  const getTrendBadge = (trend: string) => {
    switch (trend.toLowerCase()) {
      case "increasing":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400">
            <TrendingUp className="h-3.5 w-3.5" /> Accelerating
          </span>
        );
      case "decreasing":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-rose-400">
            <TrendingDown className="h-3.5 w-3.5" /> Cooling Off
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-white/50">
            <Minus className="h-3.5 w-3.5" /> Steady
          </span>
        );
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6 pb-12">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-600/20 text-emerald-400 ring-1 ring-white/10 shadow-inner">
                <Store className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  Retailer Performance & Churn Risk
                </h1>
                <p className="text-xs text-white/50">
                  Revenue rankings, ordering velocity trends, and 2x historical gap churn alerts
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <GlassButton
              variant="outline"
              size="sm"
              onClick={fetchPerformance}
              disabled={loading}
              className="gap-1.5"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </GlassButton>
            <Link href="/admin/retailers">
              <GlassButton variant="secondary" size="sm" className="gap-1.5">
                <Users className="h-4 w-4" />
                <span>Manage Retailers</span>
              </GlassButton>
            </Link>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Portfolio Revenue
              </span>
              <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400">
                <IndianRupee className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-white">
                {formatCurrency(data?.summary?.total_portfolio_revenue_inr ?? 0)}
              </span>
            </div>
            <p className="mt-1 text-xs text-white/40">
              Across {data?.summary?.total_retailers ?? 0} registered accounts
            </p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Active Buyers (90d)
              </span>
              <div className="rounded-lg bg-blue-500/10 p-2 text-blue-400">
                <Store className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-white">
                <AnimatedNumber value={data?.summary?.active_retailers_count ?? 0} />
              </span>
              <span className="text-xs text-white/50">
                / {data?.summary?.total_retailers ?? 0}
              </span>
            </div>
            <p className="mt-1 text-xs text-white/40">Purchased within trailing 90 days</p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Churn Risk Alerts
              </span>
              <div className="rounded-lg bg-rose-500/10 p-2 text-rose-400">
                <AlertTriangle className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-rose-400">
                <AnimatedNumber value={data?.summary?.churn_risk_count ?? 0} />
              </span>
              <span className="text-xs text-rose-400/80">accounts</span>
            </div>
            <p className="mt-1 text-xs text-rose-300/60">Gap &gt; 2x historical average</p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Blended AOV
              </span>
              <div className="rounded-lg bg-indigo-500/10 p-2 text-indigo-400">
                <TrendingUp className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-white">
                {formatCurrency(data?.summary?.average_order_value_inr ?? 0)}
              </span>
            </div>
            <p className="mt-1 text-xs text-white/40">Average sales order basket size</p>
          </GlassCard>
        </div>

        {/* Filter Pills & Search */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-1.5 overflow-x-auto rounded-xl bg-white/[0.03] p-1 ring-1 ring-white/10">
            {(
              [
                { id: "all", label: "All Accounts" },
                { id: "churn_risk", label: "⚠️ Churn Risk" },
                { id: "active", label: "Active Buyers" },
                { id: "increasing", label: "📈 Accelerating" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setFilter(tab.id)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                  filter === tab.id
                    ? "bg-white/15 text-white shadow"
                    : "text-white/50 hover:bg-white/5 hover:text-white/80"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/40" />
            <input
              type="text"
              placeholder="Search store, contact, tier..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl bg-white/5 py-1.5 pl-9 pr-3 text-xs text-white placeholder-white/30 ring-1 ring-white/10 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
            />
          </div>
        </div>

        {/* Table Card */}
        <GlassCard className="overflow-hidden">
          {error ? (
            <div className="p-8 text-center text-rose-400 text-sm">{error}</div>
          ) : loading && !data ? (
            <div className="flex h-64 items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-white/40" />
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="p-12">
              <EmptyState
                icon={<Store className="h-8 w-8 text-white/40" />}
                title="No retailer data found"
                description={
                  searchQuery
                    ? "No retail accounts match your active search filter."
                    : "No retailer sales order records available."
                }
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/10 bg-white/[0.02] text-white/40">
                    <th
                      className="cursor-pointer px-4 py-3 font-medium hover:text-white"
                      onClick={() => handleSort("retailer_name")}
                    >
                      <div className="flex items-center gap-1.5">
                        Retail Store / Buyer
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th className="px-4 py-3 font-medium">Pricing Tier</th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium text-right hover:text-white"
                      onClick={() => handleSort("total_revenue")}
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        Cumulative Revenue
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium text-right hover:text-white"
                      onClick={() => handleSort("avg_order_value")}
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        Avg Order (AOV)
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium hover:text-white"
                      onClick={() => handleSort("days_since_last_order")}
                    >
                      <div className="flex items-center gap-1.5">
                        Order Recency & Interval
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th className="px-4 py-3 font-medium">Frequency Trend</th>
                    <th className="px-4 py-3 font-medium text-center">Status / Alert</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredItems.map((item) => (
                    <tr
                      key={item.retailer_id}
                      className={`transition-colors hover:bg-white/[0.02] ${
                        item.is_churn_risk ? "bg-rose-500/[0.03]" : ""
                      }`}
                    >
                      <td className="px-4 py-3.5">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-white">{item.retailer_name}</span>
                            <Link
                              href={`/admin/retailers/${item.retailer_id}/ledger`}
                              className="text-white/30 hover:text-white"
                            >
                              <ArrowUpRight className="h-3 w-3" />
                            </Link>
                          </div>
                          <div className="flex items-center gap-2 mt-0.5 text-white/40">
                            {item.contact_person && <span>{item.contact_person}</span>}
                            {item.phone && (
                              <span className="flex items-center gap-1">
                                <Phone className="h-2.5 w-2.5" />
                                {item.phone}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      <td className="px-4 py-3.5">{getTierBadge(item.pricing_tier)}</td>

                      <td className="px-4 py-3.5 text-right font-medium text-white">
                        <div>{formatCurrency(item.total_revenue)}</div>
                        <div className="text-[10px] text-white/40">{item.total_orders} orders</div>
                      </td>

                      <td className="px-4 py-3.5 text-right font-medium text-white/80">
                        {formatCurrency(item.avg_order_value)}
                      </td>

                      <td className="px-4 py-3.5">
                        <div>
                          {item.last_order_date ? (
                            <span className="font-medium text-white">
                              {item.days_since_last_order}d ago
                            </span>
                          ) : (
                            <span className="text-white/40">No orders yet</span>
                          )}
                          <div className="text-[10px] text-white/40">
                            Avg interval: {item.avg_order_gap_days}d
                          </div>
                        </div>
                      </td>

                      <td className="px-4 py-3.5">{getTrendBadge(item.frequency_trend)}</td>

                      <td className="px-4 py-3.5 text-center">
                        {item.is_churn_risk ? (
                          <div
                            className="inline-flex items-center gap-1 rounded-md bg-rose-500/10 px-2 py-0.5 text-[11px] font-medium text-rose-400 ring-1 ring-rose-500/20"
                            title={item.churn_risk_reason || "Churn risk flagged"}
                          >
                            <AlertTriangle className="h-3 w-3" />
                            Churn Risk
                          </div>
                        ) : item.total_orders > 0 ? (
                          <GlassBadge variant="success">Active</GlassBadge>
                        ) : (
                          <GlassBadge variant="neutral">New / Inactive</GlassBadge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>
      </div>
    </AppLayout>
  );
}
