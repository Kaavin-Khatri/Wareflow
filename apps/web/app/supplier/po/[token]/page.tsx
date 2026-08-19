"use client";

import { use, useEffect, useState } from "react";
import {
  Boxes,
  Calendar,
  CheckCircle2,
  Clock,
  FileSpreadsheet,
  IndianRupee,
  Loader2,
  PackageCheck,
  ShieldAlert,
  Truck,
} from "lucide-react";

import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassCard } from "@/components/glass/GlassCard";
import { apiClient, ApiError } from "@/lib/api-client";

interface POItem {
  id: string;
  product_name: string;
  product_sku: string;
  qty_ordered: number;
  qty_received: number;
  unit_cost: number;
  uom_name: string | null;
  base_uom_name: string | null;
  line_total: number;
}

interface SupplierPO {
  po_id: string;
  po_number: string;
  supplier_id: string;
  supplier_name: string;
  status: string;
  order_date: string;
  expected_date: string | null;
  total_amount: number;
  items: POItem[];
}

export default function SupplierPOPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const resolvedParams = use(params);
  const token = resolvedParams.token;

  const [po, setPo] = useState<SupplierPO | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    async function fetchPO() {
      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.get<SupplierPO>(`/supplier-portal/${token}`);
        if (!ignore) {
          setPo(data);
          if (data.status === "ready_for_dispatch") {
            setSuccessMessage("This purchase order has already been marked ready for dispatch.");
          }
        }
      } catch (err: unknown) {
        if (!ignore) {
          if (err instanceof ApiError && err.status === 410) {
            setError("This magic link has expired. Please contact the buyer for a new link.");
          } else if (err instanceof ApiError && err.status === 404) {
            setError("Invalid magic link or purchase order not found.");
          } else {
            setError(err instanceof Error ? err.message : "Failed to load purchase order.");
          }
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    if (token) {
      fetchPO();
    }
    return () => {
      ignore = true;
    };
  }, [token]);

  const handleMarkReady = async () => {
    try {
      setSubmitting(true);
      setError(null);
      const res = await apiClient.post<{ success: boolean; message: string; status: string }>(
        `/supplier-portal/${token}/ready-for-dispatch`,
      );
      setSuccessMessage(
        res.message || "Order marked ready for dispatch. Warehouse staff has been notified for pickup.",
      );
      if (po) {
        setPo({ ...po, status: "ready_for_dispatch" });
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to mark ready for dispatch.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4 md:p-8 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-1/3 w-80 h-80 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-3xl space-y-6 relative z-10">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs text-indigo-300">
            <Truck className="w-3.5 h-3.5 text-cyan-400" />
            <span>WareFlow Supplier Dispatch Portal</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
            Purchase Order Dispatch Signal
          </h1>
          <p className="text-sm text-slate-400">
            No login required &bull; Confirm consignment readiness for inbound warehouse logistics
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <GlassCard className="p-12 text-center space-y-4">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
            <p className="text-sm text-slate-300">Verifying secure magic link and loading order details...</p>
          </GlassCard>
        )}

        {/* Error State */}
        {!loading && error && (
          <GlassCard className="p-8 text-center space-y-4 border-rose-500/30 bg-rose-950/20">
            <div className="w-12 h-12 rounded-full bg-rose-500/20 border border-rose-500/30 flex items-center justify-center mx-auto text-rose-400">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-semibold text-rose-200">Unable to Access Purchase Order</h2>
            <p className="text-sm text-rose-300/80 max-w-md mx-auto">{error}</p>
          </GlassCard>
        )}

        {/* Success Confirmation State */}
        {!loading && successMessage && po && (
          <GlassCard className="p-8 text-center space-y-4 border-emerald-500/30 bg-emerald-950/20">
            <div className="w-14 h-14 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-400 shadow-lg shadow-emerald-500/20">
              <PackageCheck className="w-7 h-7" />
            </div>
            <h2 className="text-xl font-bold text-white">Goods Ready for Dispatch!</h2>
            <p className="text-sm text-emerald-300/90 max-w-md mx-auto">{successMessage}</p>
            <div className="pt-2 text-xs text-slate-400">
              Purchase Order <span className="font-mono text-slate-200 font-semibold">{po.po_number}</span> is scheduled for warehouse pickup / receiving.
            </div>
          </GlassCard>
        )}

        {/* Main PO Content Card */}
        {!loading && po && (
          <GlassCard className="p-6 space-y-6">
            {/* Header info */}
            <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-white/10">
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider block">Order Number</span>
                <span className="text-xl font-bold text-white font-mono">{po.po_number}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider block">Supplier</span>
                <span className="text-base font-semibold text-slate-200">{po.supplier_name}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider block">Status</span>
                <div className="mt-1">
                  {po.status === "ready_for_dispatch" ? (
                    <GlassBadge variant="accent" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20">
                      Ready for Dispatch
                    </GlassBadge>
                  ) : po.status === "ordered" ? (
                    <GlassBadge variant="accent">Awaiting Dispatch</GlassBadge>
                  ) : (
                    <GlassBadge variant="neutral">{po.status}</GlassBadge>
                  )}
                </div>
              </div>
            </div>

            {/* Key metadata grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5">
                <span className="text-slate-400 flex items-center gap-1.5 mb-1">
                  <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                  Order Placed
                </span>
                <span className="font-semibold text-slate-200">
                  {new Date(po.order_date).toLocaleDateString()}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5">
                <span className="text-slate-400 flex items-center gap-1.5 mb-1">
                  <Clock className="w-3.5 h-3.5 text-amber-400" />
                  Expected Delivery
                </span>
                <span className="font-semibold text-slate-200">
                  {po.expected_date ? new Date(po.expected_date).toLocaleDateString() : "Immediate"}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5 col-span-2 sm:col-span-1">
                <span className="text-slate-400 flex items-center gap-1.5 mb-1">
                  <IndianRupee className="w-3.5 h-3.5 text-emerald-400" />
                  Total Value
                </span>
                <span className="font-semibold text-emerald-400 font-mono">
                  ₹{po.total_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            {/* Line items table */}
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Boxes className="w-3.5 h-3.5 text-indigo-400" />
                Ordered Line Items ({po.items.length})
              </h3>
              <div className="divide-y divide-white/5 rounded-xl bg-slate-900/40 border border-white/5 overflow-hidden">
                {po.items.map((item) => (
                  <div
                    key={item.id}
                    className="p-3.5 flex items-center justify-between gap-4 text-xs hover:bg-white/[0.02] transition-colors"
                  >
                    <div className="space-y-0.5">
                      <p className="font-semibold text-slate-200 text-sm">{item.product_name}</p>
                      <p className="text-slate-400 font-mono text-[11px]">
                        SKU: {item.product_sku} &bull; Unit Rate: ₹{item.unit_cost.toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right space-y-0.5">
                      <p className="font-semibold text-white font-mono">
                        {item.qty_ordered} {item.uom_name || "Units"}
                      </p>
                      <p className="text-emerald-400 font-mono font-medium text-[11px]">
                        ₹{item.line_total.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Section */}
            {po.status === "ordered" && !successMessage && (
              <div className="pt-4 border-t border-white/10 space-y-3">
                <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300">
                  <span className="font-semibold text-white">Action Required:</span> When the consignment is packed and ready at your loading dock, click the button below to notify WareFlow warehouse staff immediately.
                </div>

                <GlassButton
                  variant="primary"
                  size="lg"
                  onClick={handleMarkReady}
                  disabled={submitting}
                  className="w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold shadow-lg shadow-indigo-500/20"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Notifying Warehouse Operations...</span>
                    </>
                  ) : (
                    <>
                      <Truck className="w-4 h-4" />
                      <span>Mark Consignment Ready for Dispatch</span>
                    </>
                  )}
                </GlassButton>
              </div>
            )}
          </GlassCard>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-slate-500 pt-4">
          WareFlow AI Wholesale Inventory & Procurement Network &bull; Secure Magic Link
        </div>
      </div>
    </div>
  );
}
