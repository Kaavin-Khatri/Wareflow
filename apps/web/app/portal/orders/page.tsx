"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { auth } from "@/lib/firebase-client";
import { onAuthStateChanged } from "firebase/auth";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassModal } from "@/components/glass/GlassModal";
import {
  ClipboardList,
  Search,
  CheckCircle2,
  Truck,
  Eye,
  Package,
  AlertCircle,
} from "lucide-react";

interface OrderSummary {
  id: string;
  so_number: string;
  status: string;
  order_date: string | null;
  total_amount: number;
  items_count: number;
  created_at: string | null;
}

interface OrderItemDetail {
  id: string;
  product_id: string;
  product_name?: string;
  sku?: string;
  qty: number;
  unit_price: number;
  tax_rate?: number;
  uom?: string;
}

interface OrderDetailResponse {
  id: string;
  so_number: string;
  status: string;
  total_amount: number;
  order_date: string | null;
  created_at: string;
  items: OrderItemDetail[];
}

export default function PortalOrdersPage() {
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Selected Order for Detail Modal
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [detailOrder, setDetailOrder] = useState<OrderDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchOrders = async () => {
    const user = auth.currentUser;
    if (!user) return;
    try {
      setLoading(true);
      const idToken = await user.getIdToken();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/portal/orders`, {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setOrders(data);
      } else {
        setError("Failed to load your orders.");
      }
    } catch (err) {
      console.warn("Orders fetch error:", err);
      setError("Network error fetching orders.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        fetchOrders();
      } else {
        setLoading(false);
      }
    });

    return () => unsubscribe();
  }, []);

  const openOrderDetail = async (orderId: string) => {
    setSelectedOrderId(orderId);
    setDetailOrder(null);
    setDetailLoading(true);

    try {
      const user = auth.currentUser;
      if (!user) return;
      const idToken = await user.getIdToken();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/portal/orders/${orderId}`, {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDetailOrder(data);
      }
    } catch (err) {
      console.error("Order detail fetch error:", err);
    } finally {
      setDetailLoading(false);
    }
  };

  const filteredOrders = orders.filter((o) => {
    if (search.trim()) {
      const q = search.toLowerCase();
      if (!o.so_number.toLowerCase().includes(q)) return false;
    }
    if (statusFilter !== "all" && o.status.toLowerCase() !== statusFilter.toLowerCase()) {
      return false;
    }
    return true;
  });

  const getStatusVariant = (statusStr: string): "success" | "error" | "neutral" | "warning" => {
    switch (statusStr.toLowerCase()) {
      case "confirmed":
        return "success";
      case "packed":
      case "shipped":
        return "warning";
      case "delivered":
        return "success";
      case "draft":
        return "neutral";
      case "cancelled":
        return "error";
      default:
        return "neutral";
    }
  };

  const totalValue = orders.reduce((sum, o) => sum + o.total_amount, 0);
  const activeFulfillments = orders.filter((o) =>
    ["confirmed", "packed", "shipped"].includes(o.status.toLowerCase())
  ).length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            My Sales Orders
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Track and inspect wholesale orders placed directly with your distributor.
          </p>
        </div>

        <Link href="/portal/catalog">
          <GlassButton variant="primary" className="flex items-center gap-2">
            <Package className="w-4 h-4" />
            <span>Place New Order</span>
          </GlassButton>
        </Link>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <GlassCard className="p-4 flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <ClipboardList className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Total Orders Placed</p>
            <h3 className="text-xl font-bold text-white">{orders.length}</h3>
          </div>
        </GlassCard>

        <GlassCard className="p-4 flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <Truck className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Active In-Flight</p>
            <h3 className="text-xl font-bold text-amber-300">{activeFulfillments} Processing</h3>
          </div>
        </GlassCard>

        <GlassCard className="p-4 flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Cumulative Order Value</p>
            <h3 className="text-xl font-bold font-mono text-emerald-300">
              ₹{totalValue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </h3>
          </div>
        </GlassCard>
      </div>

      {/* Filter Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by SO number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {["all", "draft", "confirmed", "shipped", "delivered"].map((tab) => (
            <button
              key={tab}
              onClick={() => setStatusFilter(tab)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
                statusFilter === tab
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "bg-white/5 hover:bg-white/10 text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center p-16">
          <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
        </div>
      ) : filteredOrders.length === 0 ? (
        <GlassCard className="p-12 text-center space-y-4">
          <div className="w-16 h-16 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
            <ClipboardList className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">No Orders Found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              {orders.length === 0
                ? "You haven't placed any wholesale sales orders yet."
                : "No orders match your active filter."}
            </p>
          </div>
          {orders.length === 0 && (
            <div className="pt-2">
              <Link href="/portal/catalog">
                <GlassButton variant="primary">Browse Catalog</GlassButton>
              </Link>
            </div>
          )}
        </GlassCard>
      ) : (
        <div className="overflow-hidden rounded-3xl border border-white/10 bg-slate-900/60 backdrop-blur-xl">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-white/10 bg-white/5 text-[11px] uppercase tracking-wider font-semibold text-slate-400">
              <tr>
                <th className="px-6 py-4">SO Number</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Items Count</th>
                <th className="px-6 py-4">Total Amount</th>
                <th className="px-6 py-4">Placed Date</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredOrders.map((o) => (
                <tr key={o.id} className="hover:bg-white/5 transition-colors">
                  <td className="px-6 py-4 font-mono font-bold text-white">{o.so_number}</td>
                  <td className="px-6 py-4">
                    <GlassBadge variant={getStatusVariant(o.status)}>
                      {o.status.toUpperCase()}
                    </GlassBadge>
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-300">
                    {o.items_count > 0 ? `${o.items_count} products` : "Wholesale order"}
                  </td>
                  <td className="px-6 py-4 font-mono font-bold text-emerald-400">
                    ₹{o.total_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-400">
                    {o.created_at || o.order_date
                      ? new Date(o.created_at || o.order_date!).toLocaleDateString("en-IN", {
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                        })
                      : "Recent"}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => openOrderDetail(o.id)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-indigo-300 hover:text-white border border-white/10 text-xs font-medium transition-all"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>View Items</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Order Detail Modal */}
      {selectedOrderId && (
        <GlassModal
          isOpen={!!selectedOrderId}
          onClose={() => setSelectedOrderId(null)}
          title={`Order Details: ${detailOrder?.so_number || "Loading..."}`}
          maxWidth="2xl"
        >
          {detailLoading || !detailOrder ? (
            <div className="flex items-center justify-center p-12">
              <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
            </div>
          ) : (
            <div className="space-y-5">
              {/* Order Status Bar */}
              <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/10 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 block">Fulfillment Status</span>
                  <span className="text-base font-bold text-white uppercase tracking-wide">
                    {detailOrder.status}
                  </span>
                </div>
                <GlassBadge variant={getStatusVariant(detailOrder.status)}>
                  {detailOrder.status.toUpperCase()}
                </GlassBadge>
              </div>

              {/* Items Table */}
              <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/40">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="border-b border-white/10 bg-white/5 uppercase text-[10px] font-semibold text-slate-400">
                    <tr>
                      <th className="px-4 py-3">Product / SKU</th>
                      <th className="px-4 py-3 text-right">Quantity</th>
                      <th className="px-4 py-3 text-right">Unit Rate</th>
                      <th className="px-4 py-3 text-right">Line Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {detailOrder.items.map((it, idx) => {
                      const lineTotal = it.qty * it.unit_price;
                      return (
                        <tr key={it.id || idx}>
                          <td className="px-4 py-3 font-medium text-white">
                            {it.product_name || `Product ID: ${it.product_id.slice(0, 8)}`}
                          </td>
                          <td className="px-4 py-3 text-right font-mono">{it.qty}</td>
                          <td className="px-4 py-3 text-right font-mono">
                            ₹{it.unit_price.toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-right font-mono font-bold text-emerald-400">
                            ₹{lineTotal.toFixed(2)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Total Summary */}
              <div className="flex justify-between items-center p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
                <span className="text-xs font-semibold text-indigo-300">Order Total Amount</span>
                <span className="text-lg font-bold font-mono text-emerald-300">
                  ₹{detailOrder.total_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          )}
        </GlassModal>
      )}
    </div>
  );
}
