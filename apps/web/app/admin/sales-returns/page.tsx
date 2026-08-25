"use client";

import React, { useState, useEffect, useMemo } from "react";
import AppLayout from "@/components/AppLayout";
import { ListViewTemplate } from "@/components/templates/ListViewTemplate";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { apiClient } from "@/lib/api-client";

import {
  RotateCcw,
  Clock,
  CheckCircle2,
  XCircle,
  Plus,
  Package,
  AlertOctagon,
  Eye,
  ShieldCheck,
  Ban,
  FileText,
} from "lucide-react";

export interface SalesReturnItem {
  id: string;
  return_id: string;
  product_id: string;
  product_name?: string | null;
  product_sku?: string | null;
  qty: number;
  batch_id?: string | null;
  batch_no?: string | null;
  condition: "resellable" | "damaged";
  unit_price: number;
  refund_amount: number;
}

export interface SalesReturn {
  id: string;
  sales_order_id: string;
  so_number?: string | null;
  retailer_id: string;
  retailer_name?: string | null;
  status: "requested" | "approved" | "rejected" | "completed";
  reason?: string | null;
  credit_adjustment_amount: number;
  requested_at: string;
  items: SalesReturnItem[];
}

export interface SalesOrderOption {
  id: string;
  so_number: string;
  retailer_id: string;
  retailer_name?: string;
  status: string;
  items: {
    id: string;
    product_id: string;
    product_name?: string;
    product_sku?: string;
    qty: number;
    unit_price: number;
    batch_id?: string;
  }[];
}

const MOCK_RETURNS: SalesReturn[] = [
  {
    id: "ret-rma-001",
    sales_order_id: "so-2026-001",
    so_number: "SO-202608-0001",
    retailer_id: "ret-1",
    retailer_name: "Apex Hypermarkets Ltd",
    status: "approved",
    reason: "Wrong case size delivered",
    credit_adjustment_amount: 2700,
    requested_at: new Date(Date.now() - 86400000).toISOString(),
    items: [
      {
        id: "ri-1",
        return_id: "ret-rma-001",
        product_id: "prod-1",
        product_name: "Royal Basmati Rice 5kg",
        product_sku: "RIC-BAS-001",
        qty: 6,
        batch_no: "B-2026-001",
        condition: "resellable",
        unit_price: 450,
        refund_amount: 2700,
      },
    ],
  },
  {
    id: "ret-rma-002",
    sales_order_id: "so-2026-002",
    so_number: "SO-202608-0002",
    retailer_id: "ret-2",
    retailer_name: "Metro Kirana Mart",
    status: "requested",
    reason: "Damaged packaging in transit",
    credit_adjustment_amount: 1500,
    requested_at: new Date().toISOString(),
    items: [
      {
        id: "ri-2",
        return_id: "ret-rma-002",
        product_id: "prod-2",
        product_name: "Organic Whole Wheat 10kg",
        product_sku: "WHT-ORG-010",
        qty: 3,
        batch_no: "B-2026-002",
        condition: "damaged",
        unit_price: 500,
        refund_amount: 1500,
      },
    ],
  },
];

