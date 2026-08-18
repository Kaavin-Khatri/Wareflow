"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";

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
  FileSpreadsheet,
  Plus,
  Truck,
  Calendar,
  IndianRupee,
  CheckCircle2,
  AlertCircle,
  Clock,
  Boxes,
  Eye,
  Send,
  Trash2,
  Undo2,
  ShieldAlert,
} from "lucide-react";

export type POStatus =
  "draft" | "ordered" | "ready_for_dispatch" | "partially_received" | "received" | "cancelled";

export interface POItem {
  id: string;
  po_id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  qty_ordered: number;
  qty_received: number;
  unit_cost: number;
  uom_id: string | null;
  uom_name: string | null;
  base_uom_name: string | null;
  line_total: number;
}

export interface PurchaseOrderItemType {
  id: string;
  po_number: string;
  supplier_id: string;
  supplier_name: string;
  status: POStatus;
  order_date: string;
  expected_date: string | null;
  total_amount: number;
  items_count: number;
  items: POItem[];
  created_at: string;
}

interface SupplierOption {
  id: string;
  name: string;
  is_active: boolean;
  fssai_license_no?: string | null;
  fssai_expiry_date?: string | null;
}

interface ProductOption {
  id: string;
  name: string;
  sku: string;
  cost_price: number;
  base_uom_id: string | null;
  unit?: string;
  is_active: boolean;
}

interface WarehouseOption {
  id: string;
  name: string;
  location?: string;
  is_active: boolean;
}

interface UomOption {
  id: string;
  name: string;
  abbreviation: string;
}

