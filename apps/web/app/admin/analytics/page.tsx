"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassTiltCard } from "@/components/glass/GlassTiltCard";
import { AnimatedNumber } from "@/components/motion/AnimatedNumber";
import { ComparisonBadge } from "@/components/analytics/ComparisonBadge";
import { apiClient } from "@/lib/api-client";
import {
  Boxes,
  TrendingUp,
  Activity,
  CreditCard,
  Truck,
  Users,
  Warehouse,
  ShieldAlert,
  Download,
  Send,
  Calendar,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ArrowUpRight,
  RefreshCw,
  FileText,
  Clock,
  Layers,
} from "lucide-react";

interface PeriodMetric {
  metric_key: string;
  metric_label: string;
  current_value: number;
  prior_value: number | null;
  delta_value: number;
  delta_pct: number;
  trend: "up" | "down" | "flat";
  is_positive: boolean;
  higher_is_better: boolean;
  period_label: string;
  formatted_current: string;
  formatted_prior: string;
}

interface PeriodComparisonsResponse {
  period: string;
  as_of: string;
  metrics: Record<string, PeriodMetric>;
}

interface WeeklyHighlight {
  title: string;
  description: string;
  category: string;
  metric_value: string;
  badge_variant: "success" | "warning" | "error" | "neutral";
}

interface FastMover {
  product_id: string;
  name: string;
  sku: string;
  revenue: number;
  units: number;
}

interface SlowMover {
  product_id: string;
  name: string;
  sku: string;
  on_hand: number;
  tied_up_capital: number;
}

interface WeeklyReportData {
  report_id: string;
  start_date: string;
  end_date: string;
  period_label: string;
  generated_at: string;
  revenue_inr: number;
  revenue_delta_pct: number;
  gross_margin_pct: number;
  gross_margin_delta_pct: number;
  total_stock_valuation_inr: number;
  turnover_ratio_30d: number;
  low_stock_count: number;
  overdue_invoices_count: number;
  overdue_amount_inr: number;
  shrinkage_inr: number;
  top_fast_movers: FastMover[];
  top_slow_movers: SlowMover[];
  highlights: WeeklyHighlight[];
  narrative_summary: string;
}

const ANALYTICS_HUBS = [
  {
    title: "Stock Valuation & Inventory Health",
    description: "Real-time SKU valuation, safety stock alerts, and 3D warehouse topology mapping.",
    href: "/admin/analytics/stock",
    icon: Boxes,
    badge: "Inventory Core",
    gradient: "from-blue-500/20 via-cyan-500/10 to-transparent",
    iconColor: "text-blue-500",
  },
  {
    title: "Profitability & Product Margins",
    description: "Gross margin matrix, SKU-level contribution analysis, and category revenue ranking.",
    href: "/admin/analytics/profitability",
    icon: TrendingUp,
    badge: "Margin Matrix",
    gradient: "from-emerald-500/20 via-teal-500/10 to-transparent",
    iconColor: "text-emerald-500",
  },
  {
    title: "Turnover Velocity & Stock Aging",
    description: "Annualized inventory velocity, dead stock flags, and fast vs slow-moving SKU classification.",
    href: "/admin/analytics/turnover",
    icon: Activity,
    badge: "Velocity",
    gradient: "from-amber-500/20 via-orange-500/10 to-transparent",
    iconColor: "text-amber-500",
  },
  {
    title: "Accounts Receivable (AR) Aging",
    description: "Bucketed 30/60/90-day wholesale receivables, overdue invoices, and DSO tracking.",
    href: "/admin/analytics/ar-aging",
    icon: CreditCard,
    badge: "Collections",
    gradient: "from-rose-500/20 via-pink-500/10 to-transparent",
    iconColor: "text-rose-500",
  },
  {
    title: "Supplier Performance Scorecards",
    description: "On-time delivery rates, purchase fulfillment accuracy, and purchase return rates.",
    href: "/admin/analytics/suppliers",
    icon: Truck,
    badge: "Vendor SLAs",
    gradient: "from-indigo-500/20 via-purple-500/10 to-transparent",
    iconColor: "text-indigo-500",
  },
  {
    title: "Retailer Performance & Churn Risk",
    description: "Wholesale buyer revenue ranking, order frequency trends, and churn risk heuristics.",
    href: "/admin/analytics/retailers",
    icon: Users,
    badge: "Customer Health",
    gradient: "from-violet-500/20 via-purple-500/10 to-transparent",
    iconColor: "text-violet-500",
  },
  {
    title: "Multi-Warehouse Breakdown",
    description: "Location-level holding valuation, utilization rates, and 30-day throughput metrics.",
    href: "/admin/analytics/warehouses",
    icon: Warehouse,
    badge: "Facilities",
    gradient: "from-cyan-500/20 via-sky-500/10 to-transparent",
    iconColor: "text-cyan-500",
  },
  {
    title: "Shrinkage & Damage Write-offs",
    description: "Damage adjustments, loss rate analysis, and root-cause classification breakdowns.",
    href: "/admin/analytics/shrinkage",
    icon: ShieldAlert,
    badge: "Loss Prevention",
    gradient: "from-red-500/20 via-rose-500/10 to-transparent",
    iconColor: "text-rose-600",
  },
];

