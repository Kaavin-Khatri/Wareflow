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
  Building2,
  Package,
  Layers,
  ArrowDownLeft,
  ArrowUpRight,
  RefreshCw,
  IndianRupee,
  MapPin,
  Activity,
  ArrowRightLeft,
} from "lucide-react";

export interface WarehouseMetricsItem {
  warehouse_id: string;
  warehouse_name: string;
  location: string | null;
  is_active: boolean;
  total_products_stored: number;
  total_stock_units: number;
  total_stock_value_inr: number;
  inbound_30d_units: number;
  outbound_30d_units: number;
  movement_count_30d: number;
  valuation_share_pct: number;
}

export interface WarehouseBreakdownSummary {
  total_warehouses: number;
  company_total_stock_units: number;
  company_total_valuation_inr: number;
  total_30d_inbound_units: number;
  total_30d_outbound_units: number;
}

export interface WarehouseBreakdownResponse {
  summary: WarehouseBreakdownSummary;
  warehouses: WarehouseMetricsItem[];
  generated_at: string;
}

export default function WarehouseBreakdownPage() {
  const [data, setData] = useState<WarehouseBreakdownResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWarehouseBreakdown = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get<WarehouseBreakdownResponse>(
        "/analytics/warehouse-breakdown"
      );
      setData(res);
    } catch (err: any) {
      console.error("Failed to fetch warehouse breakdown", err);
      setError(err?.message || "Failed to load warehouse breakdown analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWarehouseBreakdown();
  }, []);

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
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500/20 to-indigo-600/20 text-purple-400 ring-1 ring-white/10 shadow-inner">
                <Building2 className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  Warehouse Holdings & Throughput Breakdown
                </h1>
                <p className="text-xs text-white/50">
                  Per-facility inventory valuations, storage concentrations, and 30-day inbound/outbound flow
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <GlassButton
              variant="outline"
              size="sm"
              onClick={fetchWarehouseBreakdown}
              disabled={loading}
              className="gap-1.5"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </GlassButton>
            <Link href="/admin/inventory">
              <GlassButton variant="secondary" size="sm" className="gap-1.5">
                <Layers className="h-4 w-4" />
                <span>Stock Overview</span>
              </GlassButton>
            </Link>
          </div>
        </div>

        {/* Company-Wide KPI Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Total Inventory Asset
              </span>
              <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400">
                <IndianRupee className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-white">
                {formatCurrency(data?.summary?.company_total_valuation_inr ?? 0)}
              </span>
            </div>
            <p className="mt-1 text-xs text-white/40">
              Across {data?.summary?.total_warehouses ?? 0} operating facilities
            </p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                Total Units Stored
              </span>
              <div className="rounded-lg bg-blue-500/10 p-2 text-blue-400">
                <Package className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-white">
                <AnimatedNumber value={data?.summary?.company_total_stock_units ?? 0} />
              </span>
              <span className="text-xs text-white/50">units</span>
            </div>
            <p className="mt-1 text-xs text-white/40">Physical base unit stock on hand</p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                30-Day Inbound Flow
              </span>
              <div className="rounded-lg bg-indigo-500/10 p-2 text-indigo-400">
                <ArrowDownLeft className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-indigo-400">
                <AnimatedNumber value={data?.summary?.total_30d_inbound_units ?? 0} />
              </span>
              <span className="text-xs text-indigo-400/70">units</span>
            </div>
            <p className="mt-1 text-xs text-white/40">Received from PO receipts and returns</p>
          </GlassCard>

          <GlassCard className="relative overflow-hidden p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                30-Day Outbound Flow
              </span>
              <div className="rounded-lg bg-purple-500/10 p-2 text-purple-400">
                <ArrowUpRight className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-purple-400">
                <AnimatedNumber value={data?.summary?.total_30d_outbound_units ?? 0} />
              </span>
              <span className="text-xs text-purple-400/70">units</span>
            </div>
            <p className="mt-1 text-xs text-white/40">Dispatched across sales orders</p>
          </GlassCard>
        </div>

        {/* Warehouse Cards Grid */}
        {error ? (
          <GlassCard className="p-8 text-center text-rose-400 text-sm">{error}</GlassCard>
        ) : loading && !data ? (
          <div className="flex h-64 items-center justify-center">
            <RefreshCw className="h-6 w-6 animate-spin text-white/40" />
          </div>
        ) : !data?.warehouses || data.warehouses.length === 0 ? (
          <GlassCard className="p-12">
            <EmptyState
              icon={<Building2 className="h-8 w-8 text-white/40" />}
              title="No warehouses found"
              description="No warehouse facilities configured in the system."
            />
          </GlassCard>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {data.warehouses.map((wh) => (
              <GlassCard key={wh.warehouse_id} className="relative overflow-hidden p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-white">{wh.warehouse_name}</h3>
                      {wh.is_active ? (
                        <GlassBadge variant="success">Active Facility</GlassBadge>
                      ) : (
                        <GlassBadge variant="neutral">Inactive</GlassBadge>
                      )}
                    </div>
                    {wh.location && (
                      <div className="flex items-center gap-1.5 mt-1 text-xs text-white/40">
                        <MapPin className="h-3.5 w-3.5" />
                        {wh.location}
                      </div>
                    )}
                  </div>

                  <div className="text-right">
                    <div className="text-xl font-bold text-white">
                      {formatCurrency(wh.total_stock_value_inr)}
                    </div>
                    <div className="text-[11px] font-medium text-emerald-400">
                      {wh.valuation_share_pct}% of total inventory
                    </div>
                  </div>
                </div>

                {/* Valuation Progress Bar */}
                <div className="mt-4">
                  <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-500"
                      style={{ width: `${Math.min(wh.valuation_share_pct, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Metric Breakdown Badges */}
                <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <div className="rounded-xl bg-white/[0.02] p-3 ring-1 ring-white/5">
                    <div className="text-[11px] font-medium text-white/40">SKUs Stored</div>
                    <div className="mt-1 text-lg font-bold text-white">
                      {wh.total_products_stored}
                    </div>
                  </div>

                  <div className="rounded-xl bg-white/[0.02] p-3 ring-1 ring-white/5">
                    <div className="text-[11px] font-medium text-white/40">Total Units</div>
                    <div className="mt-1 text-lg font-bold text-white">
                      {wh.total_stock_units}
                    </div>
                  </div>

                  <div className="rounded-xl bg-white/[0.02] p-3 ring-1 ring-white/5">
                    <div className="text-[11px] font-medium text-emerald-400/80">30d Inbound</div>
                    <div className="mt-1 text-lg font-bold text-emerald-400">
                      +{wh.inbound_30d_units}
                    </div>
                  </div>

                  <div className="rounded-xl bg-white/[0.02] p-3 ring-1 ring-white/5">
                    <div className="text-[11px] font-medium text-purple-400/80">30d Outbound</div>
                    <div className="mt-1 text-lg font-bold text-purple-400">
                      -{wh.outbound_30d_units}
                    </div>
                  </div>
                </div>

                {/* Footer Action Links */}
                <div className="mt-6 flex items-center justify-between border-t border-white/5 pt-4 text-xs">
                  <span className="flex items-center gap-1 text-white/40">
                    <Activity className="h-3.5 w-3.5" />
                    {wh.movement_count_30d} ledger transactions (30d)
                  </span>

                  <div className="flex items-center gap-3">
                    <Link
                      href={`/admin/stock/transfer?source_id=${wh.warehouse_id}`}
                      className="flex items-center gap-1 font-medium text-indigo-400 hover:text-indigo-300"
                    >
                      <ArrowRightLeft className="h-3.5 w-3.5" /> Transfer Stock
                    </Link>
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
