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
  Clock,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  Search,
  ArrowUpDown,
  FileSpreadsheet,
  ExternalLink,
  Store,
  Phone,
  RefreshCw,
  SlidersHorizontal,
  ChevronRight,
  TrendingDown,
  Building2,
  Calendar,
} from "lucide-react";

// --- Types ---
export interface ARAgingBucketItem {
  retailer_id: string;
  retailer_name: string;
  contact_person: string | null;
  phone: string | null;
  credit_limit: number;
  credit_balance: number;
  current: number;
  bucket_1_30: number;
  bucket_31_60: number;
  bucket_61_90: number;
  bucket_90_plus: number;
  total_overdue: number;
  total_outstanding: number;
  oldest_invoice_date: string | null;
  invoice_count: number;
}

export interface ARAgingSummary {
  total_current: number;
  total_bucket_1_30: number;
  total_bucket_31_60: number;
  total_bucket_61_90: number;
  total_bucket_90_plus: number;
  total_overdue: number;
  total_outstanding: number;
  total_retailers: number;
  overdue_retailers_count: number;
}

export interface ARAgingReportResponse {
  as_of_date: string;
  summary: ARAgingSummary;
  retailers: ARAgingBucketItem[];
  generated_at: string;
}

type BucketFilter = "all" | "overdue_only" | "critical_90" | "current_only" | "zero_balance";
type SortField = "total_overdue" | "total_outstanding" | "bucket_90_plus" | "retailer_name" | "current";