export default function SalesReturnsPage() {
  const [returns, setReturns] = useState<SalesReturn[]>([]);
  const [orders, setOrders] = useState<SalesOrderOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Modal States
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [selectedReturn, setSelectedReturn] = useState<SalesReturn | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Create Form State
  const [formOrderId, setFormOrderId] = useState("");
  const [formReason, setFormReason] = useState("");
  const [formLines, setFormLines] = useState<
    {
      product_id: string;
      batch_id: string;
      qty: number;
      condition: "resellable" | "damaged";
      reason: string;
    }[]
  >([]);

  const fetchReturns = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<SalesReturn[]>("/sales-returns");
      if (res && Array.isArray(res)) {
        setReturns(res);
      } else {
        setReturns(MOCK_RETURNS);
      }
    } catch {
      setReturns(MOCK_RETURNS);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const loadInitialData = async () => {
      try {
        setLoading(true);
        const [returnsRes, ordersRes] = await Promise.allSettled([
          apiClient.get<SalesReturn[]>("/sales-returns"),
          apiClient.get<SalesOrderOption[]>("/sales-orders"),
        ]);
        if (!isMounted) return;

        if (returnsRes.status === "fulfilled" && Array.isArray(returnsRes.value)) {
          setReturns(returnsRes.value);
        } else {
          setReturns(MOCK_RETURNS);
        }

        if (ordersRes.status === "fulfilled" && Array.isArray(ordersRes.value)) {
          setOrders(
            ordersRes.value.filter((o) =>
              ["confirmed", "packed", "shipped", "delivered"].includes(o.status),
            ),
          );
        }
      } catch {
        if (isMounted) setReturns(MOCK_RETURNS);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadInitialData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Filtered Returns
  const filteredReturns = useMemo(() => {
    return returns.filter((r) => {
      const matchesSearch =
        searchQuery === "" ||
        r.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (r.so_number && r.so_number.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (r.retailer_name && r.retailer_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (r.reason && r.reason.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesStatus = statusFilter === "all" || r.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [returns, searchQuery, statusFilter]);

  // Metrics
  const metrics = useMemo(() => {
    const total = returns.length;
    const requested = returns.filter((r) => r.status === "requested").length;
    let resellableUnits = 0;
    let damagedUnits = 0;
    let totalCredit = 0;

    returns.forEach((r) => {
      totalCredit += r.credit_adjustment_amount || 0;
      r.items.forEach((it) => {
        if (it.condition === "resellable") {
          resellableUnits += it.qty;
        } else {
          damagedUnits += it.qty;
        }
      });
    });

    return { total, requested, resellableUnits, damagedUnits, totalCredit };
  }, [returns]);

  // Selected Order for Create Form
  const selectedOrderForForm = useMemo(() => {
    return orders.find((o) => o.id === formOrderId);
  }, [orders, formOrderId]);

  const handleOrderSelectionChange = (orderId: string) => {
    setFormOrderId(orderId);
    const targetOrder = orders.find((o) => o.id === orderId);
    if (targetOrder && targetOrder.items.length > 0) {
      setFormLines(
        targetOrder.items.map((it) => ({
          product_id: it.product_id,
          batch_id: it.batch_id || "",
          qty: 1,
          condition: "resellable",
          reason: "",
        })),
      );
    } else {
      setFormLines([]);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formOrderId) {
      setErrorMessage("Please select a sales order.");
      return;
    }
    if (formLines.length === 0) {
      setErrorMessage("Please add at least one item to return.");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMessage(null);

      const payload = {
        sales_order_id: formOrderId,
        reason: formReason || null,
        items: formLines.map((l) => ({
          product_id: l.product_id,
          batch_id: l.batch_id || null,
          qty: Number(l.qty),
          condition: l.condition,
          reason: l.reason || null,
        })),
      };

      await apiClient.post("/sales-returns", payload);
      await fetchReturns();
      setIsCreateOpen(false);
      setFormOrderId("");
      setFormReason("");
      setFormLines([]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create return request.";
      setErrorMessage(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async (returnId: string) => {
    try {
      setSubmitting(true);
      setErrorMessage(null);
      await apiClient.patch(`/sales-returns/${returnId}/approve`, {});
      await fetchReturns();
      if (selectedReturn && selectedReturn.id === returnId) {
        setSelectedReturn((prev) => (prev ? { ...prev, status: "approved" } : null));
      }
      setIsDetailOpen(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to approve return.";
      setErrorMessage(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async (returnId: string) => {
    try {
      setSubmitting(true);
      setErrorMessage(null);
      await apiClient.patch(`/sales-returns/${returnId}/reject`, {
        status: "rejected",
        rejection_reason: "Rejected by inventory manager",
      });
      await fetchReturns();
      if (selectedReturn && selectedReturn.id === returnId) {
        setSelectedReturn((prev) => (prev ? { ...prev, status: "rejected" } : null));
      }
      setIsDetailOpen(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to reject return.";
      setErrorMessage(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const columns: DataTableColumn<SalesReturn>[] = [
    {
      key: "id",
      header: "RMA ID",
      render: (ret) => (
        <div>
          <span className="font-mono text-xs font-semibold text-[var(--accent)]">
            {ret.id.substring(0, 12)}...
          </span>
          <div className="text-[10px] text-[var(--text-muted)]">
            {new Date(ret.requested_at).toLocaleDateString("en-IN", {
              month: "short",
              day: "numeric",
              year: "numeric",
            })}
          </div>
        </div>
      ),
    },
    {
      key: "sales_order_id",
      header: "Sales Order",
      render: (ret) => (
        <div>
          <div className="font-semibold text-xs text-[var(--text)] flex items-center gap-1">
            <FileText className="w-3.5 h-3.5 text-purple-400" />
            {ret.so_number || ret.sales_order_id.substring(0, 10)}
          </div>
          <div className="text-[11px] text-[var(--text-muted)]">
            {ret.retailer_name || "Retailer"}
          </div>
        </div>
      ),
    },
    {
      key: "items",
      header: "Condition & Items",
      render: (ret) => {
        const resellableCount = ret.items.filter((i) => i.condition === "resellable").length;
        const damagedCount = ret.items.filter((i) => i.condition === "damaged").length;

        return (
          <div className="flex flex-wrap items-center gap-1.5">
            {resellableCount > 0 && (
              <GlassBadge variant="success">
                <ShieldCheck className="w-3 h-3 mr-1" /> {resellableCount} Resellable
              </GlassBadge>
            )}
            {damagedCount > 0 && (
              <GlassBadge variant="error">
                <AlertOctagon className="w-3 h-3 mr-1" /> {damagedCount} Damaged
              </GlassBadge>
            )}
          </div>
        );
      },
    },
    {
      key: "credit_adjustment_amount",
      header: "Credit Adjustment",
      align: "right",
      render: (ret) => (
        <span className="font-mono font-bold text-xs text-purple-300">
          ₹{Number(ret.credit_adjustment_amount || 0).toLocaleString("en-IN")}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (ret) => {
        switch (ret.status) {
          case "requested":
            return (
              <GlassBadge variant="warning">
                <Clock className="w-3 h-3 mr-1" /> Requested
              </GlassBadge>
            );
          case "approved":
            return (
              <GlassBadge variant="success">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Approved (Restocked)
              </GlassBadge>
            );
          case "rejected":
            return (
              <GlassBadge variant="error">
                <XCircle className="w-3 h-3 mr-1" /> Rejected
              </GlassBadge>
            );
          case "completed":
            return (
              <GlassBadge variant="accent">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Completed
              </GlassBadge>
            );
          default:
            return <GlassBadge variant="neutral">{ret.status}</GlassBadge>;
        }
      },
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (ret) => (
        <GlassButton
          variant="secondary"
          size="sm"
          onClick={() => {
            setSelectedReturn(ret);
            setIsDetailOpen(true);
          }}
        >
          <Eye className="w-3.5 h-3.5 mr-1" /> Details
        </GlassButton>
      ),
    },
  ];

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard className="p-4 flex items-center justify-between border-purple-500/20">
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)]">Total RMA Returns</p>
              <h3 className="text-2xl font-bold text-[var(--text)] mt-1">{metrics.total}</h3>
              <p className="text-[11px] text-purple-400 mt-0.5">Inbound Retailer Returns</p>
            </div>
            <div className="p-3 rounded-2xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <RotateCcw className="w-6 h-6" />
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center justify-between border-amber-500/20">
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)]">Pending Approvals</p>
              <h3 className="text-2xl font-bold text-amber-300 mt-1">{metrics.requested}</h3>
              <p className="text-[11px] text-[var(--text-muted)] mt-0.5">Awaiting inspection</p>
            </div>
            <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Clock className="w-6 h-6" />
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center justify-between border-emerald-500/20">
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)]">Resellable Restocked</p>
              <h3 className="text-2xl font-bold text-emerald-400 mt-1">
                {metrics.resellableUnits}
              </h3>
              <p className="text-[11px] text-emerald-400/80 mt-0.5">Added to stock batches</p>
            </div>
            <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center justify-between border-red-500/20">
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)]">Damaged Write-offs</p>
              <h3 className="text-2xl font-bold text-red-400 mt-1">{metrics.damagedUnits}</h3>
              <p className="text-[11px] text-red-400/80 mt-0.5">Excluded from sellable stock</p>
            </div>
            <div className="p-3 rounded-2xl bg-red-500/10 text-red-400 border border-red-500/20">
              <AlertOctagon className="w-6 h-6" />
            </div>
          </GlassCard>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {["all", "requested", "approved", "rejected"].map((tab) => (
            <button
              key={tab}
              onClick={() => setStatusFilter(tab)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                statusFilter === tab
                  ? "bg-purple-600/30 text-purple-200 border border-purple-500/40 shadow-sm"
                  : "bg-[var(--surface)] text-[var(--text-muted)] hover:text-[var(--text)] border border-[var(--glass-border)]"
              }`}
            >
              {tab === "all" ? "All Returns" : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* List View Template */}
        <ListViewTemplate
          title="Retailer Returns (RMA In)"
          description="Condition-based return management: resellable stock restocks batches via RETURN_IN; damaged stock is tracked for loss/credit adjustment."
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          primaryAction={
            <GlassButton
              variant="primary"
              onClick={() => {
                setErrorMessage(null);
                setIsCreateOpen(true);
              }}
            >
              <Plus className="w-4 h-4 mr-1.5" /> Request RMA Return
            </GlassButton>
          }
        >
          <DataTable
            data={filteredReturns}
            columns={columns}
            keyExtractor={(ret) => ret.id}
            isLoading={loading}
            emptyTitle="No retailer return records found."
            emptyDescription="When retail partners submit return requests, they will appear here for inspection."
          />
        </ListViewTemplate>

        {/* Create RMA Return Modal */}
        <GlassModal
          isOpen={isCreateOpen}
          onClose={() => setIsCreateOpen(false)}
          title="Request Inbound Retailer Return (RMA In)"
        >
          <form onSubmit={handleCreateSubmit} className="space-y-4">
            {errorMessage && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
                <AlertOctagon className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div className="space-y-1">
              <label
                htmlFor="so-select"
                className="block text-xs font-medium text-[var(--text-muted)]"
              >
                Select Sales Order *
              </label>
              <select
                id="so-select"
                value={formOrderId}
                onChange={(e) => handleOrderSelectionChange(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
              >
                <option value="">-- Choose Fulfilled Sales Order --</option>
                {orders.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.so_number} — {o.retailer_name || "Retailer"} ({o.status.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label
                htmlFor="rma-reason"
                className="block text-xs font-medium text-[var(--text-muted)]"
              >
                Reason for Return
              </label>
              <textarea
                id="rma-reason"
                value={formReason}
                onChange={(e) => setFormReason(e.target.value)}
                rows={2}
                placeholder="e.g. Retailer overstocked, wrong variant, transit damaged..."
                className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
              />
            </div>

            {/* Line Items Return Builder */}
            {formLines.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-[var(--glass-border)]">
                <h4 className="text-xs font-bold text-[var(--text)] flex items-center gap-1.5">
                  <Package className="w-3.5 h-3.5 text-purple-400" /> Return Items & Condition
                  Assessment
                </h4>

                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {formLines.map((line, idx) => {
                    const originalItem = selectedOrderForForm?.items.find(
                      (it) => it.product_id === line.product_id,
                    );

                    return (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)] space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-[var(--text)]">
                            {originalItem?.product_name || line.product_id}
                          </span>
                          <span className="text-[11px] text-[var(--text-muted)] font-mono">
                            Max Sold: {originalItem?.qty || 1} units
                          </span>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          <div>
                            <label className="block text-[10px] text-[var(--text-muted)] mb-1">
                              Return Quantity
                            </label>
                            <input
                              type="number"
                              min="1"
                              max={originalItem?.qty || 100}
                              value={line.qty}
                              onChange={(e) => {
                                const val = Number(e.target.value);
                                setFormLines((prev) =>
                                  prev.map((l, i) => (i === idx ? { ...l, qty: val } : l)),
                                );
                              }}
                              className="w-full px-2.5 py-1.5 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] font-mono"
                            />
                          </div>

                          <div>
                            <label className="block text-[10px] text-[var(--text-muted)] mb-1">
                              Condition Assessment *
                            </label>
                            <select
                              value={line.condition}
                              onChange={(e) => {
                                const cond = e.target.value as "resellable" | "damaged";
                                setFormLines((prev) =>
                                  prev.map((l, i) => (i === idx ? { ...l, condition: cond } : l)),
                                );
                              }}
                              className="w-full px-2.5 py-1.5 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)]"
                            >
                              <option value="resellable">Resellable (Restocks Stock Batch)</option>
                              <option value="damaged">Damaged (Loss Write-Off)</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-4 border-t border-[var(--glass-border)]">
              <GlassButton
                type="button"
                variant="ghost"
                onClick={() => setIsCreateOpen(false)}
                disabled={submitting}
              >
                Cancel
              </GlassButton>
              <GlassButton type="submit" variant="primary" disabled={submitting}>
                {submitting ? "Submitting..." : "Create RMA Return"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>

        {/* Return Detail Modal */}
        <GlassModal
          isOpen={isDetailOpen}
          onClose={() => setIsDetailOpen(false)}
          title="Sales Return Inspection (RMA In)"
        >
          {selectedReturn && (
            <div className="space-y-4">
              {errorMessage && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
                  <AlertOctagon className="w-4 h-4 flex-shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Summary Header */}
              <div className="p-4 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-sm text-[var(--text)]">
                      {selectedReturn.retailer_name || "Retailer"}
                    </h3>
                    <p className="text-xs text-purple-400 font-mono">
                      Sales Order: {selectedReturn.so_number || selectedReturn.sales_order_id}
                    </p>
                  </div>
                  <div>
                    {selectedReturn.status === "requested" && (
                      <GlassBadge variant="warning">
                        <Clock className="w-3 h-3 mr-1" /> Requested
                      </GlassBadge>
                    )}
                    {selectedReturn.status === "approved" && (
                      <GlassBadge variant="success">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> Approved & Restocked
                      </GlassBadge>
                    )}
                    {selectedReturn.status === "rejected" && (
                      <GlassBadge variant="error">
                        <XCircle className="w-3 h-3 mr-1" /> Rejected
                      </GlassBadge>
                    )}
                  </div>
                </div>

                {selectedReturn.reason && (
                  <p className="text-xs text-[var(--text-muted)] pt-1 border-t border-[var(--glass-border)]">
                    <span className="font-semibold text-[var(--text)]">Reason:</span>{" "}
                    {selectedReturn.reason}
                  </p>
                )}
              </div>

              {/* Line Items Table */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-[var(--text)]">Returned Items Breakdown</h4>
                <div className="rounded-xl border border-[var(--glass-border)] overflow-hidden">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-[var(--surface-hover)] text-[var(--text-muted)] border-b border-[var(--glass-border)]">
                      <tr>
                        <th className="p-2.5">Product</th>
                        <th className="p-2.5">Condition</th>
                        <th className="p-2.5 text-right">Qty</th>
                        <th className="p-2.5 text-right">Unit Price</th>
                        <th className="p-2.5 text-right">Refund Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--glass-border)]">
                      {selectedReturn.items.map((it) => (
                        <tr key={it.id} className="hover:bg-[var(--surface-hover)]">
                          <td className="p-2.5">
                            <div className="font-medium text-[var(--text)]">
                              {it.product_name || it.product_id}
                            </div>
                            {it.product_sku && (
                              <div className="text-[10px] text-[var(--text-muted)] font-mono">
                                {it.product_sku}
                              </div>
                            )}
                          </td>
                          <td className="p-2.5">
                            {it.condition === "resellable" ? (
                              <GlassBadge variant="success">
                                <ShieldCheck className="w-3 h-3 mr-1" /> Resellable
                              </GlassBadge>
                            ) : (
                              <GlassBadge variant="error">
                                <AlertOctagon className="w-3 h-3 mr-1" /> Damaged
                              </GlassBadge>
                            )}
                          </td>
                          <td className="p-2.5 text-right font-mono font-medium">{it.qty}</td>
                          <td className="p-2.5 text-right font-mono text-[var(--text-muted)]">
                            ₹{it.unit_price}
                          </td>
                          <td className="p-2.5 text-right font-mono font-bold text-purple-300">
                            ₹{it.refund_amount}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Total Credit Adjustment Banner */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs">
                <span className="font-semibold text-[var(--text)]">
                  Total Estimated Credit Adjustment:
                </span>
                <span className="font-mono text-base font-bold text-purple-300">
                  ₹{Number(selectedReturn.credit_adjustment_amount || 0).toLocaleString("en-IN")}
                </span>
              </div>

              {/* Action Bar */}
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[var(--glass-border)]">
                <GlassButton type="button" variant="ghost" onClick={() => setIsDetailOpen(false)}>
                  Close
                </GlassButton>

                {selectedReturn.status === "requested" && (
                  <>
                    <GlassButton
                      type="button"
                      variant="destructive"
                      size="sm"
                      disabled={submitting}
                      onClick={() => handleReject(selectedReturn.id)}
                    >
                      <Ban className="w-3.5 h-3.5 mr-1" /> Reject Return
                    </GlassButton>

                    <GlassButton
                      type="button"
                      variant="primary"
                      size="sm"
                      disabled={submitting}
                      onClick={() => handleApprove(selectedReturn.id)}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Approve (Restock Resellable)
                    </GlassButton>
                  </>
                )}
              </div>
            </div>
          )}
        </GlassModal>
      </div>
    </AppLayout>
  );
}
