"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { ListViewTemplate } from "@/components/templates/ListViewTemplate";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { apiClient } from "@/lib/api-client";

import {
  ShoppingBag,
  Clock,
  Package,
  Truck,
  CheckCircle2,
  XCircle,
  Plus,
  IndianRupee,
  Crown,
  Sparkles,
  AlertTriangle,
  FileSpreadsheet,
  FileText,
  Printer,
  Eye,
  Trash2,
  RotateCcw,
  FileDown,
} from "lucide-react";




export interface SalesOrderItem {
  id: string;
  so_id: string;
  product_id: string;
  product_name?: string | null;
  product_sku?: string | null;
  qty: number;
  unit_price: number;
  line_total: number;
  uom_id?: string | null;
  uom_code?: string | null;
  is_unusual?: boolean;
  anomaly_reason?: string | null;
  historical_mean?: number | null;
  historical_stddev?: number | null;
}

export interface SalesOrder {
  id: string;
  so_number: string;
  buyer_type: "retailer" | "customer";
  retailer_id?: string | null;
  retailer_name?: string | null;
  retailer_pricing_tier?: string | null;
  customer_id?: string | null;
  customer_name?: string | null;
  status: "draft" | "confirmed" | "packed" | "shipped" | "delivered" | "cancelled";
  order_date: string;
  total_amount: number;
  created_at: string;
  items: SalesOrderItem[];
  has_unusual_items?: boolean;
  unusual_items_count?: number;
  anomaly_warnings?: string[];
}

interface RetailerOption {
  id: string;
  name: string;
  pricing_tier: string;
  credit_limit: number;
  credit_balance: number;
}

interface CustomerOption {
  id: string;
  name: string;
  phone?: string | null;
}

interface ProductOption {
  id: string;
  name: string;
  sku: string;
  wholesale_price: number;
}

interface NewOrderLine {
  product_id: string;
  qty: number;
  unit_price?: number;
}

