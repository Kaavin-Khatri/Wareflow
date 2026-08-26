"use client";

import { useEffect, useState, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { ListViewTemplate } from "@/components/templates/ListViewTemplate";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassInput } from "@/components/glass/GlassInput";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassCard } from "@/components/glass/GlassCard";
import { apiClient } from "@/lib/api-client";
import {
  Undo2,
  Plus,
  Truck,
  CheckCircle2,
  AlertCircle,
  Clock,
  Boxes,
  Eye,
  Trash2,
  ArrowRight,
  ReceiptText,
} from "lucide-react";

export type PurchaseReturnStatus = "requested" | "shipped" | "credited";

export interface PurchaseReturnItem {
  id: string;
  return_id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  qty: number;
  batch_id: string;
  batch_no: string;
  reason?: string | null;
}

export interface PurchaseReturn {
  id: string;
  purchase_order_id: string;
  po_number: string;
  supplier_id: string;
  supplier_name: string;
  status: PurchaseReturnStatus;
  reason?: string | null;
  credit_note_ref?: string | null;
  requested_at: string;
  items_count: number;
  total_qty: number;
  items: PurchaseReturnItem[];
}

interface PurchaseOrderItemType {
  id: string;
  po_number: string;
  supplier_id: string;
  supplier_name: string;
  status: string;
  items: {
    id: string;
    product_id: string;
    product_name: string;
    product_sku: string;
    qty_ordered: number;
    qty_received: number;
  }[];
}

interface StockBatchOption {
  id: string;
  product_id: string;
  product_name?: string;
  batch_no: string;
  quantity: number;
  warehouse_id: string;
}

interface SupplierOption {
  id: string;
  name: string;
  is_active: boolean;
}

