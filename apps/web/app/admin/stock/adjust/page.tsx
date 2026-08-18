"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { apiClient } from "@/lib/api-client";
import {
  SlidersHorizontal,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Package,
  ShieldAlert,
  Lock,
} from "lucide-react";

interface ProductOption {
  id: string;
  name: string;
  sku: string;
}

interface WarehouseOption {
  id: string;
  name: string;
}

interface BatchOption {
  id: string;
  product_id: string;
  warehouse_id: string;
  batch_no: string;
  quantity: number;
  expiry_date?: string | null;
}

interface UserProfile {
  id: string;
  email: string;
  role: string;
  permissions: string[];
}

export default function StockAdjustPage() {
  // Reference Data
  const [products, setProducts] = useState<ProductOption[]>([]);
  const [warehouses, setWarehouses] = useState<WarehouseOption[]>([]);
  const [batches, setBatches] = useState<BatchOption[]>([]);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);

  // Form state
  const [selectedProductId, setSelectedProductId] = useState<string>("");

  const [selectedWarehouseId, setSelectedWarehouseId] = useState<string>("");
  const [selectedBatchId, setSelectedBatchId] = useState<string>("");
  const [delta, setDelta] = useState<number | string>("");
  const [reason, setReason] = useState<"damage" | "loss" | "recount" | "other">("damage");
  const [notes, setNotes] = useState<string>("");

  // Submitting state
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<{
    previous_quantity: number;
    new_quantity: number;
    delta: number;
    batch_no?: string;
  } | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadInitialData = async () => {
      try {
        const [productsRes, warehousesRes, userRes] = await Promise.all([
          apiClient.get<ProductOption[]>("/products").catch(() => []),
          apiClient.get<WarehouseOption[]>("/stock/warehouses").catch(() => []),
          apiClient.get<UserProfile>("/me").catch(() => null),
        ]);

        if (!isMounted) return;
        setProducts(productsRes || []);
        setWarehouses(warehousesRes || []);
        setCurrentUser(userRes);

        // Pre-select first warehouse if available
        if (warehousesRes && warehousesRes.length > 0) {
          setSelectedWarehouseId(warehousesRes[0].id);
        }
      } catch (err) {
        console.error("Failed to load adjustment reference data:", err);
      }
    };

    loadInitialData();
    return () => {
      isMounted = false;
    };
  }, []);


  // Fetch batches when product or warehouse changes
  useEffect(() => {
    let isMounted = true;
    const loadBatches = async () => {
      if (!selectedProductId) {
        setBatches([]);
        setSelectedBatchId("");
        return;
      }
      try {
        const queryParams = selectedWarehouseId ? `?warehouse_id=${selectedWarehouseId}` : "";
        const res = await apiClient.get<{ batches: BatchOption[] }>(
          `/products/${selectedProductId}/stock${queryParams}`
        );
        if (!isMounted) return;
        const availableBatches = res?.batches || [];
        setBatches(availableBatches);
        if (availableBatches.length > 0) {
          setSelectedBatchId(availableBatches[0].id);
        } else {
          setSelectedBatchId("");
        }
      } catch {
        if (isMounted) {
          setBatches([]);
          setSelectedBatchId("");
        }
      }
    };

    loadBatches();
    return () => {
      isMounted = false;
    };
  }, [selectedProductId, selectedWarehouseId]);

  // Selected batch object
  const selectedBatch = useMemo(() => {
    return batches.find((b) => b.id === selectedBatchId) || null;
  }, [batches, selectedBatchId]);

  // Check if caller holds recount permission
  const hasRecountPermission = useMemo(() => {
    if (!currentUser) return false;
    if (currentUser.role?.toLowerCase() === "owner") return true;
    return (
      currentUser.permissions?.includes("stock:recount") ||
      currentUser.permissions?.includes("stock.recount")
    );
  }, [currentUser]);

  // Real-time projected batch quantity
  const numericDelta = typeof delta === "number" ? delta : parseFloat(delta) || 0;
  const currentBatchQty = selectedBatch ? Number(selectedBatch.quantity) : 0;
  const projectedQty = currentBatchQty + numericDelta;
  const isNegativeProjected = projectedQty < 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!selectedProductId) {
      setErrorMessage("Please select a product.");
      return;
    }
    if (!selectedWarehouseId) {
      setErrorMessage("Please select a warehouse.");
      return;
    }
    if (!selectedBatchId) {
      setErrorMessage("Please select a stock batch.");
      return;
    }
    if (numericDelta === 0) {
      setErrorMessage("Adjustment quantity delta cannot be zero.");
      return;
    }
    if (isNegativeProjected) {
      setErrorMessage(
        `Adjustment would result in negative stock quantity (${projectedQty.toFixed(2)}).`
      );
      return;
    }
    if (reason === "recount" && !hasRecountPermission) {
      setErrorMessage("Recount adjustments require manager or owner recount permission.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        product_id: selectedProductId,
        warehouse_id: selectedWarehouseId,
        batch_id: selectedBatchId,
        delta: numericDelta,
        reason,
        notes: notes.trim() || undefined,
      };

      const res = await apiClient.post<{
        previous_quantity: number;
        new_quantity: number;
        delta: number;
      }>("/stock/adjustments", payload);

      setSuccessData({
        previous_quantity: res.previous_quantity,
        new_quantity: res.new_quantity,
        delta: res.delta,
        batch_no: selectedBatch?.batch_no,
      });
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
          ? String((err as { message: unknown }).message)
          : "Failed to record stock adjustment.";
      setErrorMessage(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--text)]">
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-4xl mx-auto">
        {/* Header with Back Button */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin/stock/ledger">
              <button className="p-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-[var(--text-muted)] hover:text-[var(--text)] transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </button>
            </Link>
            <div>
              <h1 className="text-xl font-bold text-[var(--text)] flex items-center gap-2">
                <SlidersHorizontal className="w-5 h-5 text-purple-400" />
                Record Stock Adjustment
              </h1>
              <p className="text-xs text-[var(--text-muted)]">
                Direct write path for physical count variance, transit damage, shrinkage, and authorized audit recounts.
              </p>
            </div>
          </div>
        </div>

        {/* Success Confirmation Card */}
        {successData ? (
          <GlassCard className="p-6 space-y-4 text-center">
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-[var(--text)]">Stock Adjustment Recorded</h2>
            <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto">
              Batch <span className="font-mono text-cyan-400">{successData.batch_no || "selected"}</span> was adjusted by{" "}
              <span className={`font-bold font-mono ${successData.delta > 0 ? "text-emerald-400" : "text-red-400"}`}>
                {successData.delta > 0 ? `+${successData.delta}` : successData.delta}
              </span>{" "}
              units. An immutable record has been appended to the Movement Ledger.
            </p>

            <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto p-3 rounded-2xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs">
              <div>
                <span className="text-[var(--text-muted)] block text-[11px]">Previous On-Hand</span>
                <span className="font-mono font-bold text-sm text-[var(--text)]">
                  {successData.previous_quantity.toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-[var(--text-muted)] block text-[11px]">New On-Hand</span>
                <span className="font-mono font-bold text-sm text-emerald-400">
                  {successData.new_quantity.toFixed(2)}
                </span>
              </div>
            </div>

            <div className="flex justify-center gap-3 pt-2">
              <GlassButton
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSuccessData(null);
                  setDelta("");
                  setNotes("");
                }}
              >
                Record Another Adjustment
              </GlassButton>
              <Link href="/admin/stock/ledger">
                <GlassButton variant="primary" size="sm">
                  View Movement Ledger
                </GlassButton>
              </Link>
            </div>
          </GlassCard>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {errorMessage && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <GlassCard className="p-5 space-y-4">
              <h2 className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider font-mono">
                1. Target Inventory Batch
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Product Select */}
                <div className="space-y-1">
                  <label htmlFor="adjust-product" className="block text-xs font-medium text-[var(--text-muted)]">
                    Product *
                  </label>
                  <select
                    id="adjust-product"
                    value={selectedProductId}
                    onChange={(e) => setSelectedProductId(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                  >
                    <option value="">-- Choose Product --</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.sku})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Warehouse Select */}
                <div className="space-y-1">
                  <label htmlFor="adjust-warehouse" className="block text-xs font-medium text-[var(--text-muted)]">
                    Warehouse Location *
                  </label>
                  <select
                    id="adjust-warehouse"
                    value={selectedWarehouseId}
                    onChange={(e) => setSelectedWarehouseId(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                  >
                    <option value="">-- Choose Warehouse --</option>
                    {warehouses.map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Batch Select */}
              <div className="space-y-1">
                <label htmlFor="adjust-batch" className="block text-xs font-medium text-[var(--text-muted)]">
                  Stock Batch *
                </label>
                <select
                  id="adjust-batch"
                  value={selectedBatchId}
                  onChange={(e) => setSelectedBatchId(e.target.value)}
                  required
                  disabled={batches.length === 0}
                  className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500 disabled:opacity-50"
                >
                  {batches.length === 0 ? (
                    <option value="">
                      {selectedProductId ? "No active batches in selected warehouse" : "Select a product first"}
                    </option>
                  ) : (
                    batches.map((b) => (
                      <option key={b.id} value={b.id}>
                        Batch: {b.batch_no} — On Hand: {Number(b.quantity).toFixed(2)} units{" "}
                        {b.expiry_date ? `(Exp: ${new Date(b.expiry_date).toLocaleDateString()})` : ""}
                      </option>
                    ))
                  )}
                </select>
              </div>

              {selectedBatch && (
                <div className="p-3 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)] flex items-center justify-between text-xs">
                  <span className="text-[var(--text-muted)]">Current Batch On-Hand:</span>
                  <span className="font-mono font-bold text-sm text-[var(--text)]">
                    {Number(selectedBatch.quantity).toFixed(2)} units
                  </span>
                </div>
              )}
            </GlassCard>

            <GlassCard className="p-5 space-y-4">
              <h2 className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider font-mono">
                2. Adjustment Details
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Delta Input */}
                <div className="space-y-1">
                  <label htmlFor="adjust-delta" className="block text-xs font-medium text-[var(--text-muted)]">
                    Quantity Delta (+ / -) *
                  </label>
                  <input
                    id="adjust-delta"
                    type="number"
                    step="0.01"
                    required
                    value={delta}
                    onChange={(e) => setDelta(e.target.value)}
                    placeholder="e.g. -5 for loss/damage or +10 for recount"
                    className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                  />
                  <span className="text-[10px] text-[var(--text-muted)] block">
                    Use negative values to deduct (damage, shrinkage) and positive to add (audit recount).
                  </span>
                </div>

                {/* Reason Select */}
                <div className="space-y-1">
                  <label htmlFor="adjust-reason" className="block text-xs font-medium text-[var(--text-muted)]">
                    Adjustment Reason *
                  </label>
                  <select
                    id="adjust-reason"
                    value={reason}
                    onChange={(e) => setReason(e.target.value as "damage" | "loss" | "recount" | "other")}
                    className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                  >
                    <option value="damage">Damage (Physical breakage, leak, spoilt)</option>
                    <option value="loss">Loss (Shrinkage, missing units)</option>
                    <option value="recount" disabled={!hasRecountPermission}>
                      Recount (Audit count variance) {!hasRecountPermission ? "🔒 Requires Recount Permission" : ""}
                    </option>
                    <option value="other">Other (General inventory correction)</option>
                  </select>
                  {!hasRecountPermission && (
                    <span className="text-[10px] text-amber-400 flex items-center gap-1 mt-0.5">
                      <Lock className="w-3 h-3" /> Recount requires Manager / Owner role permission.
                    </span>
                  )}
                </div>
              </div>

              {/* Real-time Projected Balance Preview */}
              {selectedBatch && (
                <div
                  className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
                    isNegativeProjected
                      ? "bg-red-500/10 border-red-500/30 text-red-300"
                      : "bg-[var(--surface-hover)] border-[var(--glass-border)] text-[var(--text)]"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {isNegativeProjected ? (
                      <ShieldAlert className="w-4 h-4 text-red-400" />
                    ) : (
                      <Package className="w-4 h-4 text-purple-400" />
                    )}
                    <span>Projected Resulting Batch Quantity:</span>
                  </div>
                  <span className={`font-mono font-bold text-sm ${isNegativeProjected ? "text-red-400" : "text-emerald-400"}`}>
                    {projectedQty.toFixed(2)} units
                  </span>
                </div>
              )}

              {/* Free-text Notes */}
              <div className="space-y-1">
                <label htmlFor="adjust-notes" className="block text-xs font-medium text-[var(--text-muted)]">
                  Context Notes / Investigation Reference
                </label>
                <textarea
                  id="adjust-notes"
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Broken packaging found during morning inspection in Bay 4; reported by Sunil."
                  className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500 resize-none"
                />
              </div>
            </GlassCard>

            <div className="flex items-center justify-end gap-3">
              <Link href="/admin/stock/ledger">
                <GlassButton variant="ghost" size="md" type="button">
                  Cancel
                </GlassButton>
              </Link>
              <GlassButton
                variant="primary"
                size="md"
                type="submit"
                disabled={submitting || isNegativeProjected || !selectedBatchId || numericDelta === 0}
              >
                {submitting ? "Processing..." : "Commit Stock Adjustment"}
              </GlassButton>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