export default function SalesOrdersAdminPage() {
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [retailers, setRetailers] = useState<RetailerOption[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [products, setProducts] = useState<ProductOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<SalesOrder | null>(null);
  const [selectedOrderDelivery, setSelectedOrderDelivery] = useState<{
    id: string;
    driver_name?: string | null;
    vehicle_no?: string | null;
    status: string;
    notes?: string | null;
    dispatched_at?: string | null;
    delivered_at?: string | null;
  } | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [generatingInvoice, setGeneratingInvoice] = useState(false);
  const router = useRouter();


  // New order form state
  const [buyerType, setBuyerType] = useState<"retailer" | "customer">("retailer");
  const [selectedRetailerId, setSelectedRetailerId] = useState<string>("");
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>("");
  const [orderLines, setOrderLines] = useState<NewOrderLine[]>([
    { product_id: "", qty: 1 },
  ]);

  async function loadData() {
    try {
      const [ordersRes, retailersRes, productsRes, customersRes] = await Promise.all([
        apiClient.get<SalesOrder[]>("/sales-orders"),
        apiClient.get<RetailerOption[]>("/retailers").catch(() => []),
        apiClient.get<ProductOption[]>("/products").catch(() => []),
        apiClient.get<CustomerOption[]>("/customers").catch(() => []),
      ]);
      setOrders(ordersRes || []);
      setRetailers(retailersRes || []);
      setProducts(productsRes || []);
      setCustomers(customersRes || []);
    } catch (err) {
      console.error("Failed to fetch sales orders:", err);
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    let ignore = false;
    async function init() {
      if (!ignore) {
        await loadData();
      }
    }
    init();
    return () => {
      ignore = true;
    };
  }, []);

  const selectedRetailer = useMemo(() => {
    return retailers.find((r) => r.id === selectedRetailerId);
  }, [retailers, selectedRetailerId]);

  // Calculate pricing for current create order form
  const computedLines = useMemo(() => {
    const tier = selectedRetailer?.pricing_tier || "standard";
    const discountMultiplier =
      tier === "gold" ? 0.9 : tier === "silver" ? 0.95 : 1.0;

    return orderLines.map((line) => {
      const prod = products.find((p) => p.id === line.product_id);
      const basePrice = prod ? prod.wholesale_price : 0;
      const unitPrice = Math.round(basePrice * discountMultiplier * 100) / 100;
      const lineTotal = Math.round(unitPrice * (line.qty || 0) * 100) / 100;
      return {
        ...line,
        product_name: prod ? prod.name : "",
        sku: prod ? prod.sku : "",
        basePrice,
        unitPrice,
        lineTotal,
      };
    });
  }, [orderLines, products, selectedRetailer]);

  const estimatedOrderTotal = useMemo(() => {
    return computedLines.reduce((acc, curr) => acc + curr.lineTotal, 0);
  }, [computedLines]);

  const isCreditExceeded = useMemo(() => {
    if (!selectedRetailer || selectedRetailer.credit_limit <= 0) return false;
    const available = selectedRetailer.credit_limit - selectedRetailer.credit_balance;
    return estimatedOrderTotal > available;
  }, [selectedRetailer, estimatedOrderTotal]);

  // KPI Calculations
  const totalOrdersCount = orders.length;
  const draftOrdersCount = orders.filter((o) => o.status === "draft").length;
  const inFulfillmentCount = orders.filter((o) =>
    ["confirmed", "packed", "shipped"].includes(o.status)
  ).length;
  const deliveredCount = orders.filter((o) => o.status === "delivered").length;
  const totalRevenue = orders
    .filter((o) => o.status !== "cancelled")
    .reduce((acc, o) => acc + Number(o.total_amount || 0), 0);

  // Filtered Orders
  const filteredOrders = useMemo(() => {
    return orders.filter((o) => {
      const matchesStatus =
        statusFilter === "ALL" || o.status.toLowerCase() === statusFilter.toLowerCase();
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        o.so_number.toLowerCase().includes(q) ||
        (o.retailer_name && o.retailer_name.toLowerCase().includes(q));
      return matchesStatus && matchesSearch;
    });
  }, [orders, statusFilter, searchQuery]);

  function handleAddLine() {
    setOrderLines([...orderLines, { product_id: "", qty: 1 }]);
  }

  function handleRemoveLine(index: number) {
    if (orderLines.length === 1) return;
    setOrderLines(orderLines.filter((_, idx) => idx !== index));
  }

  function handleLineChange(
    index: number,
    field: keyof NewOrderLine,
    value: string | number | undefined
  ) {
    const updated = [...orderLines];
    updated[index] = { ...updated[index], [field]: value };
    setOrderLines(updated);
  }

  async function handleCreateOrder(e: React.FormEvent) {
    e.preventDefault();
    setActionError(null);

    const validLines = orderLines.filter((l) => l.product_id && l.qty > 0);
    if (validLines.length === 0) {
      setActionError("Please select at least one product with quantity > 0.");
      return;
    }

    if (buyerType === "retailer" && !selectedRetailerId) {
      setActionError("Please select a wholesale retailer.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        buyer_type: buyerType,
        retailer_id: buyerType === "retailer" ? selectedRetailerId : null,
        customer_id: buyerType === "customer" && selectedCustomerId ? selectedCustomerId : null,
        items: validLines.map((l) => ({
          product_id: l.product_id,
          qty: Number(l.qty),
        })),
      };

      await apiClient.post("/sales-orders", payload);
      await loadData();
      setIsCreateModalOpen(false);
      // Reset form
      setOrderLines([{ product_id: "", qty: 1 }]);
      setSelectedRetailerId("");
      setSelectedCustomerId("");
    } catch (err: unknown) {

      const message = err instanceof Error ? err.message : String(err);
      setActionError(message || "Failed to create sales order.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleConfirmOrder(orderId: string) {
    setActionError(null);
    setSubmitting(true);
    try {
      const updated = await apiClient.post<SalesOrder>(`/sales-orders/${orderId}/confirm`);
      setSelectedOrder(updated);
      await loadData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setActionError(message || "Failed to confirm sales order.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpdateStatus(orderId: string, nextStatus: string) {
    setActionError(null);
    setSubmitting(true);
    try {
      const updated = await apiClient.patch<SalesOrder>(`/sales-orders/${orderId}/status`, {
        status: nextStatus,
      });
      setSelectedOrder(updated);
      await loadData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setActionError(message || "Failed to update order status.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleGenerateInvoice(orderId: string) {
    setActionError(null);
    setGeneratingInvoice(true);
    try {
      await apiClient.post(`/sales-orders/${orderId}/invoice`);
      router.push("/admin/invoices");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setActionError(message || "Failed to generate invoice.");
    } finally {
      setGeneratingInvoice(false);
    }
  }

  function handlePrintPickList(orderId: string) {
    apiClient.downloadBlob(`/sales-orders/${orderId}/pick-list.pdf`, `pick-list-${orderId}.pdf`).catch(() => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      window.open(`${apiUrl}/sales-orders/${orderId}/pick-list.pdf`, "_blank");
    });
  }

  function handlePrintPackingSlip(orderId: string) {
    apiClient.downloadBlob(`/sales-orders/${orderId}/packing-slip.pdf`, `packing-slip-${orderId}.pdf`).catch(() => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      window.open(`${apiUrl}/sales-orders/${orderId}/packing-slip.pdf`, "_blank");
    });
  }

  function handlePrintSalesOrderPdf(orderId: string, soNumber: string) {
    apiClient.downloadBlob(`/sales-orders/${orderId}/pdf`, `${soNumber}.pdf`).catch(() => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      window.open(`${apiUrl}/sales-orders/${orderId}/pdf`, "_blank");
    });
  }

  async function handleOpenDetail(order: SalesOrder) {
    setSelectedOrder(order);
    setActionError(null);
    setSelectedOrderDelivery(null);
    setIsDetailModalOpen(true);
    try {
      const delivery = await apiClient.get<{
        id: string;
        status: string;
        driver_name?: string | null;
        vehicle_no?: string | null;
        notes?: string | null;
        dispatched_at?: string | null;
        delivered_at?: string | null;
      } | null>(`/sales-orders/${order.id}/delivery`);
      if (delivery && delivery.id && delivery.status) {
        setSelectedOrderDelivery(delivery);
      } else {
        setSelectedOrderDelivery(null);
      }
    } catch {
      setSelectedOrderDelivery(null);
    }
  }

  const columns: DataTableColumn<SalesOrder>[] = [
    {
      key: "so_number",
      header: "SO Number",
      render: (order) => (
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4 text-purple-400" />
          <div className="flex flex-col">
            <span className="font-mono text-xs font-semibold text-[var(--text)]">
              {order.so_number}
            </span>
            {order.has_unusual_items && (
              <span className="inline-flex items-center gap-1 text-[10px] text-amber-400 font-medium font-mono">
                <AlertTriangle className="w-3 h-3 text-amber-400" />
                Unusual Size ({order.unusual_items_count})
              </span>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "retailer_name",
      header: "Retailer / Buyer",
      render: (order) => (
        <div>
          <div className="font-medium text-xs text-[var(--text)]">
            {order.retailer_name || "Direct Customer"}
          </div>
          {order.retailer_pricing_tier && (
            <div className="flex items-center gap-1 mt-0.5">
              {order.retailer_pricing_tier === "gold" ? (
                <span className="inline-flex items-center gap-1 text-[10px] text-amber-400 font-mono">
                  <Crown className="w-3 h-3" /> Gold (10% off)
                </span>
              ) : order.retailer_pricing_tier === "silver" ? (
                <span className="inline-flex items-center gap-1 text-[10px] text-slate-300 font-mono">
                  <Sparkles className="w-3 h-3" /> Silver (5% off)
                </span>
              ) : (
                <span className="text-[10px] text-[var(--text-muted)] font-mono">
                  Standard
                </span>
              )}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "order_date",
      header: "Order Date",
      render: (order) => (
        <span className="text-xs text-[var(--text-muted)]">
          {new Date(order.order_date).toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          })}
        </span>
      ),
    },
    {
      key: "items",
      header: "Lines",
      render: (order) => (
        <span className="text-xs font-mono text-[var(--text)]">
          {order.items?.length || 0} items
        </span>
      ),
    },
    {
      key: "total_amount",
      header: "Total Amount",
      render: (order) => (
        <span className="font-mono text-xs font-bold text-emerald-400">
          ₹{Number(order.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (order) => {
        switch (order.status) {
          case "draft":
            return (
              <GlassBadge variant="neutral">
                <Clock className="w-3 h-3 mr-1" /> Draft
              </GlassBadge>
            );
          case "confirmed":
            return (
              <GlassBadge variant="accent">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Confirmed
              </GlassBadge>
            );
          case "packed":
            return (
              <GlassBadge variant="warning">
                <Package className="w-3 h-3 mr-1" /> Packed
              </GlassBadge>
            );
          case "shipped":
            return (
              <GlassBadge variant="accent">
                <Truck className="w-3 h-3 mr-1" /> Shipped
              </GlassBadge>
            );
          case "delivered":
            return (
              <GlassBadge variant="success">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Delivered
              </GlassBadge>
            );
          case "cancelled":
            return (
              <GlassBadge variant="error">
                <XCircle className="w-3 h-3 mr-1" /> Cancelled
              </GlassBadge>
            );
          default:
            return <GlassBadge variant="neutral">{order.status}</GlassBadge>;
        }

      },
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (order) => (
        <div className="flex items-center justify-end gap-1.5">
          <GlassButton
            variant="outline"
            size="sm"
            onClick={() => handlePrintSalesOrderPdf(order.id, order.so_number)}
            className="text-xs py-1 px-2.5 h-8 gap-1 border-sky-500/30 text-sky-300 hover:bg-sky-500/20"
            title="Export Sales Order Confirmation PDF"
          >
            <FileDown className="w-3.5 h-3.5" /> PDF
          </GlassButton>
          <GlassButton
            variant="ghost"
            size="sm"
            onClick={() => handleOpenDetail(order)}
            className="text-xs"
          >
            <Eye className="w-3.5 h-3.5 mr-1" /> Details
          </GlassButton>
        </div>
      ),
    },
  ];


  return (
    <AppLayout>
      <div className="space-y-6 pb-12">
        {/* KPI Header Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <GlassCard className="p-4">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-medium mb-1">
              <span>Total Orders</span>
              <ShoppingBag className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-[var(--text)]">
              {totalOrdersCount}
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-medium mb-1">
              <span>Draft Orders</span>
              <Clock className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-amber-400">
              {draftOrdersCount}
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-medium mb-1">
              <span>In Fulfillment</span>
              <Truck className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-blue-400">
              {inFulfillmentCount}
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-medium mb-1">
              <span>Total Revenue</span>
              <IndianRupee className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-emerald-400 font-mono">
              ₹{Math.round(totalRevenue).toLocaleString("en-IN")}
            </div>
          </GlassCard>
        </div>

        {/* List View Template with DataTable */}
        <ListViewTemplate
          title="Sales Orders & Dispatch"
          description="Manage wholesale B2B retailer sales orders, FIFO batch deductions, and fulfillment dispatch"
          searchPlaceholder="Search by SO number or retailer..."
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          primaryAction={
            <GlassButton
              variant="primary"
              onClick={() => {
                setActionError(null);
                setIsCreateModalOpen(true);
              }}
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Sales Order
            </GlassButton>
          }
        >
          {/* Status Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <button
              type="button"
              onClick={() => setStatusFilter("ALL")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === "ALL"
                  ? "bg-purple-600/30 text-purple-300 border border-purple-500/40"
                  : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent"
              }`}
            >
              All Orders ({totalOrdersCount})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("DRAFT")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === "DRAFT"
                  ? "bg-amber-600/30 text-amber-300 border border-amber-500/40"
                  : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent"
              }`}
            >
              Drafts ({draftOrdersCount})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("CONFIRMED")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === "CONFIRMED"
                  ? "bg-blue-600/30 text-blue-300 border border-blue-500/40"
                  : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent"
              }`}
            >
              In Fulfillment ({inFulfillmentCount})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("DELIVERED")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === "DELIVERED"
                  ? "bg-emerald-600/30 text-emerald-300 border border-emerald-500/40"
                  : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent"
              }`}
            >
              Delivered ({deliveredCount})
            </button>
          </div>

          <DataTable
            columns={columns}
            data={filteredOrders}
            keyExtractor={(order) => order.id}
            isLoading={loading}
            emptyTitle="No sales orders found"
            emptyDescription="No sales orders matching your filters."
          />
        </ListViewTemplate>

        {/* CREATE SALES ORDER MODAL */}

        <GlassModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title="Create New Sales Order"
        >
          <form onSubmit={handleCreateOrder} className="space-y-4">
            {actionError && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{actionError}</span>
              </div>
            )}

            {/* Buyer Type & Retailer Selector */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                  Buyer Type
                </label>
                <select
                  value={buyerType}
                  onChange={(e) => setBuyerType(e.target.value as "retailer" | "customer")}
                  className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                >
                  <option value="retailer">Wholesale Retailer</option>
                  <option value="customer">Direct Customer</option>
                </select>
              </div>

              {buyerType === "retailer" && (
                <div>
                  <label htmlFor="retailer-select" className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                    Select Retailer *
                  </label>
                  <select
                    id="retailer-select"
                    value={selectedRetailerId}
                    onChange={(e) => setSelectedRetailerId(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                  >
                    <option value="">-- Choose Retailer --</option>
                    {retailers.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name} ({r.pricing_tier.toUpperCase()} Tier)
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {buyerType === "customer" && (
                <div>
                  <label htmlFor="customer-select" className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                    Select Walk-In Customer
                  </label>
                  <select
                    id="customer-select"
                    value={selectedCustomerId}
                    onChange={(e) => setSelectedCustomerId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                  >
                    <option value="">-- Choose Walk-In Customer (Optional) --</option>
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} {c.phone ? `(${c.phone})` : ""}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* Direct Customer Info Banner */}
            {buyerType === "customer" && (
              <div className="p-3 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[var(--text)]">
                    {customers.find((c) => c.id === selectedCustomerId)?.name || "Direct Walk-In Buyer"}
                  </span>
                  <GlassBadge variant="success">STANDARD PRICING</GlassBadge>
                </div>
                <p className="text-[11px] text-[var(--text-muted)] pt-0.5">
                  Direct cash/UPI sale — skips credit limit verification, applies standard wholesale pricing, and deducts FIFO inventory immediately on confirmation.
                </p>
              </div>
            )}

            {/* Retailer Info & Credit Banner */}
            {buyerType === "retailer" && selectedRetailer && (
              <div className="p-3 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[var(--text)]">
                    {selectedRetailer.name}
                  </span>
                  <GlassBadge
                    variant={
                      selectedRetailer.pricing_tier === "gold"
                        ? "warning"
                        : selectedRetailer.pricing_tier === "silver"
                        ? "neutral"
                        : "neutral"
                    }
                  >
                    {selectedRetailer.pricing_tier.toUpperCase()} TIER
                  </GlassBadge>
                </div>
                <div className="flex items-center justify-between text-[var(--text-muted)] pt-1">
                  <span>
                    Credit Limit: ₹{Number(selectedRetailer.credit_limit).toLocaleString("en-IN")}
                  </span>
                  <span>
                    Used: ₹{Number(selectedRetailer.credit_balance).toLocaleString("en-IN")}
                  </span>
                  <span
                    className={
                      selectedRetailer.credit_limit - selectedRetailer.credit_balance <= 0
                        ? "text-red-400 font-bold"
                        : "text-emerald-400 font-medium"
                    }
                  >
                    Available: ₹
                    {Math.max(
                      0,
                      selectedRetailer.credit_limit - selectedRetailer.credit_balance
                    ).toLocaleString("en-IN")}
                  </span>
                </div>
              </div>
            )}


            {/* Line Items Builder */}
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider font-mono">
                  Order Items
                </span>
                <GlassButton
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleAddLine}
                  className="text-xs"
                >
                  <Plus className="w-3.5 h-3.5 mr-1" /> Add Product
                </GlassButton>
              </div>

              {computedLines.map((line, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-12 gap-2 items-center p-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)]"
                >
                  <div className="col-span-6">
                    <select
                      value={line.product_id}
                      onChange={(e) => handleLineChange(idx, "product_id", e.target.value)}
                      required
                      className="w-full px-2 py-1.5 rounded-lg bg-black/20 border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none"
                    >
                      <option value="">Select product...</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} (₹{p.wholesale_price})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-2">
                    <input
                      type="number"
                      min="1"
                      step="1"
                      value={line.qty}
                      onChange={(e) => handleLineChange(idx, "qty", Number(e.target.value))}
                      required
                      className="w-full px-2 py-1.5 rounded-lg bg-black/20 border border-[var(--glass-border)] text-xs text-center text-[var(--text)] focus:outline-none"
                      placeholder="Qty"
                    />
                  </div>
                  <div className="col-span-3 text-right">
                    <span className="text-xs font-mono font-bold text-emerald-400">
                      ₹{line.lineTotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </span>
                    <div className="text-[10px] text-[var(--text-muted)] font-mono">
                      @ ₹{line.unitPrice.toFixed(2)}
                    </div>
                  </div>
                  <div className="col-span-1 text-center">
                    {orderLines.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveLine(idx)}
                        className="text-red-400 hover:text-red-300 p-1"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Total Summary & Credit Warning */}
            <div className="p-3 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] flex items-center justify-between">
              <span className="text-xs font-medium text-[var(--text-muted)]">
                Estimated Total:
              </span>
              <span className="text-base font-bold font-mono text-emerald-400">
                ₹{estimatedOrderTotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </span>
            </div>

            {isCreditExceeded && (
              <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  Warning: This order total (₹{estimatedOrderTotal.toFixed(2)}) exceeds retailer available credit. Order will be created as Draft and confirmation will be blocked until credit is settled.
                </span>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <GlassButton
                type="button"
                variant="ghost"
                onClick={() => setIsCreateModalOpen(false)}
              >
                Cancel
              </GlassButton>
              <GlassButton type="submit" variant="primary" disabled={submitting}>
                {submitting ? "Creating..." : "Create Draft Order"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>

        {/* ORDER DETAILS & FULFILLMENT MODAL */}
        <GlassModal
          isOpen={isDetailModalOpen}
          onClose={() => setIsDetailModalOpen(false)}
          title={`Sales Order: ${selectedOrder?.so_number || ""}`}
        >
          {selectedOrder && (
            <div className="space-y-4">
              {actionError && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{actionError}</span>
                </div>
              )}

              {/* Order Metadata */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] text-xs">
                <div>
                  <span className="text-[var(--text-muted)] block">Retailer / Buyer</span>
                  <span className="font-semibold text-[var(--text)]">
                    {selectedOrder.retailer_name || "Direct Customer"}
                  </span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)] block">Status</span>
                  <span className="font-semibold uppercase tracking-wider text-purple-400 font-mono">
                    {selectedOrder.status}
                  </span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)] block">Order Date</span>
                  <span className="text-[var(--text)]">
                    {new Date(selectedOrder.order_date).toLocaleDateString("en-IN")}
                  </span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)] block">Total Amount</span>
                  <span className="font-bold text-emerald-400 font-mono text-sm">
                    ₹{Number(selectedOrder.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              {/* Delivery Dispatch Info Banner (if assigned) */}
              {selectedOrderDelivery && selectedOrderDelivery.status && (
                <div className="p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Truck className="w-4 h-4 text-indigo-400" />
                      <span className="font-semibold text-white">Delivery Dispatch Status</span>
                    </div>
                    <GlassBadge
                      variant={
                        selectedOrderDelivery.status === "delivered"
                          ? "success"
                          : selectedOrderDelivery.status === "out_for_delivery"
                          ? "warning"
                          : selectedOrderDelivery.status === "failed"
                          ? "error"
                          : "accent"
                      }
                    >
                      {String(selectedOrderDelivery.status).replace(/_/g, " ").toUpperCase()}
                    </GlassBadge>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px] text-slate-300 font-mono">
                    <div>Driver: <span className="text-white">{selectedOrderDelivery.driver_name || "—"}</span></div>
                    <div>Vehicle: <span className="text-white">{selectedOrderDelivery.vehicle_no || "—"}</span></div>
                    {selectedOrderDelivery.dispatched_at && (
                      <div>Dispatched: <span className="text-white">{new Date(selectedOrderDelivery.dispatched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></div>
                    )}
                    {selectedOrderDelivery.delivered_at && (
                      <div>Delivered: <span className="text-white">{new Date(selectedOrderDelivery.delivered_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></div>
                    )}
                  </div>
                  {selectedOrderDelivery.notes && (
                    <p className={`text-[11px] p-2 rounded-lg ${selectedOrderDelivery.status === "failed" ? "bg-rose-500/10 text-rose-300 border border-rose-500/20" : "bg-black/20 text-slate-300"}`}>
                      {selectedOrderDelivery.notes}
                    </p>
                  )}
                </div>
              )}

              {/* Statistical Anomaly Advisory Banner */}
              {selectedOrder.has_unusual_items && (
                <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-xs space-y-1.5 text-amber-300">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-semibold">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>Statistical Anomaly Advisory (3σ Threshold)</span>
                    </div>
                    <GlassBadge variant="warning">
                      {selectedOrder.unusual_items_count} UNUSUAL ITEM{selectedOrder.unusual_items_count === 1 ? "" : "S"}
                    </GlassBadge>
                  </div>
                  <p className="text-[11px] text-amber-200/80 leading-relaxed">
                    This order contains line items significantly exceeding historical buyer purchase volumes (&gt; 3σ standard deviation). This is an advisory alert for warehouse staff and does not block confirmation.
                  </p>
                  {selectedOrder.anomaly_warnings && selectedOrder.anomaly_warnings.length > 0 && (
                    <div className="pt-1 space-y-1">
                      {selectedOrder.anomaly_warnings.map((warn, i) => (
                        <div key={i} className="text-[11px] font-mono text-amber-400 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0"></span>
                          <span>{warn}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Line Items Table */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider font-mono">
                  Line Items ({selectedOrder.items?.length || 0})
                </span>
                <div className="rounded-xl overflow-hidden border border-[var(--glass-border)]">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-black/20 text-[var(--text-muted)] font-mono text-[10px] uppercase">
                      <tr>
                        <th className="p-2.5">Product</th>
                        <th className="p-2.5 text-center">SKU</th>
                        <th className="p-2.5 text-center">Qty</th>
                        <th className="p-2.5 text-right">Unit Price</th>
                        <th className="p-2.5 text-right">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--glass-border)] text-[var(--text)]">
                      {selectedOrder.items?.map((it) => (
                        <tr key={it.id} className="hover:bg-white/5">
                          <td className="p-2.5 font-medium">
                            <div className="flex items-center gap-2">
                              <span>{it.product_name || it.product_id}</span>
                              {it.is_unusual && (
                                <span
                                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                  title={it.anomaly_reason || "Unusual order quantity"}
                                >
                                  <AlertTriangle className="w-2.5 h-2.5" /> 3σ Anomaly
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="p-2.5 text-center font-mono text-[var(--text-muted)]">
                            {it.product_sku || "—"}
                          </td>
                          <td className="p-2.5 text-center font-mono font-semibold">{it.qty}</td>
                          <td className="p-2.5 text-right font-mono">₹{it.unit_price.toFixed(2)}</td>
                          <td className="p-2.5 text-right font-mono font-bold text-emerald-400">
                            ₹{(it.qty * it.unit_price).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Fulfillment State Machine Actions */}
              <div className="pt-3 border-t border-[var(--glass-border)] flex flex-wrap items-center justify-between gap-2">
                <div>
                  {selectedOrder.status === "draft" && (
                    <span className="text-[11px] text-[var(--text-muted)]">
                      Ready to confirm order and deduct FIFO stock batches.
                    </span>
                  )}
                  {selectedOrder.status === "confirmed" && (
                    <span className="text-[11px] text-emerald-400 font-medium">
                      Stock deducted FIFO. Ready for packing and warehouse dispatch.
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {/* Status Actions */}
                  {selectedOrder.status === "draft" && (
                    <>
                      <GlassButton
                        type="button"
                        variant="destructive"
                        size="sm"
                        disabled={submitting}
                        onClick={() => handleUpdateStatus(selectedOrder.id, "cancelled")}
                      >
                        Cancel Order
                      </GlassButton>
                      <GlassButton
                        type="button"
                        variant="primary"
                        size="sm"
                        disabled={submitting}
                        onClick={() => handleConfirmOrder(selectedOrder.id)}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Confirm Order (Deduct FIFO)
                      </GlassButton>
                    </>
                  )}

                  {selectedOrder.status === "confirmed" && (
                    <>
                      <GlassButton
                        type="button"
                        variant="destructive"
                        size="sm"
                        disabled={submitting}
                        onClick={() => handleUpdateStatus(selectedOrder.id, "cancelled")}
                      >
                        Cancel (Restore Stock)
                      </GlassButton>
                      <GlassButton
                        type="button"
                        variant="primary"
                        size="sm"
                        disabled={submitting}
                        onClick={() => handleUpdateStatus(selectedOrder.id, "packed")}
                      >
                        <Package className="w-3.5 h-3.5 mr-1" /> Mark Packed
                      </GlassButton>
                    </>
                  )}


                  {selectedOrder.status === "packed" && (
                    <GlassButton
                      type="button"
                      variant="primary"
                      size="sm"
                      disabled={submitting}
                      onClick={() => handleUpdateStatus(selectedOrder.id, "shipped")}
                    >
                      <Truck className="w-3.5 h-3.5 mr-1" /> Dispatch / Ship
                    </GlassButton>
                  )}

                  {selectedOrder.status === "delivered" && (
                    <div className="flex items-center gap-2">
                      <Link href={`/admin/sales-returns?sales_order_id=${selectedOrder.id}`}>
                        <GlassButton type="button" variant="secondary" size="sm">
                          <RotateCcw className="w-3.5 h-3.5 mr-1" /> Request RMA Return
                        </GlassButton>
                      </Link>
                    </div>
                  )}

                  {selectedOrder.status !== "cancelled" && (
                    <>
                      <GlassButton
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => handlePrintSalesOrderPdf(selectedOrder.id, selectedOrder.so_number)}
                      >
                        <FileDown className="w-3.5 h-3.5 mr-1 text-sky-400" /> Export PDF
                      </GlassButton>

                      <GlassButton
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => handlePrintPickList(selectedOrder.id)}
                      >
                        <Printer className="w-3.5 h-3.5 mr-1 text-indigo-400" /> Print Pick List
                      </GlassButton>

                      <GlassButton
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => handlePrintPackingSlip(selectedOrder.id)}
                      >
                        <FileSpreadsheet className="w-3.5 h-3.5 mr-1 text-emerald-400" /> Print Packing Slip
                      </GlassButton>
                    </>
                  )}

                  {selectedOrder.status !== "draft" && selectedOrder.status !== "cancelled" && (
                    <GlassButton
                      type="button"
                      variant="secondary"
                      size="sm"
                      disabled={generatingInvoice}
                      onClick={() => handleGenerateInvoice(selectedOrder.id)}
                    >
                      <FileText className="w-3.5 h-3.5 mr-1 text-purple-400" />
                      {generatingInvoice ? "Generating..." : "Generate / View Invoice"}
                    </GlassButton>
                  )}
                </div>

              </div>
            </div>
          )}
        </GlassModal>

      </div>
    </AppLayout>
  );
}

