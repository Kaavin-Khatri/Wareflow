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
  Truck,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Search,
  ArrowUpDown,
  RefreshCw,
  IndianRupee,
  Percent,
  Building2,
  ExternalLink,
  Phone,
  RotateCcw,
} from "lucide-react";

export interface SupplierPerformanceItem {
  supplier_id: string;
  supplier_name: string;
  contact_person: string | null;
  phone: string | null;
  total_pos: number;
  completed_pos: number;
  on_time_delivery_pct: number;
  fulfillment_accuracy_pct: number;
  return_rate_pct: number;
  total_spend_inr: number;
  rating_band: string; // 'excellent' | 'good' | 'needs_improvement'
}

export interface SupplierPerformanceSummary {
  average_on_time_pct: number;
  average_accuracy_pct: number;
  average_return_rate_pct: number;
  total_spend_inr: number;
  total_suppliers_analyzed: number;
  excellent_count: number;
  needs_improvement_count: number;
}

export interface SupplierPerformanceResponse {
  summary: SupplierPerformanceSummary;
  items: SupplierPerformanceItem[];
  generated_at: string;
}

type RatingFilter = "all" | "excellent" | "good" | "needs_improvement";

export default function SupplierPerformancePage() {
  const [data, setData] = useState<SupplierPerformanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [ratingFilter, setRatingFilter] = useState<RatingFilter>("all");
  const [sortField, setSortField] = useState<keyof SupplierPerformanceItem>("total_spend_inr");
  const [sortAsc, setSortAsc] = useState(false);

  const fetchPerformance = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get<SupplierPerformanceResponse>(
        "/analytics/supplier-performance"
      );
      setData(res);
    } catch (err: any) {
      console.error("Failed to fetch supplier performance", err);
      setError(err?.message || "Failed to load supplier performance analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformance();
  }, []);

  const handleSort = (field: keyof SupplierPerformanceItem) => {
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
      if (ratingFilter !== "all" && item.rating_band !== ratingFilter) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const nameMatch = item.supplier_name.toLowerCase().includes(q);
        const contactMatch = item.contact_person?.toLowerCase().includes(q) ?? false;
        if (!nameMatch && !contactMatch) return false;
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
      return sortAsc
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [data?.items, ratingFilter, searchQuery, sortField, sortAsc]);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  const getRatingBadge = (rating: string) => {
    switch (rating.toLowerCase()) {
      case "excellent":
        return <GlassBadge variant="success">★ Excellent</GlassBadge>;
      case "good":
        return <GlassBadge variant="accent">Good</GlassBadge>;
      case "needs_improvement":
        return <GlassBadge variant="error">Needs Review</GlassBadge>;
      default:
        return <GlassBadge variant="neutral">{rating}</GlassBadge>;
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6 pb-12">
        {/* Header Title & Controls */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/20 to-blue-600/20 text-indigo-400 ring-1 ring-white/10 shadow-inner">
                <Truck className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  Supplier Reliability & Performance
                </h1>
                <p className="text-xs text-white/50">
                  On-time delivery rates, fulfillment accuracy, vendor returns, and procurement spend
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
            <Link href="/admin/suppliers">
              <GlassButton variant="secondary" size="sm" className="gap-1.5">
                <Building2 className="h-4 w-4" />
                <span>Manage Suppliers</span>
              </GlassButton>
            </Link>
          </div>
        </div>

        {/* Top Summary KPI Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Avg On-Time Delivery
              </span>
              <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400">
                <Clock className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-white">
                <AnimatedNumber value={data?.summary?.average_on_time_pct ?? 0} decimals={1} />
                %
              </span>
            </div>
            <p className="mt-1 text-xs text-white/40">Expected vs actual receipt dates</p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Fulfillment Accuracy
              </span>
              <div className="rounded-lg bg-blue-500/10 p-2 text-blue-400">
                <CheckCircle2 className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-white">
                <AnimatedNumber value={data?.summary?.average_accuracy_pct ?? 0} decimals={1} />
                %
              </span>
            </div>
            <p className="mt-1 text-xs text-white/40">Total units received vs ordered</p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Total PO Spend
              </span>
              <div className="rounded-lg bg-indigo-500/10 p-2 text-indigo-400">
                <IndianRupee className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-white">
                {formatCurrency(data?.summary?.total_spend_inr ?? 0)}
              </span>
            </div>
            <p className="mt-1 text-xs text-white/40">
              Across {data?.summary?.total_suppliers_analyzed ?? 0} active vendors
            </p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Vendor Quality Rating
              </span>
              <div className="rounded-lg bg-amber-500/10 p-2 text-amber-400">
                <Percent className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-3">
              <span className="text-lg font-bold text-emerald-400">
                {data?.summary?.excellent_count ?? 0} Excellent
              </span>
              <span className="text-xs text-white/40">/</span>
              <span className="text-sm font-semibold text-rose-400">
                {data?.summary?.needs_improvement_count ?? 0} Needs Review
              </span>
            </div>
            <p className="mt-1 text-xs text-white/40">
              Avg return rate: {data?.summary?.average_return_rate_pct ?? 0}%
            </p>
          </GlassCard>
        </div>

        {/* Filter Pills & Search Bar */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-1.5 overflow-x-auto rounded-xl bg-white/[0.03] p-1 ring-1 ring-white/10">
            {(
              [
                { id: "all", label: "All Vendors" },
                { id: "excellent", label: "★ Excellent" },
                { id: "good", label: "Good" },
                { id: "needs_improvement", label: "Needs Review" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setRatingFilter(tab.id)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                  ratingFilter === tab.id
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
              placeholder="Search vendor or contact..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl bg-white/5 py-1.5 pl-9 pr-3 text-xs text-white placeholder-white/30 ring-1 ring-white/10 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
        </div>

        {/* Data Table */}
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
                icon={<Truck className="h-8 w-8 text-white/40" />}
                title="No supplier data found"
                description={
                  searchQuery
                    ? "No suppliers match your active search term."
                    : "No purchase orders or vendor delivery data recorded yet."
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
                      onClick={() => handleSort("supplier_name")}
                    >
                      <div className="flex items-center gap-1.5">
                        Supplier / Vendor
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium hover:text-white"
                      onClick={() => handleSort("on_time_delivery_pct")}
                    >
                      <div className="flex items-center gap-1.5">
                        On-Time Rate
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium hover:text-white"
                      onClick={() => handleSort("fulfillment_accuracy_pct")}
                    >
                      <div className="flex items-center gap-1.5">
                        Fulfillment Accuracy
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium hover:text-white"
                      onClick={() => handleSort("return_rate_pct")}
                    >
                      <div className="flex items-center gap-1.5">
                        Return Rate
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium hover:text-white"
                      onClick={() => handleSort("total_pos")}
                    >
                      <div className="flex items-center gap-1.5">
                        Orders (Total/Recv)
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="cursor-pointer px-4 py-3 font-medium text-right hover:text-white"
                      onClick={() => handleSort("total_spend_inr")}
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        Total Spend
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th className="px-4 py-3 font-medium text-center">Quality Rating</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredItems.map((item) => (
                    <tr
                      key={item.supplier_id}
                      className="transition-colors hover:bg-white/[0.02]"
                    >
                      <td className="px-4 py-3.5">
                        <div>
                          <div className="font-semibold text-white">{item.supplier_name}</div>
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

                      {/* On-Time Rate Bar */}
                      <td className="px-4 py-3.5">
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span
                              className={`font-semibold ${
                                item.on_time_delivery_pct >= 90
                                  ? "text-emerald-400"
                                  : item.on_time_delivery_pct >= 75
                                  ? "text-amber-400"
                                  : "text-rose-400"
                              }`}
                            >
                              {item.on_time_delivery_pct}%
                            </span>
                          </div>
                          <div className="h-1.5 w-28 overflow-hidden rounded-full bg-white/10">
                            <div
                              className={`h-full rounded-full ${
                                item.on_time_delivery_pct >= 90
                                  ? "bg-emerald-500"
                                  : item.on_time_delivery_pct >= 75
                                  ? "bg-amber-500"
                                  : "bg-rose-500"
                              }`}
                              style={{ width: `${Math.min(item.on_time_delivery_pct, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Fulfillment Accuracy */}
                      <td className="px-4 py-3.5">
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span
                              className={`font-semibold ${
                                item.fulfillment_accuracy_pct >= 95
                                  ? "text-blue-400"
                                  : item.fulfillment_accuracy_pct >= 85
                                  ? "text-amber-400"
                                  : "text-rose-400"
                              }`}
                            >
                              {item.fulfillment_accuracy_pct}%
                            </span>
                          </div>
                          <div className="h-1.5 w-28 overflow-hidden rounded-full bg-white/10">
                            <div
                              className="h-full rounded-full bg-blue-500"
                              style={{ width: `${Math.min(item.fulfillment_accuracy_pct, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Return Rate */}
                      <td className="px-4 py-3.5">
                        <span
                          className={`font-medium ${
                            item.return_rate_pct > 5
                              ? "text-rose-400"
                              : item.return_rate_pct > 0
                              ? "text-amber-400"
                              : "text-white/60"
                          }`}
                        >
                          {item.return_rate_pct}%
                        </span>
                      </td>

                      {/* Orders Count */}
                      <td className="px-4 py-3.5 text-white/70">
                        <span className="font-medium text-white">{item.completed_pos}</span>
                        <span className="text-white/40"> / {item.total_pos} POs</span>
                      </td>

                      {/* Total Spend */}
                      <td className="px-4 py-3.5 text-right font-medium text-white">
                        {formatCurrency(item.total_spend_inr)}
                      </td>

                      {/* Rating Badge */}
                      <td className="px-4 py-3.5 text-center">
                        {getRatingBadge(item.rating_band)}
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
