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
  AlertOctagon,
  TrendingDown,
  Package,
  Layers,
  Search,
  ArrowUpDown,
  RefreshCw,
  IndianRupee,
  Percent,
  Calendar,
  SlidersHorizontal,
} from "lucide-react";

export interface ShrinkageItem {
  id: string;
  name: string;
  secondary_info: string | null;
  badge: string | null;
  units_lost: number;
  incidents_count: number;
  shrinkage_value_inr: number;
  pct_of_total_shrinkage: number;
}

export interface ShrinkageSummary {
  total_shrinkage_value_inr: number;
  total_units_lost: number;
  shrinkage_rate_pct: number;
  damage_incidents_count: number;
}

export interface ShrinkageResponse {
  period: string;
  group_by: string;
  summary: ShrinkageSummary;
  items: ShrinkageItem[];
  generated_at: string;
}

type GroupByOption = "product" | "category";
type PeriodOption = "7d" | "30d" | "90d" | "12m" | "all";

export default function ShrinkageAnalyticsPage() {
  const [groupBy, setGroupBy] = useState<GroupByOption>("product");
  const [period, setPeriod] = useState<PeriodOption>("30d");
  const [data, setData] = useState<ShrinkageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<keyof ShrinkageItem>("shrinkage_value_inr");
  const [sortAsc, setSortAsc] = useState(false);

  const fetchShrinkage = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get<ShrinkageResponse>(
        `/analytics/shrinkage?group_by=${groupBy}&period=${period}`,
      );
      setData(res);
    } catch (err: any) {
      console.error("Failed to fetch shrinkage analytics", err);
      setError(err?.message || "Failed to load shrinkage analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShrinkage();
  }, [groupBy, period]);

  const handleSort = (field: keyof ShrinkageItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const filteredItems = useMemo(() => {
    if (!data?.items) return [];
    return data.items
      .filter((item) => {
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const nameMatch = item.name.toLowerCase().includes(q);
          const secMatch = item.secondary_info?.toLowerCase().includes(q) ?? false;
          const badgeMatch = item.badge?.toLowerCase().includes(q) ?? false;
          if (!nameMatch && !secMatch && !badgeMatch) return false;
        }
        return true;
      })
      .sort((a, b) => {
        const valA = a[sortField];
        const valB = b[sortField];
        if (valA === null || valA === undefined) return sortAsc ? -1 : 1;
        if (valB === null || valB === undefined) return sortAsc ? 1 : -1;
        if (typeof valA === "number" && typeof valB === "number") {
          return sortAsc ? valA - valB : valB - valA;
        }
        return sortAsc
          ? String(valA).localeCompare(String(valB))
          : String(valB).localeCompare(String(valA));
      });
  }, [data, searchQuery, sortField, sortAsc]);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <AppLayout>
      <div className="space-y-6 pb-12">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-rose-500/20 to-amber-600/20 text-rose-400 ring-1 ring-white/10 shadow-inner">
                <AlertOctagon className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  Inventory Shrinkage & Loss Tracking
                </h1>
                <p className="text-xs text-white/50">
                  Damage write-offs, physical discrepancies, and spoilage values from ledger
                  adjustments
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <GlassButton
              variant="outline"
              size="sm"
              onClick={fetchShrinkage}
              disabled={loading}
              className="gap-1.5"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </GlassButton>
            <Link href="/admin/stock/adjust">
              <GlassButton variant="secondary" size="sm" className="gap-1.5">
                <SlidersHorizontal className="h-4 w-4" />
                <span>Record Adjustment</span>
              </GlassButton>
            </Link>
          </div>
        </div>

        {/* Top KPI Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Total Shrinkage Value
              </span>
              <div className="rounded-lg bg-rose-500/10 p-2 text-rose-400">
                <IndianRupee className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-rose-400">
                {formatCurrency(data?.summary?.total_shrinkage_value_inr ?? 0)}
              </span>
            </div>
            <p className="mt-1 text-xs text-white/40">Monetary write-off value (cost price)</p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Physical Units Lost
              </span>
              <div className="rounded-lg bg-amber-500/10 p-2 text-amber-400">
                <Package className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-white">
                <AnimatedNumber value={data?.summary?.total_units_lost ?? 0} />
              </span>
              <span className="text-xs text-white/50">units</span>
            </div>
            <p className="mt-1 text-xs text-white/40">
              Across {data?.summary?.damage_incidents_count ?? 0} incidents
            </p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Shrinkage Loss Rate
              </span>
              <div className="rounded-lg bg-rose-500/10 p-2 text-rose-400">
                <Percent className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-white">
                <AnimatedNumber value={data?.summary?.shrinkage_rate_pct ?? 0} decimals={2} />%
              </span>
            </div>
            <p className="mt-1 text-xs text-white/40">Of total inventory valuation</p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Damage Incidents
              </span>
              <div className="rounded-lg bg-indigo-500/10 p-2 text-indigo-400">
                <TrendingDown className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-white">
                <AnimatedNumber value={data?.summary?.damage_incidents_count ?? 0} />
              </span>
              <span className="text-xs text-white/50">events</span>
            </div>
            <p className="mt-1 text-xs text-white/40">Negative adjustment entries</p>
          </GlassCard>
        </div>

        {/* Group By Toggle & Period Tabs */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            {/* Group By Dimension */}
            <div className="flex items-center gap-1.5 rounded-xl bg-white/[0.03] p-1 ring-1 ring-white/10">
              <button
                onClick={() => setGroupBy("product")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                  groupBy === "product"
                    ? "bg-white/15 text-white shadow"
                    : "text-white/50 hover:bg-white/5 hover:text-white/80"
                }`}
              >
                <Package className="h-3.5 w-3.5" />
                Product Breakdown
              </button>
              <button
                onClick={() => setGroupBy("category")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                  groupBy === "category"
                    ? "bg-white/15 text-white shadow"
                    : "text-white/50 hover:bg-white/5 hover:text-white/80"
                }`}
              >
                <Layers className="h-3.5 w-3.5" />
                Category Breakdown
              </button>
            </div>

            {/* Time Window Tabs */}
            <div className="flex items-center gap-1 overflow-x-auto rounded-xl bg-white/[0.03] p-1 ring-1 ring-white/10">
              {(
                [
                  { id: "7d", label: "7 Days" },
                  { id: "30d", label: "30 Days" },
                  { id: "90d", label: "90 Days" },
                  { id: "12m", label: "1 Year" },
                  { id: "all", label: "All Time" },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setPeriod(tab.id)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                    period === tab.id
                      ? "bg-rose-500/20 text-rose-300 ring-1 ring-rose-500/30"
                      : "text-white/40 hover:text-white/80"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/40" />
            <input
              type="text"
              placeholder={`Search ${groupBy}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl bg-white/5 py-1.5 pl-9 pr-3 text-xs text-white placeholder-white/30 ring-1 ring-white/10 focus:outline-none focus:ring-2 focus:ring-rose-500/50"
            />
          </div>
        </div>

        {/* Data Table Card */}
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
                icon={<AlertOctagon className="h-8 w-8 text-white/40" />}
                title="Zero shrinkage recorded"
                description={
                  searchQuery
                    ? "No items match your active search filter."
                    : `No negative inventory adjustments or damage write-offs recorded in the selected ${period} window.`
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
                      onClick={() => handleSort("name")}
                    >
                      <div className="flex items-center gap-1.5">
                        {groupBy === "product" ? "Product SKU" : "Category"}
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium hover:text-white"
                      onClick={() => handleSort("units_lost")}
                    >
                      <div className="flex items-center gap-1.5">
                        Units Lost / Damaged
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium hover:text-white"
                      onClick={() => handleSort("incidents_count")}
                    >
                      <div className="flex items-center gap-1.5">
                        Incidents
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium text-right hover:text-white"
                      onClick={() => handleSort("shrinkage_value_inr")}
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        Monetary Loss (₹)
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium text-right hover:text-white"
                      onClick={() => handleSort("pct_of_total_shrinkage")}
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        Share of Total Loss
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredItems.map((item) => (
                    <tr key={item.id} className="transition-colors hover:bg-white/[0.02]">
                      <td className="px-4 py-3.5">
                        <div>
                          <div className="font-semibold text-white">{item.name}</div>
                          <div className="flex items-center gap-2 mt-0.5 text-white/40">
                            {item.secondary_info && <span>{item.secondary_info}</span>}
                            {item.badge && <GlassBadge variant="neutral">{item.badge}</GlassBadge>}
                          </div>
                        </div>
                      </td>

                      <td className="px-4 py-3.5 font-medium text-rose-300">
                        -{item.units_lost} units
                      </td>

                      <td className="px-4 py-3.5 text-white/70">
                        {item.incidents_count} event{item.incidents_count !== 1 ? "s" : ""}
                      </td>

                      <td className="px-4 py-3.5 text-right font-bold text-rose-400">
                        {formatCurrency(item.shrinkage_value_inr)}
                      </td>

                      <td className="px-4 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <span className="font-medium text-white/80">
                            {item.pct_of_total_shrinkage}%
                          </span>
                          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/10">
                            <div
                              className="h-full rounded-full bg-rose-500"
                              style={{ width: `${Math.min(item.pct_of_total_shrinkage, 100)}%` }}
                            />
                          </div>
                        </div>
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
