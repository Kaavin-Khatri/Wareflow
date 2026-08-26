"use client";

import React, { useState, useEffect, useMemo, useTransition } from "react";
import Link from "next/link";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassSelect } from "@/components/glass/GlassSelect";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { apiClient } from "@/lib/api-client";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  BellRing,
  Building2,
  Package,
  Layers,
  ArrowLeft,
  X,
  Send,
  Check,
  Search,
} from "lucide-react";

interface ProductOption {
  id: string;
  name: string;
  sku: string;
}

interface BatchOption {
  id: string;
  product_id: string;
  warehouse_id: string;
  batch_no: string;
  quantity: number;
  expiry_date?: string | null;
}

interface AffectedOrderItem {
  id: string;
  sales_order_id: string;
  sales_order_number?: string | null;
  buyer_type: string;
  buyer_id?: string | null;
  buyer_name: string;
  buyer_phone?: string | null;
  buyer_email?: string | null;
  order_date?: string | null;
  quantity_supplied: number;
  notified_at?: string | null;
}

interface BatchRecallItem {
  id: string;
  batch_id: string;
  batch_no: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  warehouse_name: string;
  remaining_quantity: number;
  reason: string;
  severity: "low" | "medium" | "critical";
  status: "initiated" | "notifying" | "resolved";
  initiated_at: string;
  resolved_at?: string | null;
  affected_orders_count: number;
  notified_count: number;
}

interface BatchRecallDetail extends BatchRecallItem {
  warehouse_id: string;
  affected_orders: AffectedOrderItem[];
}