export default function PurchaseOrdersPage() {
  const router = useRouter();
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrderItemType[]>([]);

  const [suppliers, setSuppliers] = useState<SupplierOption[]>([]);
  const [products, setProducts] = useState<ProductOption[]>([]);
  const [warehouses, setWarehouses] = useState<WarehouseOption[]>([]);
  const [uoms, setUoms] = useState<UomOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedSupplierId, setSelectedSupplierId] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modals state
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [receiveModalOpen, setReceiveModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [activePO, setActivePO] = useState<PurchaseOrderItemType | null>(null);

  // Create Draft PO Form State
  const [draftSupplierId, setDraftSupplierId] = useState("");
  const [draftExpectedDate, setDraftExpectedDate] = useState("");
  const [draftLines, setDraftLines] = useState<
    { product_id: string; qty_ordered: number; unit_cost: number; uom_id: string }[]
  >([{ product_id: "", qty_ordered: 1, unit_cost: 0, uom_id: "" }]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // FSSAI Compliance Confirmation for Expired Supplier Licenses
  const [fssaiConfirmOpen, setFssaiConfirmOpen] = useState(false);
  const [fssaiAcknowledged, setFssaiAcknowledged] = useState(false);

  // Goods Receive Form State
  const [receiveLines, setReceiveLines] = useState<
    {
      po_item_id: string;
      product_name: string;
      product_sku: string;
      qty_ordered: number;
      qty_received: number;
      qty_to_receive: number;
      batch_no: string;
      expiry_date: string;
      warehouse_id: string;
    }[]
  >([]);

  // 1. Fetch initial data
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [poRes, supRes, prodRes, whRes, uomRes] = await Promise.all([
        apiClient.get<PurchaseOrderItemType[]>("/purchase-orders").catch(() => []),
        apiClient.get<SupplierOption[]>("/suppliers").catch(() => []),
        apiClient.get<{ items: ProductOption[] } | ProductOption[]>("/products").catch(() => []),
        apiClient.get<WarehouseOption[]>("/stock/warehouses").catch(() => []),
        apiClient.get<UomOption[]>("/uom").catch(() => []),
      ]);

      setPurchaseOrders(Array.isArray(poRes) ? poRes : []);
      setSuppliers(Array.isArray(supRes) ? supRes.filter((s) => s.is_active) : []);

      const resolvedProducts = Array.isArray(prodRes)
        ? prodRes
        : (prodRes as { items?: ProductOption[] })?.items || [];
      setProducts(resolvedProducts.filter((p) => p.is_active));

      setWarehouses(Array.isArray(whRes) ? whRes.filter((w) => w.is_active) : []);
      setUoms(Array.isArray(uomRes) ? uomRes : []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load purchase orders.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        const [poRes, supRes, prodRes, whRes, uomRes] = await Promise.all([
          apiClient.get<PurchaseOrderItemType[]>("/purchase-orders").catch(() => []),
          apiClient.get<SupplierOption[]>("/suppliers").catch(() => []),
          apiClient.get<{ items: ProductOption[] } | ProductOption[]>("/products").catch(() => []),
          apiClient.get<WarehouseOption[]>("/stock/warehouses").catch(() => []),
          apiClient.get<UomOption[]>("/uom").catch(() => []),
        ]);

        if (!ignore) {
          setPurchaseOrders(Array.isArray(poRes) ? poRes : []);
          setSuppliers(Array.isArray(supRes) ? supRes.filter((s) => s.is_active) : []);

          const resolvedProducts = Array.isArray(prodRes)
            ? prodRes
            : (prodRes as { items?: ProductOption[] })?.items || [];
          setProducts(resolvedProducts.filter((p) => p.is_active));

          setWarehouses(Array.isArray(whRes) ? whRes.filter((w) => w.is_active) : []);
          setUoms(Array.isArray(uomRes) ? uomRes : []);
        }
      } catch (err: unknown) {
        if (!ignore) {
          const msg = err instanceof Error ? err.message : "Failed to load purchase orders.";
          setError(msg);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    loadData();
    return () => {
      ignore = true;
    };
  }, []);

  // 2. Filtered list
  const filteredOrders = useMemo(() => {
    return purchaseOrders.filter((po) => {
      // Status filter
      if (statusFilter !== "all" && po.status !== statusFilter) {
        return false;
      }
      // Supplier filter
      if (selectedSupplierId !== "all" && po.supplier_id !== selectedSupplierId) {
        return false;
      }
      // Search term
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesNumber = po.po_number?.toLowerCase().includes(q);
        const matchesSupplier = po.supplier_name?.toLowerCase().includes(q);
        if (!matchesNumber && !matchesSupplier) return false;
      }
      return true;
    });
  }, [purchaseOrders, statusFilter, selectedSupplierId, searchQuery]);

  // 3. KPI Summaries
  const kpis = useMemo(() => {
    const totalOrders = purchaseOrders.length;
    const totalSpend = purchaseOrders.reduce((sum, po) => sum + (po.total_amount || 0), 0);
    const draftCount = purchaseOrders.filter((p) => p.status === "draft").length;
    const orderedCount = purchaseOrders.filter((p) => p.status === "ordered").length;
    const partiallyReceivedCount = purchaseOrders.filter(
      (p) => p.status === "partially_received",
    ).length;
    const receivedCount = purchaseOrders.filter((p) => p.status === "received").length;

    return {
      totalOrders,
      totalSpend,
      draftCount,
      orderedCount,
      partiallyReceivedCount,
      receivedCount,
    };
  }, [purchaseOrders]);

  // Helper status badge styles
  const renderStatusBadge = (status: POStatus) => {
    switch (status) {
      case "draft":
        return <GlassBadge variant="neutral">Draft</GlassBadge>;
      case "ordered":
        return <GlassBadge variant="accent">Ordered</GlassBadge>;
      case "partially_received":
        return <GlassBadge variant="warning">Partially Received</GlassBadge>;
      case "received":
        return <GlassBadge variant="success">Fully Received</GlassBadge>;
      case "cancelled":
        return <GlassBadge variant="error">Cancelled</GlassBadge>;
      default:
        return <GlassBadge variant="neutral">{status}</GlassBadge>;
    }
  };

  // 4. Create Draft PO Handler
  const handleOpenCreateModal = () => {
    setDraftSupplierId(suppliers[0]?.id || "");
    setDraftExpectedDate("");
    setDraftLines([
      {
        product_id: products[0]?.id || "",
        qty_ordered: 10,
        unit_cost: products[0]?.cost_price || 0,
        uom_id: products[0]?.base_uom_id || "",
      },
    ]);
    setError(null);
    setCreateModalOpen(true);
  };

  const handleProductSelect = (index: number, productId: string) => {
    const selectedProd = products.find((p) => p.id === productId);
    const updated = [...draftLines];
    updated[index] = {
      ...updated[index],
      product_id: productId,
      unit_cost: selectedProd?.cost_price || 0,
      uom_id: selectedProd?.base_uom_id || "",
    };
    setDraftLines(updated);
  };

  const handleAddDraftLine = () => {
    setDraftLines([
      ...draftLines,
      {
        product_id: products[0]?.id || "",
        qty_ordered: 1,
        unit_cost: products[0]?.cost_price || 0,
        uom_id: products[0]?.base_uom_id || "",
      },
    ]);
  };

  const handleRemoveDraftLine = (index: number) => {
    if (draftLines.length <= 1) return;
    setDraftLines(draftLines.filter((_, i) => i !== index));
  };

  const draftGrandTotal = useMemo(() => {
    return draftLines.reduce(
      (sum, line) => sum + (Number(line.qty_ordered) || 0) * (Number(line.unit_cost) || 0),
      0,
    );
  }, [draftLines]);

  /**
   * Check if the selected supplier's FSSAI license is expired.
   * Returns true if expired and user has NOT yet acknowledged the risk.
   */
  const isSelectedSupplierFssaiExpired = useMemo(() => {
    if (!draftSupplierId) return false;
    const supplier = suppliers.find((s) => s.id === draftSupplierId);
    if (!supplier?.fssai_expiry_date) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const expiry = new Date(supplier.fssai_expiry_date);
    expiry.setHours(0, 0, 0, 0);
    return expiry < today;
  }, [draftSupplierId, suppliers]);

  const selectedSupplierForCompliance = useMemo(
    () => suppliers.find((s) => s.id === draftSupplierId) || null,
    [draftSupplierId, suppliers],
  );

  const handleCreateDraftPOSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!draftSupplierId) {
      setError("Please select a valid supplier.");
      return;
    }
    if (draftLines.some((line) => !line.product_id || line.qty_ordered <= 0)) {
      setError("Please ensure each line item has a valid product and positive quantity.");
      return;
    }

    // FSSAI compliance gate: if supplier license expired, require explicit acknowledgment
    if (isSelectedSupplierFssaiExpired && !fssaiAcknowledged) {
      setFssaiConfirmOpen(true);
      return;
    }


    await executeCreateDraftPO();
  };

  const handleFssaiConfirmProceed = async () => {
    setFssaiAcknowledged(true);
    setFssaiConfirmOpen(false);
    await executeCreateDraftPO();
  };

  const executeCreateDraftPO = async () => {
    try {
      setIsSubmitting(true);
      setError(null);

      const payload = {
        supplier_id: draftSupplierId,
        expected_date: draftExpectedDate || null,
        items: draftLines.map((line) => ({
          product_id: line.product_id,
          qty_ordered: Number(line.qty_ordered),
          unit_cost: Number(line.unit_cost),
          uom_id: line.uom_id || null,
        })),
      };

      await apiClient.post("/purchase-orders", payload);
      setSuccess("Draft purchase order created successfully!");
      setCreateModalOpen(false);
      setFssaiAcknowledged(false);
      await fetchData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create purchase order.";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 5. Place Order Transition
  const handlePlaceOrder = async (po: PurchaseOrderItemType) => {
    try {
      setIsSubmitting(true);
      setError(null);
      await apiClient.post(`/purchase-orders/${po.id}/order`, {});
      setSuccess(`Order ${po.po_number} successfully placed with ${po.supplier_name}!`);
      await fetchData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to place purchase order.";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 6. Open Receive Goods Modal
  const handleOpenReceiveModal = (po: PurchaseOrderItemType) => {
    setActivePO(po);
    const defaultWarehouseId = warehouses[0]?.id || "";
    const lines = (po.items || []).map((item) => {
      const remaining = Math.max(0, item.qty_ordered - item.qty_received);
      return {
        po_item_id: item.id,
        product_name: item.product_name,
        product_sku: item.product_sku,
        qty_ordered: item.qty_ordered,
        qty_received: item.qty_received,
        qty_to_receive: remaining,
        batch_no: `BATCH-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-01`,
        expiry_date: "",
        warehouse_id: defaultWarehouseId,
      };
    });
    setReceiveLines(lines);
    setError(null);
    setReceiveModalOpen(true);
  };

  const handleReceiveGoodsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activePO) return;

    const itemsToReceive = receiveLines.filter((l) => l.qty_to_receive > 0);
    if (itemsToReceive.length === 0) {
      setError("Please specify a quantity greater than zero for at least one item.");
      return;
    }

    for (const item of itemsToReceive) {
      if (!item.batch_no.trim()) {
        setError(`Please enter a batch number for ${item.product_name}.`);
        return;
      }
      if (!item.warehouse_id) {
        setError(`Please select a destination warehouse for ${item.product_name}.`);
        return;
      }
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const payload = {
        items: itemsToReceive.map((item) => ({
          po_item_id: item.po_item_id,
          qty_received: Number(item.qty_to_receive),
          batch_no: item.batch_no.trim().toUpperCase(),
          expiry_date: item.expiry_date || null,
          warehouse_id: item.warehouse_id,
        })),
      };

      await apiClient.post(`/purchase-orders/${activePO.id}/receive`, payload);
      setSuccess(`Goods receipt recorded successfully! Stock balances updated.`);
      setReceiveModalOpen(false);
      await fetchData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to record goods receipt.";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 7. DataTable Columns
  const columns: DataTableColumn<PurchaseOrderItemType>[] = [
    {
      key: "po_number",
      header: "PO Number",
      render: (po) => (
        <div className="flex flex-col">
          <span className="font-mono text-sm font-semibold text-sky-400">{po.po_number}</span>
          <span className="text-xs text-slate-400">
            {new Date(po.order_date).toLocaleDateString()}
          </span>
        </div>
      ),
    },
    {
      key: "supplier_name",
      header: "Supplier & Vendor",
      render: (po) => (
        <div className="flex items-center gap-2">
          <Truck className="w-4 h-4 text-slate-400 shrink-0" />
          <span className="font-medium text-slate-200">{po.supplier_name}</span>
        </div>
      ),
    },
    {
      key: "expected_date",
      header: "Expected Delivery",
      render: (po) => (
        <div className="flex items-center gap-1.5 text-xs text-slate-300">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          {po.expected_date ? new Date(po.expected_date).toLocaleDateString() : "Not specified"}
        </div>
      ),
    },
    {
      key: "total_amount",
      header: "Total Amount",
      render: (po) => (
        <div className="flex items-center gap-1 font-semibold text-emerald-400">
          <IndianRupee className="w-3.5 h-3.5" />
          {po.total_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (po) => renderStatusBadge(po.status),
    },
    {
      key: "progress",
      header: "Receiving Progress",
      render: (po) => {
        const totalOrdered = po.items?.reduce((s, i) => s + i.qty_ordered, 0) || 1;
        const totalReceived = po.items?.reduce((s, i) => s + i.qty_received, 0) || 0;
        const pct = Math.min(100, Math.round((totalReceived / totalOrdered) * 100));

        return (
          <div className="w-36 space-y-1">
            <div className="flex justify-between text-xs text-slate-400">
              <span>{po.items?.length || 0} lines</span>
              <span className="font-mono">{pct}%</span>
            </div>
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden border border-white/5">
              <div
                className={`h-full transition-all duration-500 rounded-full ${
                  pct === 100 ? "bg-emerald-500" : pct > 0 ? "bg-amber-500" : "bg-slate-700"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      },
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (po) => (
        <div className="flex items-center justify-end gap-2">
          {po.status === "draft" && (
            <GlassButton
              variant="outline"
              size="sm"
              onClick={() => handlePlaceOrder(po)}
              disabled={isSubmitting}
              className="text-xs py-1 px-2.5 h-8 gap-1 border-sky-500/30 text-sky-300 hover:bg-sky-500/20"
            >
              <Send className="w-3.5 h-3.5" />
              Place Order
            </GlassButton>
          )}

          {(po.status === "ordered" || po.status === "partially_received") && (
            <GlassButton
              variant="primary"
              size="sm"
              onClick={() => handleOpenReceiveModal(po)}
              className="text-xs py-1 px-3 h-8 gap-1.5 shadow-sm shadow-indigo-500/20"
            >
              <Boxes className="w-3.5 h-3.5" />
              Receive Goods
            </GlassButton>
          )}

          {(po.status === "partially_received" || po.status === "received") && (
            <GlassButton
              variant="outline"
              size="sm"
              onClick={() => router.push(`/admin/purchase-returns?po_id=${po.id}`)}
              className="text-xs py-1 px-2.5 h-8 gap-1 border-amber-500/30 text-amber-300 hover:bg-amber-500/20"
              title="Return goods to supplier"
            >
              <Undo2 className="w-3.5 h-3.5" />
              Return
            </GlassButton>
          )}

          <GlassButton
            variant="ghost"
            size="sm"
            onClick={() => {
              setActivePO(po);
              setDetailModalOpen(true);
            }}
            className="text-xs py-1 px-2 h-8 text-slate-400 hover:text-white"
          >
            <Eye className="w-3.5 h-3.5" />
          </GlassButton>
        </div>
      ),
    },
  ];

  return (
    <AppLayout>
      <ListViewTemplate
        title="Purchase Orders & Goods Inward"
        description="Manage inbound vendor procurement, purchase orders, and single-door goods receiving ledger."
        searchPlaceholder="Search by PO number or supplier name..."
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        primaryAction={
          <GlassButton
            variant="primary"
            onClick={handleOpenCreateModal}
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Purchase Order
          </GlassButton>
        }
      >
        {/* Error / Success Notifications */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-300 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-3 text-emerald-300 text-sm">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {/* Top KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <GlassCard className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">
                Total Orders
              </p>
              <p className="text-2xl font-bold text-white">{kpis.totalOrders}</p>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <IndianRupee className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">
                Total Purchasing Value
              </p>
              <p className="text-xl font-bold text-emerald-400">
                ₹{kpis.totalSpend.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
              </p>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">
                Awaiting Delivery
              </p>
              <p className="text-2xl font-bold text-amber-400">
                {kpis.orderedCount + kpis.partiallyReceivedCount}
              </p>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Boxes className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">
                Fully Received
              </p>
              <p className="text-2xl font-bold text-indigo-400">{kpis.receivedCount}</p>
            </div>
          </GlassCard>
        </div>

        {/* Filters & Status Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-1.5 bg-slate-900/60 p-1 rounded-xl border border-white/5 backdrop-blur-md">
            {[
              { id: "all", label: "All Orders" },
              { id: "draft", label: "Draft" },
              { id: "ordered", label: "Ordered" },
              { id: "partially_received", label: "Partially Received" },
              { id: "received", label: "Received" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  statusFilter === tab.id
                    ? "bg-indigo-600 text-white shadow-sm shadow-indigo-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400">Filter Supplier:</label>
            <select
              value={selectedSupplierId}
              onChange={(e) => setSelectedSupplierId(e.target.value)}
              className="bg-slate-900/80 border border-white/10 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Suppliers</option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredOrders}
          keyExtractor={(po) => po.id}
          isLoading={loading}
          emptyTitle="No purchase orders found"
          emptyDescription="No purchase orders match your active filter criteria."
        />

        {/* MODAL 1: Create Draft Purchase Order */}
        <GlassModal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          title="Create Draft Purchase Order"
          description="Create a draft purchase order with line items. You can edit quantities and prices before confirming the order."
          maxWidth="xl"
        >
          <form onSubmit={handleCreateDraftPOSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Supplier / Vendor *
                </label>
                <select
                  value={draftSupplierId}
                  onChange={(e) => {
                    setDraftSupplierId(e.target.value);
                    setFssaiAcknowledged(false);
                  }}
                  required
                  className="w-full bg-slate-900/90 border border-white/10 text-sm text-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Select a supplier...</option>
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
                {/* FSSAI Expired Supplier Warning Banner */}
                {isSelectedSupplierFssaiExpired && selectedSupplierForCompliance && (
                  <div className="mt-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-start gap-2">
                    <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold">⚠️ FSSAI License Expired</div>
                      <div className="mt-0.5 text-[var(--text-muted)]">
                        {selectedSupplierForCompliance.name}&apos;s FSSAI license
                        {selectedSupplierForCompliance.fssai_license_no && (
                          <span className="font-mono"> ({selectedSupplierForCompliance.fssai_license_no})</span>
                        )}
                        {" "}expired on {selectedSupplierForCompliance.fssai_expiry_date}.
                        Placing a PO requires explicit compliance acknowledgment.
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Expected Delivery Date
                </label>
                <GlassInput
                  type="date"
                  value={draftExpectedDate}
                  onChange={(e) => setDraftExpectedDate(e.target.value)}
                />
              </div>
            </div>

            {/* Line items section */}
            <div className="pt-2">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Order Line Items
                </h4>
                <GlassButton
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleAddDraftLine}
                  className="text-xs text-indigo-400 hover:text-indigo-300 gap-1 h-7"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add Line Item
                </GlassButton>
              </div>

              <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                {draftLines.map((line, idx) => (
                  <div
                    key={idx}
                    className="flex flex-wrap md:flex-nowrap items-center gap-2.5 p-3 rounded-xl bg-slate-900/60 border border-white/5"
                  >
                    <div className="flex-1 min-w-[180px]">
                      <select
                        value={line.product_id}
                        onChange={(e) => handleProductSelect(idx, e.target.value)}
                        required
                        className="w-full bg-slate-950/80 border border-white/10 text-xs text-slate-200 rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500"
                      >
                        <option value="">Select product...</option>
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} ({p.sku})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="w-24">
                      <input
                        type="number"
                        min="0.01"
                        step="any"
                        placeholder="Qty"
                        value={line.qty_ordered}
                        onChange={(e) => {
                          const updated = [...draftLines];
                          updated[idx].qty_ordered = parseFloat(e.target.value) || 0;
                          setDraftLines(updated);
                        }}
                        className="w-full bg-slate-950/80 border border-white/10 text-xs text-slate-200 rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500 text-right"
                      />
                    </div>

                    <div className="w-28">
                      <select
                        value={line.uom_id}
                        onChange={(e) => {
                          const updated = [...draftLines];
                          updated[idx].uom_id = e.target.value;
                          setDraftLines(updated);
                        }}
                        className="w-full bg-slate-950/80 border border-white/10 text-xs text-slate-200 rounded-lg px-2 py-2 focus:outline-none focus:border-indigo-500"
                      >
                        <option value="">Base Unit</option>
                        {uoms.map((u) => (
                          <option key={u.id} value={u.id}>
                            {u.abbreviation}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="w-28">
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="Cost"
                        value={line.unit_cost}
                        onChange={(e) => {
                          const updated = [...draftLines];
                          updated[idx].unit_cost = parseFloat(e.target.value) || 0;
                          setDraftLines(updated);
                        }}
                        className="w-full bg-slate-950/80 border border-white/10 text-xs text-slate-200 rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500 text-right font-mono"
                      />
                    </div>

                    <div className="w-24 text-right font-mono text-xs font-semibold text-emerald-400 pr-1">
                      ₹{((line.qty_ordered || 0) * (line.unit_cost || 0)).toFixed(2)}
                    </div>

                    {draftLines.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveDraftLine(idx)}
                        className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {/* Total preview */}
              <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-sm">
                <span className="text-slate-400">Total Purchase Value:</span>
                <span className="text-base font-bold text-emerald-400 font-mono">
                  ₹{draftGrandTotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <GlassButton
                type="button"
                variant="ghost"
                onClick={() => setCreateModalOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </GlassButton>
              <GlassButton type="submit" variant="primary" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Save Draft PO"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>

        {/* MODAL 2: Authoritative Goods Receiving Flow */}
        <GlassModal
          isOpen={receiveModalOpen}
          onClose={() => setReceiveModalOpen(false)}
          title={`Receive Inbound Goods — ${activePO?.po_number}`}
          description="Receiving stock updates inventory balances and creates immutable stock_movements(type=in) ledger entries."
          maxWidth="xl"
        >
          <form onSubmit={handleReceiveGoodsSubmit} className="space-y-4">
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-between text-xs text-indigo-300">
              <div>
                <span className="font-semibold text-white">Vendor:</span> {activePO?.supplier_name}
              </div>
              <div>
                <span className="font-semibold text-white">Date Placed:</span>{" "}
                {activePO?.order_date ? new Date(activePO.order_date).toLocaleDateString() : ""}
              </div>
            </div>

            <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
              {receiveLines.map((line, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-slate-900/70 border border-white/10 space-y-3"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div>
                      <span className="font-semibold text-slate-200 text-sm">
                        {line.product_name}
                      </span>
                      <span className="ml-2 font-mono text-slate-400">({line.product_sku})</span>
                    </div>
                    <div className="text-slate-400">
                      Ordered:{" "}
                      <span className="text-slate-200 font-semibold">{line.qty_ordered}</span> |
                      Received:{" "}
                      <span className="text-emerald-400 font-semibold">{line.qty_received}</span> |
                      Pending:{" "}
                      <span className="text-amber-400 font-semibold">
                        {Math.max(0, line.qty_ordered - line.qty_received)}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-2.5 pt-1">
                    <div>
                      <label className="block text-[11px] font-medium text-slate-400 mb-1">
                        Qty Receiving Now
                      </label>
                      <input
                        type="number"
                        min="0"
                        max={Math.max(0, line.qty_ordered - line.qty_received)}
                        step="any"
                        value={line.qty_to_receive}
                        onChange={(e) => {
                          const updated = [...receiveLines];
                          updated[idx].qty_to_receive = parseFloat(e.target.value) || 0;
                          setReceiveLines(updated);
                        }}
                        className="w-full bg-slate-950 border border-white/10 text-xs text-white rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 font-mono text-right"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-medium text-slate-400 mb-1">
                        Batch Number *
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. BATCH-01"
                        value={line.batch_no}
                        onChange={(e) => {
                          const updated = [...receiveLines];
                          updated[idx].batch_no = e.target.value;
                          setReceiveLines(updated);
                        }}
                        className="w-full bg-slate-950 border border-white/10 text-xs text-white rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 uppercase font-mono"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-medium text-slate-400 mb-1">
                        Expiry Date
                      </label>
                      <input
                        type="date"
                        value={line.expiry_date}
                        onChange={(e) => {
                          const updated = [...receiveLines];
                          updated[idx].expiry_date = e.target.value;
                          setReceiveLines(updated);
                        }}
                        className="w-full bg-slate-950 border border-white/10 text-xs text-white rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-medium text-slate-400 mb-1">
                        Warehouse *
                      </label>
                      <select
                        value={line.warehouse_id}
                        onChange={(e) => {
                          const updated = [...receiveLines];
                          updated[idx].warehouse_id = e.target.value;
                          setReceiveLines(updated);
                        }}
                        className="w-full bg-slate-950 border border-white/10 text-xs text-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:border-indigo-500"
                      >
                        {warehouses.map((wh) => (
                          <option key={wh.id} value={wh.id}>
                            {wh.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
              <GlassButton
                type="button"
                variant="ghost"
                onClick={() => setReceiveModalOpen(false)}
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
                {isSubmitting ? "Receiving..." : "Confirm Goods Receipt"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>

        {/* MODAL 3: Purchase Order Details */}
        <GlassModal
          isOpen={detailModalOpen}
          onClose={() => setDetailModalOpen(false)}
          title={`Purchase Order Details — ${activePO?.po_number}`}
          description={`Issued to ${activePO?.supplier_name}`}
          maxWidth="xl"
        >
          {activePO && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-white/5 text-xs">
                <div>
                  <span className="text-slate-400 block">PO Status</span>
                  <div className="mt-1">{renderStatusBadge(activePO.status)}</div>
                </div>
                <div>
                  <span className="text-slate-400 block">Order Date</span>
                  <span className="font-semibold text-slate-200 mt-1 block">
                    {new Date(activePO.order_date).toLocaleDateString()}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Expected Date</span>
                  <span className="font-semibold text-slate-200 mt-1 block">
                    {activePO.expected_date
                      ? new Date(activePO.expected_date).toLocaleDateString()
                      : "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Total Amount</span>
                  <span className="font-semibold text-emerald-400 font-mono mt-1 block">
                    ₹{activePO.total_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Line Items Breakdown
                </h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {activePO.items?.map((item) => (
                    <div
                      key={item.id}
                      className="p-3 rounded-xl bg-slate-900/40 border border-white/5 flex items-center justify-between text-xs"
                    >
                      <div>
                        <p className="font-semibold text-slate-200">{item.product_name}</p>
                        <p className="text-slate-400 font-mono">
                          {item.product_sku} &bull; Unit Cost: ₹{item.unit_cost.toFixed(2)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-slate-200">
                          {item.qty_received} / {item.qty_ordered} {item.uom_name || "Units"}{" "}
                          received
                        </p>
                        <p className="text-emerald-400 font-mono font-semibold">
                          ₹{item.line_total.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-white/10">
                {activePO.status !== "draft" && activePO.status !== "cancelled" ? (
                  <GlassButton
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setDetailModalOpen(false);
                      router.push(`/admin/purchase-returns?po_id=${activePO.id}`);
                    }}
                    className="gap-1.5 text-xs text-amber-300 hover:text-amber-200 border-amber-500/30"
                  >
                    <Undo2 className="w-3.5 h-3.5" />
                    Return Goods to Supplier (RMA)
                  </GlassButton>
                ) : (
                  <div />
                )}
                <GlassButton variant="ghost" onClick={() => setDetailModalOpen(false)}>
                  Close
                </GlassButton>
              </div>
            </div>
          )}
        </GlassModal>

        {/* FSSAI EXPIRED SUPPLIER CONFIRMATION DIALOG */}
        <GlassModal
          isOpen={fssaiConfirmOpen}
          onClose={() => {
            setFssaiConfirmOpen(false);
          }}
          title="⚠️ Supplier FSSAI License Expired"
          description="Proceeding with a non-compliant supplier carries regulatory risk."
        >
          <div className="space-y-4 pt-2">
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-sm">
              <div className="flex items-start gap-3">
                <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-rose-400">
                    Compliance Risk Warning
                  </div>
                  <p className="text-xs text-[var(--text-muted)] mt-1">
                    <strong className="text-rose-300">
                      {selectedSupplierForCompliance?.name}
                    </strong>
                    &apos;s FSSAI license
                    {selectedSupplierForCompliance?.fssai_license_no && (
                      <span className="font-mono">
                        {" "}({selectedSupplierForCompliance.fssai_license_no})
                      </span>
                    )}
                    {" "}expired on{" "}
                    <strong className="text-rose-300">
                      {selectedSupplierForCompliance?.fssai_expiry_date}
                    </strong>.
                    Procuring from non-compliant suppliers carries regulatory risk under
                    FSSAI Food Safety regulations.
                  </p>
                </div>
              </div>
            </div>

            <label className="flex items-start gap-3 cursor-pointer p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 hover:bg-amber-500/10 transition-colors">
              <input
                type="checkbox"
                checked={fssaiAcknowledged}
                onChange={(e) => setFssaiAcknowledged(e.target.checked)}
                className="rounded border-[var(--border)] text-amber-500 focus:ring-amber-500/40 bg-[var(--surface)] mt-0.5"
              />
              <span className="text-xs text-[var(--text)]">
                I acknowledge the compliance risk and wish to proceed with this purchase order.
                This is a human decision — the supplier&apos;s FSSAI renewal will be followed up separately.
              </span>
            </label>

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-[var(--glass-border)]">
              <GlassButton
                type="button"
                variant="ghost"
                onClick={() => {
                  setFssaiConfirmOpen(false);
                  setFssaiAcknowledged(false);
                }}
              >
                Cancel
              </GlassButton>
              <GlassButton
                type="button"
                variant="primary"
                disabled={!fssaiAcknowledged}
                onClick={handleFssaiConfirmProceed}
                className="bg-rose-600 hover:bg-rose-500 border-rose-500/40"
              >
                <ShieldAlert className="w-4 h-4 mr-1.5" />
                Proceed Anyway
              </GlassButton>
            </div>
          </div>
        </GlassModal>

      </ListViewTemplate>
    </AppLayout>
  );
}