export default function ARAgingReportPage() {
  const [report, setReport] = useState<ARAgingReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [bucketFilter, setBucketFilter] = useState<BucketFilter>("all");
  const [hideZeroBalance, setHideZeroBalance] = useState(false);
  const [sortField, setSortField] = useState<SortField>("total_overdue");
  const [sortAsc, setSortAsc] = useState(false);

  const fetchReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.get<ARAgingReportResponse>("/analytics/ar-aging?include_zero_balance=true");
      setReport(data);
    } catch (err: any) {
      console.error("Failed to load AR aging report:", err);
      setError(err?.message || "Failed to load Accounts Receivable Aging Report.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  // Filtered & Sorted Retailers
  const filteredRetailers = useMemo(() => {
    if (!report?.retailers) return [];

    let list = [...report.retailers];

    // 1. Zero balance toggle
    if (hideZeroBalance) {
      list = list.filter((r) => r.total_outstanding > 0.001);
    }

    // 2. Search query filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(
        (r) =>
          r.retailer_name.toLowerCase().includes(q) ||
          (r.contact_person && r.contact_person.toLowerCase().includes(q)) ||
          (r.phone && r.phone.toLowerCase().includes(q))
      );
    }

    // 3. Bucket filter
    if (bucketFilter === "overdue_only") {
      list = list.filter((r) => r.total_overdue > 0.001);
    } else if (bucketFilter === "critical_90") {
      list = list.filter((r) => r.bucket_90_plus > 0.001);
    } else if (bucketFilter === "current_only") {
      list = list.filter((r) => r.current > 0.001 && r.total_overdue <= 0.001);
    } else if (bucketFilter === "zero_balance") {
      list = list.filter((r) => r.total_outstanding <= 0.001);
    }

    // 4. Sort
    list.sort((a, b) => {
      let valA: any = a[sortField];
      let valB: any = b[sortField];

      if (typeof valA === "string") {
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortAsc ? valA - valB : valB - valA;
    });

    return list;
  }, [report, searchQuery, bucketFilter, hideZeroBalance, sortField, sortAsc]);

  // Proportional percentages for the distribution bar
  const distributionPercentages = useMemo(() => {
    if (!report?.summary || report.summary.total_outstanding <= 0) {
      return { current: 100, b1_30: 0, b31_60: 0, b61_90: 0, b90_plus: 0 };
    }
    const tot = report.summary.total_outstanding;
    return {
      current: Math.round((report.summary.total_current / tot) * 100),
      b1_30: Math.round((report.summary.total_bucket_1_30 / tot) * 100),
      b31_60: Math.round((report.summary.total_bucket_31_60 / tot) * 100),
      b61_90: Math.round((report.summary.total_bucket_61_90 / tot) * 100),
      b90_plus: Math.round((report.summary.total_bucket_90_plus / tot) * 100),
    };
  }, [report]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const exportCSV = () => {
    if (!filteredRetailers.length) return;
    const headers = [
      "Retailer ID",
      "Retailer Name",
      "Contact Person",
      "Phone",
      "Credit Limit (INR)",
      "Current (INR)",
      "1-30 Days Overdue (INR)",
      "31-60 Days Overdue (INR)",
      "61-90 Days Overdue (INR)",
      "90+ Days Overdue (INR)",
      "Total Overdue (INR)",
      "Total Outstanding (INR)",
      "Oldest Invoice Date",
      "Open Invoices Count",
    ];

    const rows = filteredRetailers.map((r) => [
      `"${r.retailer_id}"`,
      `"${r.retailer_name.replace(/"/g, '""')}"`,
      `"${(r.contact_person || "").replace(/"/g, '""')}"`,
      `"${r.phone || ""}"`,
      r.credit_limit,
      r.current,
      r.bucket_1_30,
      r.bucket_31_60,
      r.bucket_61_90,
      r.bucket_90_plus,
      r.total_overdue,
      r.total_outstanding,
      `"${r.oldest_invoice_date || "N/A"}"`,
      r.invoice_count,
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Wareflow_AR_Aging_Report_${report?.as_of_date || "today"}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <AppLayout>
      <div className="w-full space-y-6 pb-16">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-[var(--border)]">
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[var(--text)]">
                Accounts-Receivable Aging Report
              </h1>
              <GlassBadge variant="neutral" className="text-xs">
                <Calendar className="w-3.5 h-3.5 mr-1" />
                As of: {report?.as_of_date || "Live"}
              </GlassBadge>
            </div>
            <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-1">
              Real-time portfolio debt aging across wholesale retailers grouped into 30, 60, and 90+ day risk cutoffs.
            </p>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            <GlassButton
              variant="outline"
              size="sm"
              onClick={exportCSV}
              disabled={loading || !filteredRetailers.length}
            >
              <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5" />
              <span>Export CSV</span>
            </GlassButton>
            <GlassButton
              variant="ghost"
              size="sm"
              onClick={fetchReport}
              disabled={loading}
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </GlassButton>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Top KPI Cards Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-3.5">
          {/* Card 1: Total Outstanding */}
          <GlassCard className="p-4 flex flex-col justify-between border-white/10 bg-white/[0.03]">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
              <span>Total Outstanding</span>
              <Building2 className="w-4 h-4 text-blue-400" />
            </div>
            <div className="mt-3">
              <div className="text-xl sm:text-2xl font-bold tracking-tight text-[var(--text)]">
                {loading ? "..." : <AnimatedNumber value={report?.summary?.total_outstanding || 0} prefix="₹" />}
              </div>
              <div className="text-[11px] text-[var(--text-muted)] mt-1">
                {report?.summary?.total_retailers || 0} Active Retailers
              </div>
            </div>
          </GlassCard>

          {/* Card 2: Current (0d) */}
          <GlassCard className="p-4 flex flex-col justify-between border-emerald-500/20 bg-emerald-500/[0.03]">
            <div className="flex items-center justify-between text-xs text-emerald-400">
              <span>Current (Within Terms)</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="mt-3">
              <div className="text-xl sm:text-2xl font-bold tracking-tight text-emerald-400">
                {loading ? "..." : <AnimatedNumber value={report?.summary?.total_current || 0} prefix="₹" />}
              </div>
              <div className="text-[11px] text-emerald-500/80 mt-1">
                {distributionPercentages.current}% of Receivables
              </div>
            </div>
          </GlassCard>

          {/* Card 3: 1-30 Days */}
          <GlassCard className="p-4 flex flex-col justify-between border-amber-500/20 bg-amber-500/[0.03]">
            <div className="flex items-center justify-between text-xs text-amber-400">
              <span>1–30 Days Overdue</span>
              <Clock className="w-4 h-4 text-amber-400" />
            </div>
            <div className="mt-3">
              <div className="text-xl sm:text-2xl font-bold tracking-tight text-amber-400">
                {loading ? "..." : <AnimatedNumber value={report?.summary?.total_bucket_1_30 || 0} prefix="₹" />}
              </div>
              <div className="text-[11px] text-amber-500/80 mt-1">
                {distributionPercentages.b1_30}% of Portfolio
              </div>
            </div>
          </GlassCard>

          {/* Card 4: 31-60 Days */}
          <GlassCard className="p-4 flex flex-col justify-between border-orange-500/20 bg-orange-500/[0.03]">
            <div className="flex items-center justify-between text-xs text-orange-400">
              <span>31–60 Days Overdue</span>
              <AlertTriangle className="w-4 h-4 text-orange-400" />
            </div>
            <div className="mt-3">
              <div className="text-xl sm:text-2xl font-bold tracking-tight text-orange-400">
                {loading ? "..." : <AnimatedNumber value={report?.summary?.total_bucket_31_60 || 0} prefix="₹" />}
              </div>
              <div className="text-[11px] text-orange-500/80 mt-1">
                {distributionPercentages.b31_60}% of Portfolio
              </div>
            </div>
          </GlassCard>

          {/* Card 5: 61-90 Days */}
          <GlassCard className="p-4 flex flex-col justify-between border-rose-500/20 bg-rose-500/[0.03]">
            <div className="flex items-center justify-between text-xs text-rose-400">
              <span>61–90 Days Overdue</span>
              <AlertCircle className="w-4 h-4 text-rose-400" />
            </div>
            <div className="mt-3">
              <div className="text-xl sm:text-2xl font-bold tracking-tight text-rose-400">
                {loading ? "..." : <AnimatedNumber value={report?.summary?.total_bucket_61_90 || 0} prefix="₹" />}
              </div>
              <div className="text-[11px] text-rose-500/80 mt-1">
                {distributionPercentages.b61_90}% of Portfolio
              </div>
            </div>
          </GlassCard>

          {/* Card 6: 90+ Days Critical */}
          <GlassCard className="p-4 flex flex-col justify-between border-red-600/30 bg-red-600/[0.05]">
            <div className="flex items-center justify-between text-xs text-red-400">
              <span>90+ Days (Critical)</span>
              <ShieldAlert className="w-4 h-4 text-red-500" />
            </div>
            <div className="mt-3">
              <div className="text-xl sm:text-2xl font-bold tracking-tight text-red-400">
                {loading ? "..." : <AnimatedNumber value={report?.summary?.total_bucket_90_plus || 0} prefix="₹" />}
              </div>
              <div className="text-[11px] text-red-500/80 mt-1">
                {report?.summary?.overdue_retailers_count || 0} Delinquent Accounts
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Visual Portfolio Aging Distribution Bar */}
        <GlassCard className="p-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
            <div>
              <h3 className="text-sm font-bold text-[var(--text)]">Portfolio Debt Aging Distribution</h3>
              <p className="text-xs text-[var(--text-muted)]">
                Proportional capital exposure across current and overdue aging horizons.
              </p>
            </div>
            <div className="text-xs font-mono text-[var(--text-muted)]">
              Total Overdue Risk:{" "}
              <span className="font-semibold text-rose-400">
                {formatCurrency(report?.summary?.total_overdue || 0)}
              </span>
            </div>
          </div>

          <div className="w-full h-4 rounded-full overflow-hidden flex bg-white/5 border border-white/10 p-0.5">
            <div
              style={{ width: `${distributionPercentages.current}%` }}
              className="h-full bg-emerald-500 rounded-l-full transition-all duration-500"
              title={`Current (Within Terms): ${distributionPercentages.current}% (${formatCurrency(report?.summary?.total_current || 0)})`}
            />
            <div
              style={{ width: `${distributionPercentages.b1_30}%` }}
              className="h-full bg-amber-500 transition-all duration-500"
              title={`1-30 Days Overdue: ${distributionPercentages.b1_30}% (${formatCurrency(report?.summary?.total_bucket_1_30 || 0)})`}
            />
            <div
              style={{ width: `${distributionPercentages.b31_60}%` }}
              className="h-full bg-orange-500 transition-all duration-500"
              title={`31-60 Days Overdue: ${distributionPercentages.b31_60}% (${formatCurrency(report?.summary?.total_bucket_31_60 || 0)})`}
            />
            <div
              style={{ width: `${distributionPercentages.b61_90}%` }}
              className="h-full bg-rose-500 transition-all duration-500"
              title={`61-90 Days Overdue: ${distributionPercentages.b61_90}% (${formatCurrency(report?.summary?.total_bucket_61_90 || 0)})`}
            />
            <div
              style={{ width: `${distributionPercentages.b90_plus}%` }}
              className="h-full bg-red-600 rounded-r-full transition-all duration-500"
              title={`90+ Days Critical: ${distributionPercentages.b90_plus}% (${formatCurrency(report?.summary?.total_bucket_90_plus || 0)})`}
            />
          </div>

          {/* Legend */}
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 mt-3 pt-2 border-t border-white/5 text-[11px] text-[var(--text-muted)]">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block" />
              <span>Current ({formatCurrency(report?.summary?.total_current || 0)})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-amber-500 inline-block" />
              <span>1–30d ({formatCurrency(report?.summary?.total_bucket_1_30 || 0)})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-orange-500 inline-block" />
              <span>31–60d ({formatCurrency(report?.summary?.total_bucket_31_60 || 0)})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-rose-500 inline-block" />
              <span>61–90d ({formatCurrency(report?.summary?.total_bucket_61_90 || 0)})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-red-600 inline-block" />
              <span>90+d Critical ({formatCurrency(report?.summary?.total_bucket_90_plus || 0)})</span>
            </div>
          </div>
        </GlassCard>

        {/* Filter & Search Toolbar */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search by retailer name, contact, phone..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs rounded-xl bg-white/[0.04] border border-[var(--border)] text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
            />
          </div>

          {/* Bucket Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            <button
              onClick={() => setBucketFilter("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                bucketFilter === "all"
                  ? "bg-[var(--accent)] text-white shadow-sm"
                  : "bg-white/[0.04] text-[var(--text-muted)] hover:bg-white/[0.08]"
              }`}
            >
              All ({report?.summary?.total_retailers || 0})
            </button>
            <button
              onClick={() => setBucketFilter("overdue_only")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                bucketFilter === "overdue_only"
                  ? "bg-rose-500 text-white shadow-sm"
                  : "bg-white/[0.04] text-[var(--text-muted)] hover:bg-white/[0.08]"
              }`}
            >
              Overdue Only ({report?.summary?.overdue_retailers_count || 0})
            </button>
            <button
              onClick={() => setBucketFilter("critical_90")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                bucketFilter === "critical_90"
                  ? "bg-red-600 text-white shadow-sm"
                  : "bg-white/[0.04] text-[var(--text-muted)] hover:bg-white/[0.08]"
              }`}
            >
              90+ Days
            </button>
            <button
              onClick={() => setBucketFilter("current_only")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                bucketFilter === "current_only"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "bg-white/[0.04] text-[var(--text-muted)] hover:bg-white/[0.08]"
              }`}
            >
              Within Terms
            </button>
          </div>

          {/* Zero balance toggle */}
          <label className="flex items-center gap-2 text-xs text-[var(--text-muted)] cursor-pointer select-none shrink-0">
            <input
              type="checkbox"
              checked={hideZeroBalance}
              onChange={(e) => setHideZeroBalance(e.target.checked)}
              className="rounded border-[var(--border)] text-[var(--accent)] focus:ring-0 bg-transparent"
            />
            <span>Hide Zero Balance</span>
          </label>
        </div>

        {/* Bucketed Accounts Receivable Aging Table */}
        <GlassCard className="overflow-hidden p-0 border-[var(--border)]">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[var(--border)] bg-white/[0.02] text-[var(--text-muted)] select-none">
                  <th
                    onClick={() => handleSort("retailer_name")}
                    className="p-3.5 font-semibold cursor-pointer hover:text-[var(--text)] transition-colors"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Retailer / Business</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="p-3.5 font-semibold text-right">Credit Line</th>
                  <th
                    onClick={() => handleSort("current")}
                    className="p-3.5 font-semibold text-right cursor-pointer hover:text-emerald-400 transition-colors text-emerald-400/90"
                  >
                    <div className="flex items-center justify-end gap-1.5">
                      <span>Current</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="p-3.5 font-semibold text-right text-amber-400/90">1–30 Days</th>
                  <th className="p-3.5 font-semibold text-right text-orange-400/90">31–60 Days</th>
                  <th className="p-3.5 font-semibold text-right text-rose-400/90">61–90 Days</th>
                  <th
                    onClick={() => handleSort("bucket_90_plus")}
                    className="p-3.5 font-semibold text-right cursor-pointer hover:text-red-400 transition-colors text-red-400/90"
                  >
                    <div className="flex items-center justify-end gap-1.5">
                      <span>90+ Days</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort("total_overdue")}
                    className="p-3.5 font-semibold text-right cursor-pointer hover:text-[var(--text)] transition-colors text-rose-300 font-bold"
                  >
                    <div className="flex items-center justify-end gap-1.5">
                      <span>Total Overdue</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort("total_outstanding")}
                    className="p-3.5 font-semibold text-right cursor-pointer hover:text-[var(--text)] transition-colors text-[var(--text)] font-bold"
                  >
                    <div className="flex items-center justify-end gap-1.5">
                      <span>Total Balance</span>
                      <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="p-3.5 font-semibold text-center">Ledger Action</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-white/[0.04]">
                {loading ? (
                  <tr>
                    <td colSpan={10} className="p-12 text-center text-xs text-[var(--text-muted)]">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-[var(--accent)]" />
                      Compiling live accounts receivable aging telemetry...
                    </td>
                  </tr>
                ) : filteredRetailers.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="p-8">
                      <EmptyState
                        title="No Matching Retailer Accounts"
                        description="No receivables match the active search or bucket filtering criteria."
                      />
                    </td>
                  </tr>
                ) : (
                  filteredRetailers.map((r) => {
                    const isOverdue = r.total_overdue > 0.001;
                    const isCritical = r.bucket_90_plus > 0.001;

                    return (
                      <tr
                        key={r.retailer_id}
                        className={`transition-colors hover:bg-white/[0.03] ${
                          isCritical ? "bg-red-500/[0.02]" : isOverdue ? "bg-amber-500/[0.01]" : ""
                        }`}
                      >
                        {/* Retailer Info & Ledger Link */}
                        <td className="p-3.5">
                          <div className="flex flex-col">
                            <Link
                              href={`/admin/retailers/${r.retailer_id}/ledger`}
                              className="font-semibold text-sm text-[var(--text)] hover:text-[var(--accent)] transition-colors flex items-center gap-1.5 group"
                            >
                              <span>{r.retailer_name}</span>
                              <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity text-[var(--accent)]" />
                            </Link>
                            <div className="flex items-center gap-2 mt-0.5 text-[11px] text-[var(--text-muted)]">
                              {r.contact_person && <span>{r.contact_person}</span>}
                              {r.contact_person && r.phone && <span>•</span>}
                              {r.phone && (
                                <span className="flex items-center gap-1">
                                  <Phone className="w-2.5 h-2.5" />
                                  {r.phone}
                                </span>
                              )}
                            </div>
                          </div>
                        </td>

                        {/* Credit Limit */}
                        <td className="p-3.5 text-right font-mono text-[var(--text-muted)]">
                          {formatCurrency(r.credit_limit)}
                        </td>

                        {/* Current (Within Terms) */}
                        <td className="p-3.5 text-right font-mono text-emerald-400">
                          {r.current > 0 ? formatCurrency(r.current) : "—"}
                        </td>

                        {/* 1-30 Days Overdue */}
                        <td className="p-3.5 text-right font-mono text-amber-400">
                          {r.bucket_1_30 > 0 ? formatCurrency(r.bucket_1_30) : "—"}
                        </td>

                        {/* 31-60 Days Overdue */}
                        <td className="p-3.5 text-right font-mono text-orange-400">
                          {r.bucket_31_60 > 0 ? formatCurrency(r.bucket_31_60) : "—"}
                        </td>

                        {/* 61-90 Days Overdue */}
                        <td className="p-3.5 text-right font-mono text-rose-400">
                          {r.bucket_61_90 > 0 ? formatCurrency(r.bucket_61_90) : "—"}
                        </td>

                        {/* 90+ Days Critical */}
                        <td className="p-3.5 text-right font-mono">
                          {r.bucket_90_plus > 0 ? (
                            <span className="px-2 py-0.5 rounded-md bg-red-500/10 text-red-400 border border-red-500/20 font-bold">
                              {formatCurrency(r.bucket_90_plus)}
                            </span>
                          ) : (
                            <span className="text-[var(--text-muted)]">—</span>
                          )}
                        </td>

                        {/* Total Overdue */}
                        <td className="p-3.5 text-right font-mono font-bold text-rose-300">
                          {r.total_overdue > 0 ? formatCurrency(r.total_overdue) : "₹0"}
                        </td>

                        {/* Total Outstanding */}
                        <td className="p-3.5 text-right font-mono font-bold text-[var(--text)]">
                          {formatCurrency(r.total_outstanding)}
                        </td>

                        {/* Ledger Actions */}
                        <td className="p-3.5 text-center">
                          <Link href={`/admin/retailers/${r.retailer_id}/ledger`}>
                            <GlassButton variant="outline" size="sm" className="text-[11px] h-7 px-2.5">
                              <span>Ledger</span>
                              <ChevronRight className="w-3 h-3 ml-1" />
                            </GlassButton>
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>

              {/* Table Footer with Summary Totals */}
              {!loading && filteredRetailers.length > 0 && (
                <tfoot>
                  <tr className="border-t-2 border-[var(--border)] bg-white/[0.04] font-bold text-xs">
                    <td className="p-3.5 text-[var(--text)]">
                      Total ({filteredRetailers.length} Retailers)
                    </td>
                    <td className="p-3.5 text-right font-mono text-[var(--text-muted)]">
                      {formatCurrency(
                        filteredRetailers.reduce((acc, curr) => acc + curr.credit_limit, 0)
                      )}
                    </td>
                    <td className="p-3.5 text-right font-mono text-emerald-400">
                      {formatCurrency(
                        filteredRetailers.reduce((acc, curr) => acc + curr.current, 0)
                      )}
                    </td>
                    <td className="p-3.5 text-right font-mono text-amber-400">
                      {formatCurrency(
                        filteredRetailers.reduce((acc, curr) => acc + curr.bucket_1_30, 0)
                      )}
                    </td>
                    <td className="p-3.5 text-right font-mono text-orange-400">
                      {formatCurrency(
                        filteredRetailers.reduce((acc, curr) => acc + curr.bucket_31_60, 0)
                      )}
                    </td>
                    <td className="p-3.5 text-right font-mono text-rose-400">
                      {formatCurrency(
                        filteredRetailers.reduce((acc, curr) => acc + curr.bucket_61_90, 0)
                      )}
                    </td>
                    <td className="p-3.5 text-right font-mono text-red-400">
                      {formatCurrency(
                        filteredRetailers.reduce((acc, curr) => acc + curr.bucket_90_plus, 0)
                      )}
                    </td>
                    <td className="p-3.5 text-right font-mono text-rose-300">
                      {formatCurrency(
                        filteredRetailers.reduce((acc, curr) => acc + curr.total_overdue, 0)
                      )}
                    </td>
                    <td className="p-3.5 text-right font-mono text-[var(--text)]">
                      {formatCurrency(
                        filteredRetailers.reduce((acc, curr) => acc + curr.total_outstanding, 0)
                      )}
                    </td>
                    <td className="p-3.5" />
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        </GlassCard>
      </div>
    </AppLayout>
  );
}
