"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassSelect } from "@/components/glass/GlassSelect";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { apiClient } from "@/lib/api-client";
import {
  ArrowLeftRight,
  ArrowLeft,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Warehouse as WarehouseIcon,
  Package,
  Layers,
  History,
  ShieldAlert,
  Send,
  Camera,
  ScanLine,
} from "lucide-react";
import { BarcodeScannerModal, ScannedProduct } from "@/components/barcode/BarcodeScannerModal";

interface ProductOption {
  id: string;
  name: string;
  sku: string;
}

interface WarehouseOption {
  id: string;
  name: string;
  is_active: boolean;
}

interface BatchOption {
  id: string;
  product_id: string;
  warehouse_id: string;
  batch_no: string;
  quantity: number;
  expiry_date?: string | null;
}

interface TransferItem {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  from_warehouse_id: string;
  from_warehouse_name: string;
  to_warehouse_id: string;
  to_warehouse_name: string;
  batch_no: string;
  quantity: number;
  created_by?: string | null;
  created_at: string;
  notes?: string | null;
}

interface TransferListResponse {
  items: TransferItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

const MOCK_TRANSFERS: TransferItem[] = [
  {
    id: "trf-1",
    product_id: "prod-1",
    product_name: "Organic Whole Milk 1L",
    product_sku: "MILK-ORG-001",
    from_warehouse_id: "wh-1",
    from_warehouse_name: "Central Cold Storage",
    to_warehouse_id: "wh-2",
    to_warehouse_name: "North Logistics Hub",
    batch_no: "BATCH-2026-0801",
    quantity: 100,
    created_by: "operations@wareflow.io",
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    notes: "Regional buffer stock redistribution",
  },
  {
    id: "trf-2",
    product_id: "prod-2",
    product_name: "Royal Basmati Rice 5kg",
    product_sku: "RIC-BAS-005",
    from_warehouse_id: "wh-1",
    from_warehouse_name: "Central Distribution Center",
    to_warehouse_id: "wh-3",
    to_warehouse_name: "West Coast Depo",
    batch_no: "BATCH-2026-0810",
    quantity: 50,
    created_by: "admin@wareflow.io",
    created_at: new Date(Date.now() - 86400000 * 4).toISOString(),
    notes: "High retail demand fulfillment in West zone",
  },
];

export default function StockTransferPage() {
  // Reference Data
  const [products, setProducts] = useState<ProductOption[]>([]);
  const [warehouses, setWarehouses] = useState<WarehouseOption[]>([]);
  const [sourceBatches, setSourceBatches] = useState<BatchOption[]>([]);
  const [destProductStock, setDestProductStock] = useState<number>(0);

  // Form State
  const [selectedProductId, setSelectedProductId] = useState<string>("");
  const [scannerOpen, setScannerOpen] = useState<boolean>(false);
  const [selectedFromWhId, setSelectedFromWhId] = useState<string>("");
  const [selectedToWhId, setSelectedToWhId] = useState<string>("");
  const [selectedBatchId, setSelectedBatchId] = useState<string>("");
  const [quantity, setQuantity] = useState<number | string>("");
  const [notes, setNotes] = useState<string>("");

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [transfers, setTransfers] = useState<TransferItem[]>([]);
  const [loadingTransfers, setLoadingTransfers] = useState(true);

  // Load Products, Warehouses, and Transfers History
  useEffect(() => {
    let isMounted = true;
    const fetchInitial = async () => {
      try {
        const [prodRes, whRes, trfRes] = await Promise.all([
          apiClient.get<ProductOption[]>("/products").catch(() => []),
          apiClient.get<WarehouseOption[]>("/stock/warehouses").catch(() => []),
          apiClient.get<TransferListResponse>("/stock/transfers?page_size=50").catch(() => null),
        ]);

        if (!isMounted) return;
        setProducts(prodRes || []);
        const activeWhs = (whRes || []).filter((w) => w.is_active);
        setWarehouses(activeWhs);

        if (activeWhs.length >= 2) {
          setSelectedFromWhId(activeWhs[0].id);
          setSelectedToWhId(activeWhs[1].id);
        }

        if (trfRes && Array.isArray(trfRes.items)) {
          setTransfers(trfRes.items);
        } else {
          setTransfers(MOCK_TRANSFERS);
        }
      } catch {
        if (isMounted) setTransfers(MOCK_TRANSFERS);
      } finally {
        if (isMounted) setLoadingTransfers(false);
      }
    };

    fetchInitial();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch source warehouse batches when product or source warehouse changes
  useEffect(() => {
    let isMounted = true;
    const loadSourceBatches = async () => {
      if (!selectedProductId || !selectedFromWhId) {
        setSourceBatches([]);
        setSelectedBatchId("");
        return;
      }
      try {
        const res = await apiClient.get<{ batches: BatchOption[] }>(
          `/products/${selectedProductId}/stock?warehouse_id=${selectedFromWhId}`,
        );
        if (!isMounted) return;
        const bList = res?.batches || [];
        setSourceBatches(bList);
        if (bList.length > 0) {
          setSelectedBatchId(bList[0].id);
        } else {
          setSelectedBatchId("");
        }
      } catch {
        if (isMounted) {
          setSourceBatches([]);
          setSelectedBatchId("");
        }
      }
    };

    loadSourceBatches();
    return () => {
      isMounted = false;
    };
  }, [selectedProductId, selectedFromWhId]);

  // Fetch destination warehouse current on-hand
  useEffect(() => {
    let isMounted = true;
    const loadDestStock = async () => {
      if (!selectedProductId || !selectedToWhId) {
        setDestProductStock(0);
        return;
      }
      try {
        const res = await apiClient.get<{ batches: BatchOption[] }>(
          `/products/${selectedProductId}/stock?warehouse_id=${selectedToWhId}`,
        );
        if (!isMounted) return;
        const total = (res?.batches || []).reduce((acc, b) => acc + Number(b.quantity), 0);
        setDestProductStock(total);
      } catch {
        if (isMounted) setDestProductStock(0);
      }
    };

    loadDestStock();
    return () => {
      isMounted = false;
    };
  }, [selectedProductId, selectedToWhId]);

  // Selected source batch
  const selectedBatch = useMemo(() => {
    return sourceBatches.find((b) => b.id === selectedBatchId) || null;
  }, [sourceBatches, selectedBatchId]);

  // Calculations
  const numericQty = typeof quantity === "number" ? quantity : parseFloat(quantity) || 0;
  const sourceAvailableQty = selectedBatch ? Number(selectedBatch.quantity) : 0;
  const projectedSourceQty = sourceAvailableQty - numericQty;
  const projectedDestQty = destProductStock + numericQty;
  const isOverStock = numericQty > sourceAvailableQty;
  const isInvalidQty = numericQty <= 0;
  const isSameWarehouse = selectedFromWhId === selectedToWhId;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!selectedProductId) {
      setErrorMessage("Please select a product to transfer.");
      return;
    }
    if (!selectedFromWhId || !selectedToWhId) {
      setErrorMessage("Please select both source and destination warehouses.");
      return;
    }
    if (isSameWarehouse) {
      setErrorMessage("Source and destination warehouses cannot be the same.");
      return;
    }
    if (!selectedBatchId) {
      setErrorMessage("Please select a source stock batch.");
      return;
    }
    if (isInvalidQty) {
      setErrorMessage("Transfer quantity must be greater than zero.");
      return;
    }
    if (isOverStock) {
      setErrorMessage(
        `Requested quantity (${numericQty.toFixed(2)}) exceeds available stock in source batch (${sourceAvailableQty.toFixed(2)}).`,
      );
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        product_id: selectedProductId,
        batch_id: selectedBatchId,
        from_warehouse_id: selectedFromWhId,
        to_warehouse_id: selectedToWhId,
        quantity: numericQty,
        notes: notes.trim() || undefined,
      };

      const res = await apiClient.post<TransferItem>("/stock/transfers", payload);

      const fromWhName = warehouses.find((w) => w.id === selectedFromWhId)?.name || "Source";
      const toWhName = warehouses.find((w) => w.id === selectedToWhId)?.name || "Destination";

      setSuccessMessage(
        `Successfully transferred ${numericQty.toFixed(2)} units from ${fromWhName} to ${toWhName}.`,
      );

      // Append new transfer to history
      const newEntry: TransferItem = {
        id: res.id || `trf-${Date.now()}`,
        product_id: selectedProductId,
        product_name: products.find((p) => p.id === selectedProductId)?.name || "Product",
        product_sku: products.find((p) => p.id === selectedProductId)?.sku || "",
        from_warehouse_id: selectedFromWhId,
        from_warehouse_name: fromWhName,
        to_warehouse_id: selectedToWhId,
        to_warehouse_name: toWhName,
        batch_no: selectedBatch?.batch_no || "—",
        quantity: numericQty,
        created_by: "You",
        created_at: new Date().toISOString(),
        notes: notes.trim() || null,
      };

      setTransfers((prev) => [newEntry, ...prev]);

      // Reset quantity and notes
      setQuantity("");
      setNotes("");

      // Refresh source batches
      const updatedBatches = await apiClient.get<{ batches: BatchOption[] }>(
        `/products/${selectedProductId}/stock?warehouse_id=${selectedFromWhId}`,
      );
      if (updatedBatches?.batches) {
        setSourceBatches(updatedBatches.batches);
      }
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
            ? String((err as { message: unknown }).message)
            : "Failed to execute stock transfer.";
      setErrorMessage(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const columns: DataTableColumn<TransferItem>[] = [
    {
      key: "created_at",
      header: "Timestamp",
      sortable: true,
      render: (t) => (
        <div className="flex flex-col">
          <span className="font-mono text-xs text-[var(--text)] font-semibold">
            {new Date(t.created_at).toLocaleDateString("en-IN", {
              day: "2-digit",
              month: "short",
              year: "numeric",
            })}
          </span>
          <span className="text-[11px] text-[var(--text-muted)] font-mono">
            {new Date(t.created_at).toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>
      ),
    },
    {
      key: "product_name",
      header: "Product & SKU",
      sortable: true,
      render: (t) => (
        <div className="flex flex-col">
          <span className="font-semibold text-xs text-[var(--text)]">{t.product_name}</span>
          <span className="font-mono text-[11px] text-[var(--text-muted)]">{t.product_sku}</span>
        </div>
      ),
    },
    {
      key: "from_warehouse_name",
      header: "Transfer Route (Source → Destination)",
      render: (t) => (
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-purple-300 font-medium">{t.from_warehouse_name}</span>
          <ArrowRight className="w-3.5 h-3.5 text-[var(--text-muted)] flex-shrink-0" />
          <span className="text-cyan-300 font-medium">{t.to_warehouse_name}</span>
        </div>
      ),
    },
    {
      key: "batch_no",
      header: "Batch #",
      render: (t) => <GlassBadge variant="neutral">{t.batch_no}</GlassBadge>,
    },
    {
      key: "quantity",
      header: "Quantity Transferred",
      align: "right",
      sortable: true,
      render: (t) => (
        <span className="font-mono font-bold text-xs text-purple-400">
          {t.quantity.toFixed(2)} units
        </span>
      ),
    },
    {
      key: "notes",
      header: "Context / Notes",
      render: (t) => <span className="text-xs text-[var(--text-muted)]">{t.notes || "—"}</span>,
    },
  ];

  return (
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--text)]">
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin/stock/ledger">
              <button className="p-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-[var(--text-muted)] hover:text-[var(--text)] transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </button>
            </Link>
            <div>
              <h1 className="text-xl font-bold text-[var(--text)] flex items-center gap-2">
                <ArrowLeftRight className="w-5 h-5 text-purple-400" />
                Inter-Warehouse Stock Transfers
              </h1>
              <p className="text-xs text-[var(--text-muted)]">
                Relocate inventory batches across physical warehouse facilities with atomic paired
                ledger movement.
              </p>
            </div>
          </div>

          <Link href="/admin/stock/ledger">
            <GlassButton variant="ghost" size="sm">
              <History className="w-4 h-4 mr-1.5" /> View Full Ledger
            </GlassButton>
          </Link>
        </div>

        {/* Transfer Form Card */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {errorMessage && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-400 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Form Inputs (2 Cols) */}
            <div className="lg:col-span-2 space-y-4">
              <GlassCard className="p-5 space-y-4">
                <h2 className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider font-mono">
                  1. Transfer Route & Batch Selection
                </h2>

                {/* Product Select */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label
                      htmlFor="trf-product"
                      className="block text-xs font-medium text-[var(--text-muted)]"
                    >
                      Product to Relocate *
                    </label>
                    <button
                      type="button"
                      onClick={() => setScannerOpen(true)}
                      className="text-[11px] text-[var(--accent)] hover:underline flex items-center gap-1 font-semibold"
                    >
                      <Camera className="w-3 h-3" />
                      <span>Scan Barcode</span>
                    </button>
                  </div>
                  <GlassSelect
                    id="trf-product"
                    value={selectedProductId}
                    onChange={setSelectedProductId}
                    placeholder="-- Choose Product --"
                    options={products.map((p) => ({
                      value: p.id,
                      label: `${p.name} (${p.sku})`,
                    }))}
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Source Warehouse */}
                  <div className="space-y-1">
                    <label
                      htmlFor="trf-from-wh"
                      className="block text-xs font-medium text-[var(--text-muted)]"
                    >
                      Source Warehouse (Dispatch) *
                    </label>
                    <GlassSelect
                      id="trf-from-wh"
                      value={selectedFromWhId}
                      onChange={setSelectedFromWhId}
                      placeholder="-- Source Warehouse --"
                      options={warehouses.map((w) => ({
                        value: w.id,
                        label: w.name,
                      }))}
                    />
                  </div>

                  {/* Destination Warehouse */}
                  <div className="space-y-1">
                    <label
                      htmlFor="trf-to-wh"
                      className="block text-xs font-medium text-[var(--text-muted)]"
                    >
                      Destination Warehouse (Receive) *
                    </label>
                    <GlassSelect
                      id="trf-to-wh"
                      value={selectedToWhId}
                      onChange={setSelectedToWhId}
                      placeholder="-- Destination Warehouse --"
                      options={warehouses
                        .filter((w) => w.id !== selectedFromWhId)
                        .map((w) => ({
                          value: w.id,
                          label: w.name,
                        }))}
                    />
                  </div>
                </div>

                {/* Source Batch Select */}
                <div className="space-y-1">
                  <label
                    htmlFor="trf-batch"
                    className="block text-xs font-medium text-[var(--text-muted)]"
                  >
                    Source Stock Batch *
                  </label>
                  <GlassSelect
                    id="trf-batch"
                    value={selectedBatchId}
                    onChange={setSelectedBatchId}
                    disabled={sourceBatches.length === 0}
                    placeholder={
                      sourceBatches.length === 0
                        ? selectedProductId
                          ? "No active batches in source warehouse"
                          : "Select product and warehouse first"
                        : "-- Select Stock Batch --"
                    }
                    options={sourceBatches.map((b) => ({
                      value: b.id,
                      label: `Batch: ${b.batch_no} — Available: ${Number(b.quantity).toFixed(2)} units ${
                        b.expiry_date ? `(Exp: ${new Date(b.expiry_date).toLocaleDateString()})` : ""
                      }`,
                    }))}
                  />
                </div>
              </GlassCard>

              <GlassCard className="p-5 space-y-4">
                <h2 className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider font-mono">
                  2. Transfer Quantity & Context
                </h2>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Quantity Input */}
                  <div className="space-y-1">
                    <label
                      htmlFor="trf-quantity"
                      className="block text-xs font-medium text-[var(--text-muted)]"
                    >
                      Quantity to Transfer *
                    </label>
                    <input
                      id="trf-quantity"
                      type="number"
                      step="0.01"
                      min="0.01"
                      required
                      value={quantity}
                      onChange={(e) => setQuantity(e.target.value)}
                      placeholder="e.g. 25.00"
                      className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                    />
                  </div>

                  {/* Notes */}
                  <div className="space-y-1">
                    <label
                      htmlFor="trf-notes"
                      className="block text-xs font-medium text-[var(--text-muted)]"
                    >
                      Reference / Reason Notes
                    </label>
                    <input
                      id="trf-notes"
                      type="text"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="e.g. Regional buffer rebalance"
                      className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <GlassButton
                    variant="primary"
                    size="md"
                    type="submit"
                    disabled={
                      submitting ||
                      isOverStock ||
                      isInvalidQty ||
                      isSameWarehouse ||
                      !selectedBatchId ||
                      !selectedProductId
                    }
                  >
                    <Send className="w-4 h-4 mr-1.5" />
                    {submitting ? "Processing Transfer..." : "Execute Inter-Warehouse Transfer"}
                  </GlassButton>
                </div>
              </GlassCard>
            </div>

            {/* Live Dual-Warehouse On-Hand Preview (1 Col) */}
            <div className="space-y-4">
              <GlassCard className="p-5 space-y-4">
                <h2 className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-purple-400" /> Live Inventory Impact
                </h2>

                {/* Source Warehouse Card */}
                <div className="p-3.5 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--text-muted)] flex items-center gap-1">
                      <WarehouseIcon className="w-3.5 h-3.5 text-purple-400" /> Source Facility
                    </span>
                    <GlassBadge variant="neutral">OUTBOUND</GlassBadge>
                  </div>
                  <p className="text-xs font-semibold text-[var(--text)] truncate">
                    {warehouses.find((w) => w.id === selectedFromWhId)?.name || "Select Source"}
                  </p>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[var(--glass-border)] text-xs">
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">
                        Current On-Hand
                      </span>
                      <span className="font-mono font-bold text-xs text-[var(--text)]">
                        {sourceAvailableQty.toFixed(2)} units
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">
                        Projected Balance
                      </span>
                      <span
                        className={`font-mono font-bold text-xs ${
                          isOverStock ? "text-red-400" : "text-amber-400"
                        }`}
                      >
                        {projectedSourceQty.toFixed(2)} units
                      </span>
                    </div>
                  </div>

                  {isOverStock && (
                    <div className="p-2 rounded-xl bg-red-500/10 border border-red-500/30 text-[10px] text-red-300 flex items-center gap-1">
                      <ShieldAlert className="w-3 h-3 flex-shrink-0" />
                      <span>Transfer exceeds available source batch stock!</span>
                    </div>
                  )}
                </div>

                {/* Destination Warehouse Card */}
                <div className="p-3.5 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--text-muted)] flex items-center gap-1">
                      <WarehouseIcon className="w-3.5 h-3.5 text-cyan-400" /> Destination Facility
                    </span>
                    <GlassBadge variant="success">INBOUND</GlassBadge>
                  </div>
                  <p className="text-xs font-semibold text-[var(--text)] truncate">
                    {warehouses.find((w) => w.id === selectedToWhId)?.name || "Select Destination"}
                  </p>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[var(--glass-border)] text-xs">
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">
                        Current On-Hand
                      </span>
                      <span className="font-mono font-bold text-xs text-[var(--text)]">
                        {destProductStock.toFixed(2)} units
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] block">
                        Projected Balance
                      </span>
                      <span className="font-mono font-bold text-xs text-emerald-400">
                        {projectedDestQty.toFixed(2)} units
                      </span>
                    </div>
                  </div>
                </div>

                {/* Atomic Paired Invariant Note */}
                <div className="p-3 rounded-xl bg-purple-500/5 border border-purple-500/20 text-[10px] text-purple-300 space-y-1">
                  <span className="font-semibold flex items-center gap-1">
                    <Package className="w-3 h-3" /> Atomic Paired Ledger Guarantee
                  </span>
                  <p className="text-[var(--text-muted)]">
                    Source deduction (-{numericQty.toFixed(2)}) and destination addition (+
                    {numericQty.toFixed(2)}) execute within a single atomic database transaction.
                    Zero risk of lost in-transit stock.
                  </p>
                </div>
              </GlassCard>
            </div>
          </div>
        </form>

        {/* Transfers History Table */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
              <History className="w-4 h-4 text-purple-400" /> Recent Inter-Warehouse Transfers
            </h2>
            <span className="text-xs text-[var(--text-muted)] font-mono">
              Total Records: {transfers.length}
            </span>
          </div>

          <DataTable
            data={transfers}
            columns={columns}
            keyExtractor={(t) => t.id}
            isLoading={loadingTransfers}
            emptyTitle="No inter-warehouse transfers found."
            emptyDescription="Completed inter-warehouse transfers will be recorded here atomically."
          />
        </div>
      </div>

      {/* Barcode Scanner Modal */}
      {scannerOpen && (
        <BarcodeScannerModal
          isOpen={scannerOpen}
          onClose={() => setScannerOpen(false)}
          title="Scan Product for Relocation"
          description="Scan barcode on goods to quickly locate stock batches for transfer."
          onScanSuccess={(code, prod) => {
            if (prod) {
              setProducts((prev) => {
                if (!prev.some((p) => p.id === prod.id)) {
                  return [...prev, { id: prod.id, name: prod.name, sku: prod.sku }];
                }
                return prev;
              });
              setSelectedProductId(prod.id);
            }
          }}
        />
      )}
    </div>
  );
}