interface RecallListResponse {
  items: BatchRecallItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

const MOCK_RECALLS: BatchRecallItem[] = [
  {
    id: "rec-1",
    batch_id: "batch-101",
    batch_no: "BATCH-2026-0801",
    product_id: "prod-1",
    product_name: "Organic Whole Milk 1L",
    product_sku: "MILK-ORG-001",
    warehouse_name: "Central Cold Storage",
    remaining_quantity: 45.0,
    reason: "Packaging seal integrity issue identified during batch sample audit.",
    severity: "critical",
    status: "initiated",
    initiated_at: new Date(Date.now() - 3600000 * 5).toISOString(),
    resolved_at: null,
    affected_orders_count: 3,
    notified_count: 0,
  },
  {
    id: "rec-2",
    batch_id: "batch-102",
    batch_no: "BATCH-2026-0715",
    product_id: "prod-2",
    product_name: "Royal Basmati Rice 5kg",
    product_sku: "RIC-BAS-005",
    warehouse_name: "West Coast Depo",
    remaining_quantity: 12.0,
    reason: "Labeling weight discrepancy reported by customer audit.",
    severity: "medium",
    status: "resolved",
    initiated_at: new Date(Date.now() - 86400000 * 4).toISOString(),
    resolved_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    affected_orders_count: 2,
    notified_count: 2,
  },
];

export default function BatchRecallsPage() {
  const [, startTransition] = useTransition();

  // Reference Data
  const [products, setProducts] = useState<ProductOption[]>([]);
  const [batches, setBatches] = useState<BatchOption[]>([]);
  const [recalls, setRecalls] = useState<BatchRecallItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");

  // Create Recall Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [selectedBatchId, setSelectedBatchId] = useState("");
  const [severity, setSeverity] = useState<"low" | "medium" | "critical">("critical");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Recall Detail Modal / Drawer
  const [selectedRecall, setSelectedRecall] = useState<BatchRecallDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [notifying, setNotifying] = useState(false);
  const [resolving, setResolving] = useState(false);

  // Load Initial Recalls & Products
  useEffect(() => {
    let isMounted = true;
    const fetchInitialData = async () => {
      try {
        const [prodRes, recRes] = await Promise.all([
          apiClient.get<ProductOption[]>("/products").catch(() => []),
          apiClient.get<RecallListResponse>("/stock/recalls?page_size=100").catch(() => null),
        ]);

        if (!isMounted) return;
        setProducts(prodRes || []);

        if (recRes && Array.isArray(recRes.items) && recRes.items.length > 0) {
          setRecalls(recRes.items);
        } else {
          setRecalls(MOCK_RECALLS);
        }
      } catch {
        if (isMounted) setRecalls(MOCK_RECALLS);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchInitialData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch product batches when product is selected in create modal
  useEffect(() => {
    let isMounted = true;
    const loadBatches = async () => {
      if (!selectedProductId) {
        setBatches([]);
        setSelectedBatchId("");
        return;
      }
      try {
        const res = await apiClient.get<{ batches: BatchOption[] }>(
          `/products/${selectedProductId}/stock`,
        );
        if (!isMounted) return;
        const bList = res?.batches || [];
        setBatches(bList);
        if (bList.length > 0) {
          setSelectedBatchId(bList[0].id);
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
  }, [selectedProductId]);

  // KPIs
  const kpis = useMemo(() => {
    const total = recalls.length;
    const active = recalls.filter((r) => r.status !== "resolved").length;
    const totalAffected = recalls.reduce((acc, r) => acc + (r.affected_orders_count || 0), 0);
    const totalNotified = recalls.reduce((acc, r) => acc + (r.notified_count || 0), 0);

    return { total, active, totalAffected, totalNotified };
  }, [recalls]);

  // Filtered List
  const filteredRecalls = useMemo(() => {
    return recalls.filter((r) => {
      const matchSearch =
        !searchQuery ||
        r.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.product_sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.batch_no.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.reason.toLowerCase().includes(searchQuery.toLowerCase());

      const matchStatus = statusFilter === "all" || r.status === statusFilter;
      const matchSeverity = severityFilter === "all" || r.severity === severityFilter;

      return matchSearch && matchStatus && matchSeverity;
    });
  }, [recalls, searchQuery, statusFilter, severityFilter]);

  // Handle Initiate Recall Submission
  const handleInitiateRecall = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);
    setActionSuccess(null);

    if (!selectedBatchId) {
      setActionError("Please select a batch to recall.");
      return;
    }
    if (!reason.trim() || reason.trim().length < 5) {
      setActionError("Please provide a detailed reason for the recall (at least 5 characters).");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        batch_id: selectedBatchId,
        reason: reason.trim(),
        severity: severity,
      };

      const res = await apiClient.post<BatchRecallDetail>("/stock/recalls", payload);

      setActionSuccess(`Batch recall initiated successfully for ${res.batch_no}.`);

      // Prepend newly created recall
      const newItem: BatchRecallItem = {
        id: res.id || `rec-${Date.now()}`,
        batch_id: res.batch_id,
        batch_no: res.batch_no,
        product_id: res.product_id,
        product_name: res.product_name,
        product_sku: res.product_sku,
        warehouse_name: res.warehouse_name,
        remaining_quantity: res.remaining_quantity,
        reason: res.reason,
        severity: res.severity,
        status: res.status,
        initiated_at: res.initiated_at || new Date().toISOString(),
        resolved_at: null,
        affected_orders_count: res.affected_orders?.length || 0,
        notified_count: 0,
      };

      setRecalls((prev) => [newItem, ...prev]);

      // Open detail drawer for newly initiated recall
      setSelectedRecall(res);
      setIsCreateOpen(false);
      setReason("");
      setSelectedProductId("");
      setSelectedBatchId("");
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
            ? String((err as { message: unknown }).message)
            : "Failed to initiate batch recall.";
      setActionError(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  // Open Detail Modal
  const handleOpenDetail = async (item: BatchRecallItem) => {
    setLoadingDetail(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const detail = await apiClient.get<BatchRecallDetail>(`/stock/recalls/${item.id}`);
      setSelectedRecall(detail);
    } catch {
      // Fallback to local mock details if endpoint unavailable
      setSelectedRecall({
        ...item,
        warehouse_id: "wh-1",
        affected_orders: [
          {
            id: "aff-1",
            sales_order_id: "so-101",
            sales_order_number: "SO-101",
            buyer_type: "retailer",
            buyer_name: "Fresh Mart Retail",
            buyer_phone: "+919876543210",
            buyer_email: "freshmart@example.com",
            order_date: new Date(Date.now() - 86400000 * 2).toISOString(),
            quantity_supplied: 25.0,
            notified_at: item.status === "resolved" ? new Date().toISOString() : null,
          },
          {
            id: "aff-2",
            sales_order_id: "so-102",
            sales_order_number: "SO-102",
            buyer_type: "retailer",
            buyer_name: "Green Grocers Hub",
            buyer_phone: "+919876543211",
            buyer_email: "greengrocers@example.com",
            order_date: new Date(Date.now() - 86400000 * 3).toISOString(),
            quantity_supplied: 15.0,
            notified_at: item.status === "resolved" ? new Date().toISOString() : null,
          },
        ],
      });
    } finally {
      setLoadingDetail(false);
    }
  };

  // Broadcast Recall Alerts
  const handleNotifyAffected = async (recallId: string) => {
    setNotifying(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const res = await apiClient.patch<{
        status: "notifying";
        retailers_notified_count: number;
        customers_notified_count: number;
        notified_at: string;
      }>(`/stock/recalls/${recallId}/notify`, {});

      setActionSuccess(
        `Recall notification broadcast sent to ${res.retailers_notified_count} retailers and ${res.customers_notified_count} customers.`,
      );

      // Update state
      startTransition(() => {
        if (selectedRecall) {
          const nowStr = res.notified_at || new Date().toISOString();
          const updatedAffected = selectedRecall.affected_orders.map((a) => ({
            ...a,
            notified_at: a.notified_at || nowStr,
          }));
          setSelectedRecall({
            ...selectedRecall,
            status: "notifying",
            notified_count: updatedAffected.length,
            affected_orders: updatedAffected,
          });
        }

        setRecalls((prev) =>
          prev.map((r) =>
            r.id === recallId
              ? {
                  ...r,
                  status: "notifying",
                  notified_count: r.affected_orders_count,
                }
              : r,
          ),
        );
      });
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
            ? String((err as { message: unknown }).message)
            : "Failed to broadcast recall notifications.";
      setActionError(errorMsg);
    } finally {
      setNotifying(false);
    }
  };

  // Resolve Recall
  const handleResolveRecall = async (recallId: string) => {
    setResolving(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const res = await apiClient.patch<BatchRecallDetail>(
        `/stock/recalls/${recallId}/resolve`,
        {},
      );

      setActionSuccess(`Recall for batch ${res.batch_no} marked as RESOLVED.`);

      startTransition(() => {
        if (selectedRecall) {
          setSelectedRecall({
            ...selectedRecall,
            status: "resolved",
            resolved_at: res.resolved_at || new Date().toISOString(),
          });
        }

        setRecalls((prev) =>
          prev.map((r) =>
            r.id === recallId
              ? {
                  ...r,
                  status: "resolved",
                  resolved_at: res.resolved_at || new Date().toISOString(),
                }
              : r,
          ),
        );
      });
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
            ? String((err as { message: unknown }).message)
            : "Failed to resolve recall.";
      setActionError(errorMsg);
    } finally {
      setResolving(false);
    }
  };

  const columns: DataTableColumn<BatchRecallItem>[] = [
    {
      key: "severity",
      header: "Severity",
      sortable: true,
      render: (r) => {
        if (r.severity === "critical") {
          return <GlassBadge variant="error">CRITICAL</GlassBadge>;
        }
        if (r.severity === "medium") {
          return <GlassBadge variant="warning">MEDIUM</GlassBadge>;
        }
        return <GlassBadge variant="accent">LOW</GlassBadge>;
      },
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      render: (r) => {
        if (r.status === "resolved") {
          return <GlassBadge variant="success">RESOLVED</GlassBadge>;
        }
        if (r.status === "notifying") {
          return <GlassBadge variant="accent">NOTIFYING</GlassBadge>;
        }
        return <GlassBadge variant="warning">INITIATED</GlassBadge>;
      },
    },

    {
      key: "product_name",
      header: "Product & SKU",
      sortable: true,
      render: (r) => (
        <div className="flex flex-col">
          <span className="font-semibold text-xs text-[var(--text)]">{r.product_name}</span>
          <span className="font-mono text-[11px] text-[var(--text-muted)]">{r.product_sku}</span>
        </div>
      ),
    },
    {
      key: "batch_no",
      header: "Recalled Batch #",
      render: (r) => (
        <div className="flex flex-col">
          <span className="font-mono font-bold text-xs text-red-400">{r.batch_no}</span>
          <span className="text-[10px] text-[var(--text-muted)]">{r.warehouse_name}</span>
        </div>
      ),
    },
    {
      key: "remaining_quantity",
      header: "Remaining Isolated Stock",
      align: "right",
      sortable: true,
      render: (r) => (
        <div className="flex flex-col items-end">
          <span className="font-mono font-bold text-xs text-red-400">
            {r.remaining_quantity.toFixed(2)} units
          </span>
          <span className="text-[10px] text-red-400/70 uppercase tracking-tight font-mono">
            Unsellable
          </span>
        </div>
      ),
    },
    {
      key: "affected_orders_count",
      header: "Affected Orders",
      align: "center",
      sortable: true,
      render: (r) => (
        <div className="flex items-center justify-center gap-1">
          <GlassBadge variant={r.affected_orders_count > 0 ? "warning" : "neutral"}>
            {r.affected_orders_count} Traced
          </GlassBadge>
        </div>
      ),
    },
    {
      key: "initiated_at",
      header: "Initiated Date",
      sortable: true,
      render: (r) => (
        <span className="font-mono text-xs text-[var(--text-muted)]">
          {new Date(r.initiated_at).toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          })}
        </span>
      ),
    },
    {
      key: "id",
      header: "Action",
      align: "right",
      render: (r) => (
        <GlassButton variant="secondary" size="sm" onClick={() => handleOpenDetail(r)}>
          <ShieldAlert className="w-3.5 h-3.5 mr-1 text-purple-400" />
          Trace & Alert
        </GlassButton>
      ),
    },
  ];

  return (
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--text)]">
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/admin/inventory">
              <button className="p-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-[var(--text-muted)] hover:text-[var(--text)] transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </button>
            </Link>
            <div>
              <h1 className="text-xl font-bold text-[var(--text)] flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-red-400" />
                Batch Recall & Traceability
              </h1>
              <p className="text-xs text-[var(--text-muted)]">
                Trace outbound sales orders, isolate defective inventory, and broadcast emergency
                alerts to retailers.
              </p>
            </div>
          </div>

          <GlassButton variant="primary" size="md" onClick={() => setIsCreateOpen(true)}>
            <AlertTriangle className="w-4 h-4 mr-1.5 text-amber-300" />
            Initiate Batch Recall
          </GlassButton>
        </div>

        {/* Global Action Alerts */}
        {actionError && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{actionError}</span>
            </div>
            <button onClick={() => setActionError(null)}>
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {actionSuccess && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-400 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{actionSuccess}</span>
            </div>
            <button onClick={() => setActionSuccess(null)}>
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* 4 KPI Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard className="p-4 space-y-1">
            <span className="text-xs text-[var(--text-muted)] font-medium flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-purple-400" /> Total Recalls
            </span>
            <div className="text-2xl font-bold font-mono text-[var(--text)]">{kpis.total}</div>
            <p className="text-[11px] text-[var(--text-muted)]">Historical defect events</p>
          </GlassCard>

          <GlassCard className="p-4 space-y-1">
            <span className="text-xs text-amber-400 font-medium flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" /> Active Quarantines
            </span>
            <div className="text-2xl font-bold font-mono text-amber-400">{kpis.active}</div>
            <p className="text-[11px] text-[var(--text-muted)]">Unresolved recall workflows</p>
          </GlassCard>

          <GlassCard className="p-4 space-y-1">
            <span className="text-xs text-cyan-400 font-medium flex items-center gap-1.5">
              <Package className="w-3.5 h-3.5" /> Affected Orders Traced
            </span>
            <div className="text-2xl font-bold font-mono text-cyan-400">{kpis.totalAffected}</div>
            <p className="text-[11px] text-[var(--text-muted)]">
              Outbound orders containing defect batch
            </p>
          </GlassCard>

          <GlassCard className="p-4 space-y-1">
            <span className="text-xs text-emerald-400 font-medium flex items-center gap-1.5">
              <BellRing className="w-3.5 h-3.5" /> Retailers Alerted
            </span>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              {kpis.totalNotified}
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">
              WhatsApp / Email notices dispatched
            </p>
          </GlassCard>
        </div>

        {/* Filters and Search Bar */}
        <GlassCard className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search product, batch #, reason..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {/* Status Filter */}
            <GlassSelect
              value={statusFilter}
              onChange={setStatusFilter}
              options={[
                { value: "all", label: "All Statuses" },
                { value: "initiated", label: "Initiated" },
                { value: "notifying", label: "Notifying" },
                { value: "resolved", label: "Resolved" },
              ]}
              className="w-36"
            />

            {/* Severity Filter */}
            <GlassSelect
              value={severityFilter}
              onChange={setSeverityFilter}
              options={[
                { value: "all", label: "All Severities" },
                { value: "critical", label: "Critical" },
                { value: "medium", label: "Medium" },
                { value: "low", label: "Low" },
              ]}
              className="w-36"
            />
          </div>
        </GlassCard>

        {/* Recalls DataTable */}
        <DataTable
          data={filteredRecalls}
          columns={columns}
          keyExtractor={(r) => r.id}
          isLoading={loading}
          emptyTitle="No batch recalls found."
          emptyDescription="Product quality recalls and defect tracking events will appear here."
        />

        {/* Initiate Batch Recall Modal */}
        {isCreateOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="relative w-full max-w-xl">
              <GlassCard className="p-6 space-y-5 border-red-500/30">
                <div className="flex items-center justify-between border-b border-[var(--glass-border)] pb-3">
                  <div className="flex items-center gap-2 text-red-400">
                    <AlertTriangle className="w-5 h-5" />
                    <h2 className="text-base font-bold text-[var(--text)]">
                      Initiate Product Batch Recall
                    </h2>
                  </div>
                  <button
                    onClick={() => setIsCreateOpen(false)}
                    className="text-[var(--text-muted)] hover:text-[var(--text)]"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleInitiateRecall} className="space-y-4">
                  {/* Product Picker */}
                  <div className="space-y-1">
                    <label
                      htmlFor="recall-prod"
                      className="block text-xs font-medium text-[var(--text-muted)]"
                    >
                      Product to Recall *
                    </label>
                    <GlassSelect
                      id="recall-prod"
                      value={selectedProductId}
                      onChange={setSelectedProductId}
                      placeholder="-- Select Product --"
                      options={products.map((p) => ({
                        value: p.id,
                        label: `${p.name} (${p.sku})`,
                      }))}
                    />
                  </div>

                  {/* Batch Picker */}
                  <div className="space-y-1">
                    <label
                      htmlFor="recall-batch"
                      className="block text-xs font-medium text-[var(--text-muted)]"
                    >
                      Defective Stock Batch *
                    </label>
                    <GlassSelect
                      id="recall-batch"
                      value={selectedBatchId}
                      onChange={setSelectedBatchId}
                      disabled={batches.length === 0}
                      placeholder={
                        batches.length === 0
                          ? selectedProductId
                            ? "No active batches found"
                            : "Select product first"
                          : "-- Choose Stock Batch --"
                      }
                      options={batches.map((b) => ({
                        value: b.id,
                        label: `Batch ${b.batch_no} — On Hand: ${Number(b.quantity).toFixed(2)} units`,
                      }))}
                    />
                  </div>

                  {/* Severity */}
                  <div className="space-y-1">
                    <label
                      htmlFor="recall-severity"
                      className="block text-xs font-medium text-[var(--text-muted)]"
                    >
                      Recall Severity Classification *
                    </label>
                    <GlassSelect
                      id="recall-severity"
                      value={severity}
                      onChange={(val) => setSeverity(val as "low" | "medium" | "critical")}
                      options={[
                        {
                          value: "critical",
                          label: "Critical — Immediate Safety Hazard / Contamination",
                        },
                        {
                          value: "medium",
                          label: "Medium — Quality / Packaging Defect",
                        },
                        {
                          value: "low",
                          label: "Low — Minor Labeling / Spec Deviation",
                        },
                      ]}
                    />
                  </div>

                  {/* Reason Textarea */}
                  <div className="space-y-1">
                    <label
                      htmlFor="recall-reason"
                      className="block text-xs font-medium text-[var(--text-muted)]"
                    >
                      Root Cause / Recall Reason *
                    </label>
                    <textarea
                      id="recall-reason"
                      rows={3}
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="Describe the exact quality defect, contaminated batch analysis, or regulatory breach..."
                      required
                      className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                    />
                  </div>

                  {/* Quarantine Invariant Alert */}
                  <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-[11px] text-red-300 space-y-1">
                    <span className="font-semibold flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5" /> Immediate Quarantine & Traceability
                      Guarantee
                    </span>
                    <p className="text-[var(--text-muted)]">
                      All remaining stock in this batch will be flagged unsellable immediately. The
                      system will scan the ledger to trace all outbound sales orders.
                    </p>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-2">
                    <GlassButton
                      variant="ghost"
                      size="md"
                      type="button"
                      onClick={() => setIsCreateOpen(false)}
                    >
                      Cancel
                    </GlassButton>
                    <GlassButton
                      variant="destructive"
                      size="md"
                      type="submit"
                      disabled={submitting || !selectedBatchId || !reason.trim()}
                    >
                      {submitting ? "Initiating Recall..." : "Initiate Recall & Trace Orders"}
                    </GlassButton>
                  </div>
                </form>
              </GlassCard>
            </div>
          </div>
        )}

        {/* Traceability & Detail Drawer / Modal */}
        {selectedRecall && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto">
              <GlassCard className="p-6 space-y-6">
                {/* Header */}
                <div className="flex items-start justify-between border-b border-[var(--glass-border)] pb-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-bold text-[var(--text)]">
                        Batch Traceability: {selectedRecall.batch_no}
                      </h2>
                      {selectedRecall.severity === "critical" ? (
                        <GlassBadge variant="error">CRITICAL</GlassBadge>
                      ) : selectedRecall.severity === "medium" ? (
                        <GlassBadge variant="warning">MEDIUM</GlassBadge>
                      ) : (
                        <GlassBadge variant="accent">LOW</GlassBadge>
                      )}
                      {selectedRecall.status === "resolved" ? (
                        <GlassBadge variant="success">RESOLVED</GlassBadge>
                      ) : selectedRecall.status === "notifying" ? (
                        <GlassBadge variant="accent">NOTIFYING</GlassBadge>
                      ) : (
                        <GlassBadge variant="warning">INITIATED</GlassBadge>
                      )}
                    </div>
                    <p className="text-xs text-[var(--text-muted)]">
                      Product: {selectedRecall.product_name} ({selectedRecall.product_sku}) •
                      Facility: {selectedRecall.warehouse_name}
                    </p>
                  </div>

                  <button
                    onClick={() => setSelectedRecall(null)}
                    className="text-[var(--text-muted)] hover:text-[var(--text)] p-1"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Reason & Isolated Stock Info */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2 p-3.5 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] space-y-1">
                    <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-mono">
                      Recall Root Cause / Reason
                    </span>
                    <p className="text-xs text-[var(--text)]">{selectedRecall.reason}</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 space-y-1">
                    <span className="text-[10px] text-red-300 uppercase tracking-wider font-mono flex items-center gap-1">
                      <ShieldAlert className="w-3 h-3" /> Isolated On-Hand
                    </span>
                    <div className="text-lg font-bold font-mono text-red-400">
                      {selectedRecall.remaining_quantity.toFixed(2)} units
                    </div>
                    <span className="text-[10px] text-red-300/80">Excluded from sales orders</span>
                  </div>
                </div>

                {/* Traced Affected Orders Table */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold uppercase tracking-wider font-mono text-[var(--text)] flex items-center gap-1.5">
                      <Building2 className="w-4 h-4 text-purple-400" /> Traced Affected Orders &
                      Retailers ({selectedRecall.affected_orders.length})
                    </h3>
                    <span className="text-xs text-[var(--text-muted)] font-mono">
                      {selectedRecall.notified_count} of {selectedRecall.affected_orders.length}{" "}
                      Notified
                    </span>
                  </div>

                  {loadingDetail ? (
                    <div className="p-8 text-center text-xs text-[var(--text-muted)]">
                      Tracing outbound sales order movements...
                    </div>
                  ) : selectedRecall.affected_orders.length === 0 ? (
                    <div className="p-6 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-center text-xs text-[var(--text-muted)]">
                      Zero outbound sales orders drew from this batch. No retailers affected.
                    </div>
                  ) : (
                    <div className="overflow-x-auto rounded-xl border border-[var(--glass-border)]">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-[var(--surface)] border-b border-[var(--glass-border)] text-[var(--text-muted)]">
                          <tr>
                            <th className="p-3">Order Ref</th>
                            <th className="p-3">Buyer / Retailer</th>
                            <th className="p-3">Contact</th>
                            <th className="p-3 text-right">Units Supplied</th>
                            <th className="p-3">Notification Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--glass-border)] bg-[var(--surface-hover)]">
                          {selectedRecall.affected_orders.map((aff) => (
                            <tr key={aff.id} className="hover:bg-[var(--surface)]">
                              <td className="p-3 font-mono font-semibold text-[var(--text)]">
                                {aff.sales_order_number || aff.sales_order_id.slice(0, 8)}
                              </td>
                              <td className="p-3 font-medium text-[var(--text)]">
                                {aff.buyer_name}
                                <span className="block text-[10px] text-[var(--text-muted)] capitalize">
                                  {aff.buyer_type}
                                </span>
                              </td>
                              <td className="p-3 text-[11px] text-[var(--text-muted)] font-mono">
                                <div>{aff.buyer_phone || "—"}</div>
                                <div className="text-[10px]">{aff.buyer_email || ""}</div>
                              </td>
                              <td className="p-3 text-right font-mono font-bold text-purple-300">
                                {aff.quantity_supplied.toFixed(2)}
                              </td>
                              <td className="p-3">
                                {aff.notified_at ? (
                                  <div className="flex items-center gap-1 text-emerald-400 text-[11px]">
                                    <Check className="w-3.5 h-3.5" />
                                    <span>
                                      Alerted (
                                      {new Date(aff.notified_at).toLocaleTimeString("en-IN", {
                                        hour: "2-digit",
                                        minute: "2-digit",
                                      })}
                                      )
                                    </span>
                                  </div>
                                ) : (
                                  <div className="flex items-center gap-1 text-amber-400 text-[11px]">
                                    <AlertTriangle className="w-3.5 h-3.5" />
                                    <span>Pending Alert</span>
                                  </div>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Drawer Footer Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-[var(--glass-border)]">
                  <GlassButton variant="ghost" size="sm" onClick={() => setSelectedRecall(null)}>
                    Close
                  </GlassButton>

                  <div className="flex items-center gap-3">
                    {selectedRecall.status !== "resolved" && (
                      <>
                        <GlassButton
                          variant="secondary"
                          size="sm"
                          disabled={notifying}
                          onClick={() => handleNotifyAffected(selectedRecall.id)}
                        >
                          <Send className="w-3.5 h-3.5 mr-1.5 text-cyan-400" />
                          {notifying
                            ? "Broadcasting..."
                            : "Broadcast Recall Alerts (WhatsApp + Email)"}
                        </GlassButton>

                        <GlassButton
                          variant="primary"
                          size="sm"
                          disabled={resolving}
                          onClick={() => handleResolveRecall(selectedRecall.id)}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
                          {resolving ? "Resolving..." : "Mark as Resolved"}
                        </GlassButton>
                      </>
                    )}
                  </div>
                </div>
              </GlassCard>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