export default function AnalyticsLandingPage() {
  const [selectedPeriod, setSelectedPeriod] = useState<string>("30d");
  const [comparisons, setComparisons] = useState<PeriodComparisonsResponse | null>(null);
  const [weeklyReport, setWeeklyReport] = useState<WeeklyReportData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [downloadingPdf, setDownloadingPdf] = useState<boolean>(false);
  const [sendingReport, setSendingReport] = useState<boolean>(false);
  const [sendSuccessMsg, setSendSuccessMsg] = useState<string | null>(null);

  const fetchAnalyticsData = async (period: string) => {
    setLoading(true);
    try {
      const [compRes, reportRes] = await Promise.all([
        apiClient.get<PeriodComparisonsResponse>(`/analytics/period-comparisons?period=${period}`),
        apiClient.get<WeeklyReportData>(`/analytics/weekly-report/latest`),
      ]);
      setComparisons(compRes);
      setWeeklyReport(reportRes);
    } catch (err) {
      console.error("Failed to load analytics executive dashboard", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData(selectedPeriod);
  }, [selectedPeriod]);

  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    try {
      const fileName = `WareFlow_Weekly_Executive_Report_${weeklyReport?.start_date || "latest"}.pdf`;
      await apiClient.downloadBlob("/analytics/weekly-report/pdf", fileName);
    } catch (err) {
      console.error("Failed to download executive PDF report", err);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleSendReportNow = async () => {
    setSendingReport(true);
    setSendSuccessMsg(null);
    try {
      const res = await apiClient.post<{
        success: boolean;
        message: string;
        recipients_count: number;
        channels_used: string[];
      }>("/analytics/weekly-report/send-now", {
        channels: ["email", "whatsapp", "in_app"],
      });
      setSendSuccessMsg(
        `Report dispatched successfully to ${res.recipients_count} recipient(s) across ${res.channels_used.join(", ")}!`
      );
      setTimeout(() => setSendSuccessMsg(null), 6000);
    } catch (err) {
      console.error("Failed to trigger weekly executive report dispatch", err);
    } finally {
      setSendingReport(false);
    }
  };

  const metrics = comparisons?.metrics || {};

  return (
    <AppLayout>
      <div className="space-y-8 pb-12 max-w-7xl mx-auto">
        {/* Header with Period Controls and Action Buttons */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-zinc-200 dark:border-zinc-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
                Analytics & Business Intelligence
              </h1>
              <GlassBadge variant="accent" className="hidden sm:inline-flex">
                Live BI Hub
              </GlassBadge>
            </div>
            <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
              Real-time enterprise metrics, period comparisons, automated executive summaries, and specialized reports.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Period Selector Tabs */}
            <div className="inline-flex rounded-xl bg-zinc-100 dark:bg-zinc-800/80 p-1 border border-zinc-200 dark:border-zinc-700/60">
              {[
                { id: "7d", label: "7D" },
                { id: "30d", label: "30D" },
                { id: "90d", label: "90D" },
                { id: "12m", label: "12M" },
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => setSelectedPeriod(p.id)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                    selectedPeriod === p.id
                      ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-white shadow-sm"
                      : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Download PDF Action */}
            <button
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-medium rounded-xl bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-800 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-700/50 shadow-sm transition-all disabled:opacity-50"
            >
              {downloadingPdf ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5 text-indigo-500" />
              )}
              <span>Weekly PDF</span>
            </button>

            {/* Send Report Action */}
            <button
              onClick={handleSendReportNow}
              disabled={sendingReport}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-md hover:from-indigo-500 hover:to-violet-500 transition-all disabled:opacity-50"
            >
              {sendingReport ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
              <span>Send Report Now</span>
            </button>
          </div>
        </div>

        {/* Dispatch Confirmation Toast */}
        {sendSuccessMsg && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-sm animate-in fade-in slide-in-from-top-2 duration-300">
            <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
            <span className="font-medium">{sendSuccessMsg}</span>
          </div>
        )}

        {/* Live KPI Scorecard with Comparison Badges */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {/* 1. Revenue */}
          <GlassTiltCard className="p-4 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">Total Revenue</span>
              <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-500">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 tabular-nums">
                ₹<AnimatedNumber value={metrics.revenue?.current_value || 0} />
              </div>
              <div className="mt-2 flex items-center justify-between">
                <ComparisonBadge
                  deltaPct={metrics.revenue?.delta_pct}
                  currentValue={metrics.revenue?.current_value}
                  priorValue={metrics.revenue?.prior_value}
                  higherIsBetter={true}
                  periodLabel={`vs prior ${selectedPeriod}`}
                  size="xs"
                />
              </div>
            </div>
          </GlassTiltCard>

          {/* 2. Gross Margin */}
          <GlassTiltCard className="p-4 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">Gross Margin</span>
              <div className="p-2 rounded-xl bg-blue-500/10 text-blue-500">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 tabular-nums">
                <AnimatedNumber value={metrics.gross_margin?.current_value || 0} />%
              </div>
              <div className="mt-2 flex items-center justify-between">
                <ComparisonBadge
                  deltaPct={metrics.gross_margin?.delta_pct}
                  currentValue={metrics.gross_margin?.current_value}
                  priorValue={metrics.gross_margin?.prior_value}
                  higherIsBetter={true}
                  periodLabel={`vs prior ${selectedPeriod}`}
                  size="xs"
                />
              </div>
            </div>
          </GlassTiltCard>

          {/* 3. Stock Holding Valuation */}
          <GlassTiltCard className="p-4 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">Stock Valuation</span>
              <div className="p-2 rounded-xl bg-violet-500/10 text-violet-500">
                <Boxes className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 tabular-nums">
                ₹<AnimatedNumber value={metrics.stock_valuation?.current_value || 0} />
              </div>
              <div className="mt-2 flex items-center justify-between">
                <ComparisonBadge
                  deltaPct={metrics.stock_valuation?.delta_pct}
                  currentValue={metrics.stock_valuation?.current_value}
                  priorValue={metrics.stock_valuation?.prior_value}
                  higherIsBetter={true}
                  periodLabel={`vs prior ${selectedPeriod}`}
                  size="xs"
                />
              </div>
            </div>
          </GlassTiltCard>

          {/* 4. Turnover Velocity */}
          <GlassTiltCard className="p-4 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">Turnover Velocity</span>
              <div className="p-2 rounded-xl bg-amber-500/10 text-amber-500">
                <RefreshCw className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 tabular-nums">
                <AnimatedNumber value={metrics.turnover_rate?.current_value || 0} />x
              </div>
              <div className="mt-2 flex items-center justify-between">
                <ComparisonBadge
                  deltaPct={metrics.turnover_rate?.delta_pct}
                  currentValue={metrics.turnover_rate?.current_value}
                  priorValue={metrics.turnover_rate?.prior_value}
                  higherIsBetter={true}
                  periodLabel={`vs prior ${selectedPeriod}`}
                  size="xs"
                />
              </div>
            </div>
          </GlassTiltCard>

          {/* 5. Units Sold */}
          <GlassTiltCard className="p-4 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">Units Sold</span>
              <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-500">
                <Layers className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 tabular-nums">
                <AnimatedNumber value={metrics.units_sold?.current_value || 0} />
              </div>
              <div className="mt-2 flex items-center justify-between">
                <ComparisonBadge
                  deltaPct={metrics.units_sold?.delta_pct}
                  currentValue={metrics.units_sold?.current_value}
                  priorValue={metrics.units_sold?.prior_value}
                  higherIsBetter={true}
                  periodLabel={`vs prior ${selectedPeriod}`}
                  size="xs"
                />
              </div>
            </div>
          </GlassTiltCard>

          {/* 6. Shrinkage Loss */}
          <GlassTiltCard className="p-4 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">Shrinkage Loss</span>
              <div className="p-2 rounded-xl bg-rose-500/10 text-rose-500">
                <ShieldAlert className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 tabular-nums">
                ₹<AnimatedNumber value={metrics.shrinkage_value?.current_value || 0} />
              </div>
              <div className="mt-2 flex items-center justify-between">
                <ComparisonBadge
                  deltaPct={metrics.shrinkage_value?.delta_pct}
                  currentValue={metrics.shrinkage_value?.current_value}
                  priorValue={metrics.shrinkage_value?.prior_value}
                  higherIsBetter={false}
                  periodLabel={`vs prior ${selectedPeriod}`}
                  size="xs"
                />
              </div>
            </div>
          </GlassTiltCard>
        </div>

        {/* Weekly Executive Summary & Actionable Highlights */}
        {weeklyReport && (
          <GlassCard className="p-6 rounded-3xl border border-zinc-200/80 dark:border-zinc-800/80 bg-gradient-to-br from-white/80 via-white/50 to-indigo-500/5 dark:from-zinc-900/80 dark:via-zinc-900/50 dark:to-indigo-950/20">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-zinc-200/60 dark:border-zinc-800/60">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-indigo-600 text-white shadow-md">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                    Weekly Executive Summary ({weeklyReport.period_label})
                  </h2>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    Compiled automatically every Monday for business owners and leadership.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-zinc-400 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" /> ID: {weeklyReport.report_id}
                </span>
              </div>
            </div>

            {/* Narrative Box */}
            <div className="mt-4 p-4 rounded-2xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200/60 dark:border-zinc-700/60">
              <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed font-normal">
                {weeklyReport.narrative_summary}
              </p>
            </div>

            {/* Highlights Feed & Fast Movers */}
            <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Highlights List */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                  Actionable Operational Alerts
                </h3>
                {weeklyReport.highlights.length > 0 ? (
                  weeklyReport.highlights.map((h, i) => (
                    <div
                      key={i}
                      className="p-3.5 rounded-2xl bg-white/70 dark:bg-zinc-800/70 border border-zinc-200/60 dark:border-zinc-700/60 flex items-start justify-between gap-3 shadow-sm"
                    >
                      <div>
                        <div className="text-xs font-bold text-zinc-900 dark:text-zinc-100">
                          {h.title}
                        </div>
                        <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                          {h.description}
                        </div>
                      </div>
                      <GlassBadge
                        variant={h.badge_variant}
                        className="shrink-0 font-bold"
                      >
                        {h.metric_value}
                      </GlassBadge>
                    </div>
                  ))
                ) : (
                  <div className="p-4 text-center text-xs text-zinc-500">
                    No critical operational anomalies logged for this week.
                  </div>
                )}
              </div>

              {/* Fast Movers vs Sitting Capital */}
              <div className="space-y-4">
                {/* Fast Movers */}
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2">
                    Top Fast-Moving SKUs (7D Revenue)
                  </h3>
                  <div className="space-y-2">
                    {weeklyReport.top_fast_movers.map((m) => (
                      <div
                        key={m.product_id}
                        className="flex items-center justify-between p-2.5 rounded-xl bg-white/70 dark:bg-zinc-800/70 border border-zinc-200/60 dark:border-zinc-700/60 text-xs"
                      >
                        <div>
                          <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                            {m.name}
                          </span>
                          <span className="text-[10px] text-zinc-400 ml-1.5">({m.sku})</span>
                        </div>
                        <div className="font-bold text-emerald-600 dark:text-emerald-400 tabular-nums">
                          ₹{m.revenue.toLocaleString()}
                          <span className="text-[10px] text-zinc-400 ml-1 font-normal">
                            ({m.units} units)
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Slow Movers */}
                {weeklyReport.top_slow_movers.length > 0 && (
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2">
                      Stagnant Capital SKUs (0 Sales in 7D)
                    </h3>
                    <div className="space-y-2">
                      {weeklyReport.top_slow_movers.map((s) => (
                        <div
                          key={s.product_id}
                          className="flex items-center justify-between p-2.5 rounded-xl bg-white/70 dark:bg-zinc-800/70 border border-zinc-200/60 dark:border-zinc-700/60 text-xs"
                        >
                          <div>
                            <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                              {s.name}
                            </span>
                            <span className="text-[10px] text-zinc-400 ml-1.5">({s.on_hand} on hand)</span>
                          </div>
                          <div className="font-bold text-amber-600 dark:text-amber-400 tabular-nums">
                            ₹{s.tied_up_capital.toLocaleString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </GlassCard>
        )}

        {/* 8 Specialized Analytics Modules Hub Directory */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                Specialized BI & Analytics Reports
              </h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Drill down into domain-specific reports across inventory, finance, suppliers, and buyers.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {ANALYTICS_HUBS.map((hub) => {
              const Icon = hub.icon;
              return (
                <Link key={hub.href} href={hub.href} className="group block">
                  <GlassCard
                    className="h-full p-5 rounded-3xl border border-zinc-200/80 dark:border-zinc-800/80 hover:border-indigo-500/40 dark:hover:border-indigo-500/40 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <div className={`p-3 rounded-2xl bg-gradient-to-br ${hub.gradient} ${hub.iconColor} border border-zinc-200/60 dark:border-zinc-700/60`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <GlassBadge variant="neutral">
                          {hub.badge}
                        </GlassBadge>
                      </div>

                      <h3 className="mt-4 text-base font-bold text-zinc-900 dark:text-zinc-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors flex items-center justify-between">
                        <span>{hub.title}</span>
                        <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-indigo-500 shrink-0" />
                      </h3>

                      <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                        {hub.description}
                      </p>
                    </div>

                    <div className="mt-5 pt-3 border-t border-zinc-100 dark:border-zinc-800/60 flex items-center text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                      <span>Open Report & Analytics</span>
                      <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
                    </div>
                  </GlassCard>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