function PurchaseReturnsContent() {
  const searchParams = useSearchParams();
  const prefillPoId = searchParams.get("po_id");

  const [returns, setReturns] = useState<PurchaseReturn[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrderItemType[]>([]);
  const [batches, setBatches] = useState<StockBatchOption[]>([]);
  const [suppliers, setSuppliers] = useState<SupplierOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedSupplierId, setSelectedSupplierId] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modals state
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [activeReturn, setActiveReturn] = useState<PurchaseReturn | null>(null);

  // Create Return Form State
  const [returnPoId, setReturnPoId] = useState<string>("");
  const [returnReason, setReturnReason] = useState<string>("");
  const [returnLines, setReturnLines] = useState<
    {
      product_id: string;
      batch_id: string;
      qty: number;
      reason: string;
    }[]
  >([{ product_id: "", batch_id: "", qty: 1, reason: "" }]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Status Update Form State
  const [targetStatus, setTargetStatus] = useState<PurchaseReturnStatus>("shipped");
  const [creditNoteRef, setCreditNoteRef] = useState<string>("");

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [returnsRes, posRes, batchesRes, supRes] = await Promise.all([
        apiClient.get<PurchaseReturn[]>("/purchase-returns").catch((err) => {
          if (err instanceof Error && err.message.toLowerCase().includes("two-factor")) {
            setError(err.message);
          }
          return [];
        }),
        apiClient.get<PurchaseOrderItemType[]>("/purchase-orders").catch(() => []),
        apiClient
          .get<StockBatchOption[] | { batches?: StockBatchOption[] }>("/stock/batches")
          .catch(() => []),
        apiClient.get<SupplierOption[]>("/suppliers").catch(() => []),
      ]);

      const loadedReturns = Array.isArray(returnsRes) ? returnsRes : [];
      const loadedPos = Array.isArray(posRes) ? posRes.filter((po) => po.status !== "draft") : [];
      const resolvedBatches = Array.isArray(batchesRes)
        ? batchesRes
        : (batchesRes as { batches?: StockBatchOption[] })?.batches || [];
      const loadedSuppliers = Array.isArray(supRes) ? supRes.filter((s) => s.is_active) : [];

      setReturns(loadedReturns);
      setPurchaseOrders(loadedPos);
      setBatches(resolvedBatches);
      setSuppliers(loadedSuppliers);

      if (prefillPoId) {
        const targetPO = loadedPos.find((p) => p.id === prefillPoId);
        if (targetPO) {
          setReturnPoId(targetPO.id);
          if (targetPO.items && targetPO.items.length > 0) {
            const matchingBatches = resolvedBatches.filter(
              (b) => b.product_id === targetPO.items[0].product_id,
            );
            setReturnLines([
              {
                product_id: targetPO.items[0].product_id,
                batch_id: matchingBatches.length > 0 ? matchingBatches[0].id : "",
                qty: 1,
                reason: "Quality defect / damaged",
              },
            ]);
          }
          setCreateModalOpen(true);
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load supplier returns.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    const handle2FAVerified = () => {
      setError(null);
      fetchData();
    };

    window.addEventListener("wareflow:2fa-verified", handle2FAVerified);
    return () => {
      window.removeEventListener("wareflow:2fa-verified", handle2FAVerified);
    };
  }, [prefillPoId]);

  // When PO selection changes in form, auto-fill first product & matching batch
  const handlePoSelection = (poId: string) => {
    setReturnPoId(poId);
    const selectedPo = purchaseOrders.find((p) => p.id === poId);
    if (selectedPo && selectedPo.items && selectedPo.items.length > 0) {
      const firstItem = selectedPo.items[0];
      const matchingBatches = batches.filter((b) => b.product_id === firstItem.product_id);
      setReturnLines([
        {
          product_id: firstItem.product_id,
          batch_id: matchingBatches.length > 0 ? matchingBatches[0].id : "",
          qty: 1,
          reason: "",
        },
      ]);
    }
  };

  // KPI Metrics Calculation
  const metrics = useMemo(() => {
    const totalRequests = returns.length;
    const totalUnitsReturned = returns.reduce((sum, r) => sum + (r.total_qty || 0), 0);
    const inTransit = returns.filter((r) => r.status === "shipped").length;
    const credited = returns.filter((r) => r.status === "credited").length;

    return {
      totalRequests,
      totalUnitsReturned,
      inTransit,
      credited,
    };
  }, [returns]);

  // Filtered Returns
  const filteredReturns = useMemo(() => {
    return returns.filter((ret) => {
      const matchesSearch =
        searchQuery === "" ||
        ret.po_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
        ret.supplier_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (ret.credit_note_ref &&
          ret.credit_note_ref.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (ret.items &&
          ret.items.some(
            (i) =>
              i.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              i.product_sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
              (i.batch_no && i.batch_no.toLowerCase().includes(searchQuery.toLowerCase())),
          ));

      const matchesStatus = statusFilter === "all" || ret.status === statusFilter;
      const matchesSupplier =
        selectedSupplierId === "all" || ret.supplier_id === selectedSupplierId;

      return matchesSearch && matchesStatus && matchesSupplier;
    });
  }, [returns, searchQuery, statusFilter, selectedSupplierId]);

  // Status Badge Renderer
  const renderStatusBadge = (status: PurchaseReturnStatus) => {
    switch (status) {
      case "requested":
        return (
          <GlassBadge variant="warning" className="gap-1 font-mono uppercase text-[10px]">
            <Clock className="w-3 h-3" />
            Requested
          </GlassBadge>
        );
      case "shipped":
        return (
          <GlassBadge variant="accent" className="gap-1 font-mono uppercase text-[10px]">
            <Truck className="w-3 h-3" />
            Shipped (RMA)
          </GlassBadge>
        );
      case "credited":
        return (
          <GlassBadge variant="success" className="gap-1 font-mono uppercase text-[10px]">
            <CheckCircle2 className="w-3 h-3" />
            Credited
          </GlassBadge>
        );
      default:
        return <GlassBadge variant="neutral">{status}</GlassBadge>;
    }
  };

  // Submit Create Return Request
  const handleCreateReturn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!returnPoId) {
      setError("Please select an original Purchase Order.");
      return;
    }

    for (let i = 0; i < returnLines.length; i++) {
      const line = returnLines[i];
      if (!line.product_id || !line.batch_id || line.qty <= 0) {
        setError(`Line #${i + 1}: Please select a valid product, batch, and return quantity > 0.`);
        return;
      }
      const targetBatch = batches.find((b) => b.id === line.batch_id);
      if (targetBatch && line.qty > targetBatch.quantity) {
        setError(
          `Line #${i + 1}: Return quantity (${line.qty}) exceeds available batch balance (${targetBatch.quantity}).`,
        );
        return;
      }
    }

    try {
      setIsSubmitting(true);
      setError(null);

      await apiClient.post("/purchase-returns", {
        purchase_order_id: returnPoId,
        reason: returnReason || "Supplier return request",
        items: returnLines.map((l) => ({
          product_id: l.product_id,
          batch_id: l.batch_id,
          qty: Number(l.qty),
          reason: l.reason || undefined,
        })),
      });

      setSuccess("Supplier return request created and stock deducted from inventory!");
      setCreateModalOpen(false);
      setReturnPoId("");
      setReturnReason("");
      setReturnLines([{ product_id: "", batch_id: "", qty: 1, reason: "" }]);
      fetchData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create return request.";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Status Update
  const handleStatusUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeReturn) return;

    if (targetStatus === "credited" && (!creditNoteRef || !creditNoteRef.trim())) {
      setError("Credit Note Reference is mandatory when marking a return as credited.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      await apiClient.patch(`/purchase-returns/${activeReturn.id}/status`, {
        status: targetStatus,
        credit_note_ref: targetStatus === "credited" ? creditNoteRef.trim() : undefined,
      });

      setSuccess(
        `Return ${activeReturn.id.slice(0, 8)} successfully updated to ${targetStatus.toUpperCase()}!`,
      );
      setStatusModalOpen(false);
      setActiveReturn(null);
      setCreditNoteRef("");
      fetchData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update return status.";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Table Columns
  const columns: DataTableColumn<PurchaseReturn>[] = [
    {
      key: "id",
      header: "RMA Reference",
      sortable: true,
      render: (row) => (
        <div>
          <span className="font-mono font-semibold text-slate-200 block text-xs">
            RMA-{row.id.slice(0, 8).toUpperCase()}
          </span>
          <span className="text-[11px] text-slate-400">
            {new Date(row.requested_at).toLocaleDateString("en-IN", {
              day: "numeric",
              month: "short",
              year: "numeric",
            })}
          </span>
        </div>
      ),
    },
    {
      key: "po_number",
      header: "Original PO",
      sortable: true,
      render: (row) => (
        <span className="font-mono text-xs font-medium text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
          {row.po_number}
        </span>
      ),
    },
    {
      key: "supplier_name",
      header: "Supplier",
      sortable: true,
      render: (row) => (
        <div>
          <span className="font-medium text-slate-200 block text-xs">{row.supplier_name}</span>
          <span className="text-[11px] text-slate-400">
            {row.items_count} {row.items_count === 1 ? "item" : "items"}
          </span>
        </div>
      ),
    },
    {
      key: "items",
      header: "Items & Batches",
      render: (row) => (
        <div className="space-y-1 max-w-xs">
          {row.items?.slice(0, 2).map((itm) => (
            <div
              key={itm.id}
              className="text-xs text-slate-300 flex items-center justify-between gap-2"
            >
              <span className="truncate">
                {itm.product_name} ({itm.product_sku})
              </span>
              <span className="font-mono text-[11px] text-amber-300 shrink-0">
                {itm.batch_no || "N/A"}
              </span>
            </div>
          ))}
          {row.items && row.items.length > 2 && (
            <span className="text-[10px] text-slate-400 italic">
              +{row.items.length - 2} more item(s)
            </span>
          )}
        </div>
      ),
    },
    {
      key: "total_qty",
      header: "Total Return Qty",
      sortable: true,
      render: (row) => (
        <span className="font-mono text-xs font-semibold text-rose-400">{row.total_qty} units</span>
      ),
    },
    {
      key: "credit_note_ref",
      header: "Credit Note Ref",
      render: (row) =>
        row.credit_note_ref ? (
          <span className="font-mono text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            {row.credit_note_ref}
          </span>
        ) : (
          <span className="text-slate-400 text-xs italic">Pending</span>
        ),
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      render: (row) => renderStatusBadge(row.status),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={() => {
              setActiveReturn(row);
              setDetailModalOpen(true);
            }}
            title="View Details"
          >
            <Eye className="w-3.5 h-3.5" />
          </GlassButton>

          {row.status === "requested" && (
            <GlassButton
              size="sm"
              variant="secondary"
              onClick={() => {
                setActiveReturn(row);
                setTargetStatus("shipped");
                setStatusModalOpen(true);
              }}
              className="gap-1 text-xs"
            >
              <Truck className="w-3.5 h-3.5 text-indigo-400" />
              Ship RMA
            </GlassButton>
          )}

          {row.status === "shipped" && (
            <GlassButton
              size="sm"
              variant="primary"
              onClick={() => {
                setActiveReturn(row);
                setTargetStatus("credited");
                setStatusModalOpen(true);
              }}
              className="gap-1 text-xs"
            >
              <ReceiptText className="w-3.5 h-3.5 text-emerald-300" />
              Mark Credited
            </GlassButton>
          )}
        </div>
      ),
    },
  ];

  return (
    <AppLayout>
      <ListViewTemplate
        title="Supplier Returns (RMA Out)"
        description="Process goods returned to suppliers, deduct returned batch stock, track outbound shipping, and log vendor credit notes."
        searchPlaceholder="Search RMA, PO, supplier, batch..."
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        primaryAction={
          <GlassButton
            variant="primary"
            onClick={() => setCreateModalOpen(true)}
            className="gap-2 shadow-lg shadow-indigo-500/20"
          >
            <Plus className="w-4 h-4" />
            Request Return (RMA)
          </GlassButton>
        }
        statsBar={
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
            <GlassCard className="p-4 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Undo2 className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Total Returns
                </p>
                <p className="text-2xl font-bold text-slate-100">{metrics.totalRequests}</p>
              </div>
            </GlassCard>

            <GlassCard className="p-4 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <Boxes className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Units Returned
                </p>
                <p className="text-2xl font-bold text-slate-100">{metrics.totalUnitsReturned}</p>
              </div>
            </GlassCard>

            <GlassCard className="p-4 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Truck className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Shipped in Transit
                </p>
                <p className="text-2xl font-bold text-slate-100">{metrics.inTransit}</p>
              </div>
            </GlassCard>

            <GlassCard className="p-4 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <ReceiptText className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Vendor Credited
                </p>
                <p className="text-2xl font-bold text-emerald-400">{metrics.credited}</p>
              </div>
            </GlassCard>
          </div>
        }
        filters={
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={selectedSupplierId}
              onChange={(e) => setSelectedSupplierId(e.target.value)}
              className="bg-slate-900 border border-white/10 text-xs text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Suppliers</option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>

            <div className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-white/5">
              {(["all", "requested", "shipped", "credited"] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 text-xs rounded-lg transition-all capitalize ${
                    statusFilter === st
                      ? "bg-indigo-600 text-white font-semibold shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {st === "all" ? "All" : st}
                </button>
              ))}
            </div>
          </div>
        }
      >
        {/* Alerts */}
        {error && (
          <div className="mb-4 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-rose-300 shadow-lg shadow-rose-950/20">
            <div className="flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
            <div className="flex items-center gap-2 self-end sm:self-auto">
              {error.toLowerCase().includes("two-factor") && (
                <GlassButton
                  size="sm"
                  variant="primary"
                  onClick={() => window.dispatchEvent(new CustomEvent("wareflow:2fa-required"))}
                  className="text-xs py-1 px-3 bg-gradient-to-r from-amber-500 to-indigo-600 border-amber-400/30 text-white font-medium"
                >
                  Verify 2FA Now
                </GlassButton>
              )}
              <button
                onClick={() => setError(null)}
                className="text-rose-400 hover:text-rose-200 px-1 py-0.5 rounded hover:bg-rose-500/20 transition-colors"
              >
                &times;
              </button>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-4 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between text-xs text-emerald-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{success}</span>
            </div>
            <button
              onClick={() => setSuccess(null)}
              className="text-emerald-400 hover:text-emerald-200"
            >
              &times;
            </button>
          </div>
        )}

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredReturns}
          keyExtractor={(item) => item.id}
          isLoading={loading}
          emptyTitle="No supplier returns match your criteria"
          emptyDescription="Supplier return requests and outbound RMAs will appear here."
        />

        {/* MODAL 1: Create Return Request */}
        <GlassModal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          title="Create Supplier Return Request (RMA Out)"
          description="Stock is physically deducted from the chosen batch immediately upon submission."
          maxWidth="2xl"
        >
          <form onSubmit={handleCreateReturn} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">
                Original Purchase Order <span className="text-rose-400">*</span>
              </label>
              <select
                value={returnPoId}
                onChange={(e) => handlePoSelection(e.target.value)}
                required
                className="w-full bg-slate-950 border border-white/10 text-xs text-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:border-indigo-500"
              >
                <option value="">Select a Purchase Order...</option>
                {purchaseOrders.map((po) => (
                  <option key={po.id} value={po.id}>
                    {po.po_number} — {po.supplier_name} ({po.status.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">
                Overall Return Reason / RMA Details
              </label>
              <GlassInput
                placeholder="e.g. Moisture contamination, batch packaging defect"
                value={returnReason}
                onChange={(e) => setReturnReason(e.target.value)}
              />
            </div>

            {/* Line Items Builder */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Returned Items & Batches
                </h4>
                <GlassButton
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() =>
                    setReturnLines([
                      ...returnLines,
                      { product_id: "", batch_id: "", qty: 1, reason: "" },
                    ])
                  }
                  className="gap-1 text-xs"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add Line
                </GlassButton>
              </div>

              {returnLines.map((line, idx) => {
                const selectedPo = purchaseOrders.find((p) => p.id === returnPoId);
                const poProducts = selectedPo?.items || [];
                const matchingBatches = batches.filter((b) => b.product_id === line.product_id);
                const chosenBatch = batches.find((b) => b.id === line.batch_id);

                return (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-900/60 border border-white/5 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-indigo-400">Line #{idx + 1}</span>
                      {returnLines.length > 1 && (
                        <button
                          type="button"
                          onClick={() => setReturnLines(returnLines.filter((_, i) => i !== idx))}
                          className="text-rose-400 hover:text-rose-300 text-xs"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      {/* Product Selector */}
                      <div className="space-y-1">
                        <label className="text-[11px] text-slate-400">Product</label>
                        <select
                          value={line.product_id}
                          onChange={(e) => {
                            const newProdId = e.target.value;
                            const newBatches = batches.filter((b) => b.product_id === newProdId);
                            const updated = [...returnLines];
                            updated[idx].product_id = newProdId;
                            updated[idx].batch_id = newBatches.length > 0 ? newBatches[0].id : "";
                            setReturnLines(updated);
                          }}
                          required
                          className="w-full bg-slate-950 border border-white/10 text-xs text-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="">Select Product...</option>
                          {poProducts.map((itm) => (
                            <option key={itm.product_id} value={itm.product_id}>
                              {itm.product_name} ({itm.product_sku})
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Batch Selector */}
                      <div className="space-y-1">
                        <label className="text-[11px] text-slate-400">
                          Stock Batch{" "}
                          {chosenBatch && (
                            <span className="text-amber-400 font-mono text-[10px]">
                              (On-Hand: {chosenBatch.quantity})
                            </span>
                          )}
                        </label>
                        <select
                          value={line.batch_id}
                          onChange={(e) => {
                            const updated = [...returnLines];
                            updated[idx].batch_id = e.target.value;
                            setReturnLines(updated);
                          }}
                          required
                          className="w-full bg-slate-950 border border-white/10 text-xs text-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="">Select Batch...</option>
                          {matchingBatches.map((b) => (
                            <option key={b.id} value={b.id}>
                              {b.batch_no} — Avail: {b.quantity}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Quantity */}
                      <div className="space-y-1">
                        <label className="text-[11px] text-slate-400">Return Qty</label>
                        <input
                          type="number"
                          min="0.1"
                          step="any"
                          max={chosenBatch ? chosenBatch.quantity : undefined}
                          value={line.qty}
                          onChange={(e) => {
                            const updated = [...returnLines];
                            updated[idx].qty = parseFloat(e.target.value) || 0;
                            setReturnLines(updated);
                          }}
                          required
                          className="w-full bg-slate-950 border border-white/10 text-xs text-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[11px] text-slate-400">Line Defect Reason</label>
                      <input
                        type="text"
                        placeholder="e.g. Broken seal, damaged packaging"
                        value={line.reason}
                        onChange={(e) => {
                          const updated = [...returnLines];
                          updated[idx].reason = e.target.value;
                          setReturnLines(updated);
                        }}
                        className="w-full bg-slate-950 border border-white/10 text-xs text-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
              <GlassButton
                type="button"
                variant="ghost"
                onClick={() => setCreateModalOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </GlassButton>
              <GlassButton
                type="submit"
                variant="primary"
                disabled={isSubmitting}
                className="gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                {isSubmitting ? "Submitting..." : "Confirm & Deduct Stock"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>

        {/* MODAL 2: Lifecycle Transition (shipped / credited) */}
        <GlassModal
          isOpen={statusModalOpen}
          onClose={() => setStatusModalOpen(false)}
          title={`Update RMA Status — ${activeReturn?.id.slice(0, 8).toUpperCase()}`}
          description={`Transitioning status to ${targetStatus.toUpperCase()}`}
          maxWidth="md"
        >
          <form onSubmit={handleStatusUpdate} className="space-y-4">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Supplier:</span>
                <span className="font-semibold text-slate-200">{activeReturn?.supplier_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Original PO:</span>
                <span className="font-mono text-indigo-300">{activeReturn?.po_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Total Units:</span>
                <span className="font-semibold text-rose-400">{activeReturn?.total_qty} units</span>
              </div>
            </div>

            {targetStatus === "credited" && (
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">
                  Supplier Credit Note Reference <span className="text-rose-400">*</span>
                </label>
                <GlassInput
                  placeholder="e.g. CRN-2026-0891"
                  value={creditNoteRef}
                  onChange={(e) => setCreditNoteRef(e.target.value)}
                  required
                />
                <p className="text-[11px] text-slate-400">
                  Enter the credit note invoice number issued by {activeReturn?.supplier_name}.
                </p>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
              <GlassButton
                type="button"
                variant="ghost"
                onClick={() => setStatusModalOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </GlassButton>
              <GlassButton
                type="submit"
                variant="primary"
                disabled={isSubmitting}
                className="gap-1.5"
              >
                <ArrowRight className="w-4 h-4" />
                {isSubmitting ? "Updating..." : `Confirm ${targetStatus.toUpperCase()}`}
              </GlassButton>
            </div>
          </form>
        </GlassModal>

        {/* MODAL 3: Purchase Return Details */}
        <GlassModal
          isOpen={detailModalOpen}
          onClose={() => setDetailModalOpen(false)}
          title={`Supplier Return RMA-${activeReturn?.id.slice(0, 8).toUpperCase()}`}
          description={`Issued against ${activeReturn?.po_number} to ${activeReturn?.supplier_name}`}
          maxWidth="xl"
        >
          {activeReturn && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-white/5 text-xs">
                <div>
                  <span className="text-slate-400 block">Status</span>
                  <div className="mt-1">{renderStatusBadge(activeReturn.status)}</div>
                </div>
                <div>
                  <span className="text-slate-400 block">Date Requested</span>
                  <span className="font-semibold text-slate-200 mt-1 block">
                    {new Date(activeReturn.requested_at).toLocaleDateString()}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Total Qty</span>
                  <span className="font-semibold text-rose-400 font-mono mt-1 block">
                    {activeReturn.total_qty} units
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Credit Note</span>
                  <span className="font-mono text-emerald-400 mt-1 block">
                    {activeReturn.credit_note_ref || "Pending"}
                  </span>
                </div>
              </div>

              {activeReturn.reason && (
                <div className="p-3 rounded-xl bg-slate-900/40 border border-white/5 text-xs">
                  <span className="text-slate-400 block mb-1">Return Reason:</span>
                  <p className="text-slate-200">{activeReturn.reason}</p>
                </div>
              )}

              <div>
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Returned Lines Breakdown
                </h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {activeReturn.items?.map((item) => (
                    <div
                      key={item.id}
                      className="p-3 rounded-xl bg-slate-900/40 border border-white/5 flex items-center justify-between text-xs"
                    >
                      <div>
                        <p className="font-semibold text-slate-200">{item.product_name}</p>
                        <p className="text-slate-400 font-mono">
                          {item.product_sku} &bull; Batch: {item.batch_no || "N/A"}
                        </p>
                        {item.reason && (
                          <p className="text-slate-400 italic text-[11px] mt-0.5">
                            Note: {item.reason}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-rose-400 font-mono">{item.qty} units</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end pt-3">
                <GlassButton variant="ghost" onClick={() => setDetailModalOpen(false)}>
                  Close
                </GlassButton>
              </div>
            </div>
          )}
        </GlassModal>
      </ListViewTemplate>
    </AppLayout>
  );
}

export default function PurchaseReturnsPage() {
  return (
    <Suspense
      fallback={
        <AppLayout>
          <div className="p-8 text-center text-slate-400">Loading Supplier Returns...</div>
        </AppLayout>
      }
    >
      <PurchaseReturnsContent />
    </Suspense>
  );
}
