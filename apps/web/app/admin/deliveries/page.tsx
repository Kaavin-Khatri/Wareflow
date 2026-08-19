"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import AppLayout from "@/components/AppLayout";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassModal } from "@/components/glass/GlassModal";
import { apiClient } from "@/lib/api-client";
import {
  Truck,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Search,
  Plus,
  RefreshCw,
  MapPin,
  User,
  RotateCcw,
  Send,
  XCircle,
} from "lucide-react";

export interface DeliveryItem {
  id: string;
  sales_order_id: string;
  so_number?: string | null;
  buyer_name?: string | null;
  destination_address?: string | null;
  driver_name?: string | null;
  vehicle_no?: string | null;
  status: "assigned" | "out_for_delivery" | "delivered" | "failed";
  total_amount?: number | null;
  dispatched_at?: string | null;
  delivered_at?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface PackedSalesOrder {
  id: string;
  so_number: string;
  buyer_name?: string | null;
  retailer_name?: string | null;
  total_amount: number;
  status: string;
}

export default function DeliveriesPage() {
  const [deliveries, setDeliveries] = useState<DeliveryItem[]>([]);
  const [packedOrders, setPackedOrders] = useState<PackedSalesOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [driverFilter, setDriverFilter] = useState("");
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Assign Modal State
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState("");
  const [driverName, setDriverName] = useState("");
  const [vehicleNo, setVehicleNo] = useState("");
  const [assignNotes, setAssignNotes] = useState("");
  const [submittingAssign, setSubmittingAssign] = useState(false);
  const [assignError, setAssignError] = useState<string | null>(null);

  // Fail Modal State
  const [failModalDelivery, setFailModalDelivery] = useState<DeliveryItem | null>(null);
  const [failReason, setFailReason] = useState("");
  const [submittingFail, setSubmittingFail] = useState(false);
  const [failError, setFailError] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const fetchDeliveries = useCallback(async () => {
    try {
      const data = await apiClient.get<DeliveryItem[]>("/deliveries");
      setDeliveries(data || []);
    } catch (err) {
      console.error("Failed to fetch deliveries:", err);
    }
  }, []);

  const fetchPackedOrders = useCallback(async () => {
    try {
      const orders = await apiClient.get<PackedSalesOrder[]>("/sales-orders?status=packed");
      setPackedOrders(orders || []);
    } catch (err) {
      console.error("Failed to fetch packed orders:", err);
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    async function load() {
      try {
        setLoading(true);
        const [dData, pData] = await Promise.all([
          apiClient.get<DeliveryItem[]>("/deliveries"),
          apiClient.get<PackedSalesOrder[]>("/sales-orders?status=packed").catch(() => []),
        ]);
        if (!ignore) {
          setDeliveries(dData || []);
          setPackedOrders(pData || []);
        }
      } catch (err) {
        console.error("Failed to load deliveries:", err);
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      ignore = true;
    };
  }, []);

  // Unique driver names for filter
  const driverOptions = useMemo(() => {
    const drivers = new Set<string>();
    deliveries.forEach((d) => {
      if (d.driver_name) drivers.add(d.driver_name);
    });
    return Array.from(drivers).sort();
  }, [deliveries]);

  // Filtered deliveries
  const filteredDeliveries = useMemo(() => {
    return deliveries.filter((d) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        (d.so_number && d.so_number.toLowerCase().includes(q)) ||
        (d.buyer_name && d.buyer_name.toLowerCase().includes(q)) ||
        (d.driver_name && d.driver_name.toLowerCase().includes(q)) ||
        (d.vehicle_no && d.vehicle_no.toLowerCase().includes(q));

      const matchesDriver = !driverFilter || d.driver_name === driverFilter;
      return matchesSearch && matchesDriver;
    });
  }, [deliveries, searchQuery, driverFilter]);

  // Status columns
  const assignedList = useMemo(
    () => filteredDeliveries.filter((d) => d.status === "assigned"),
    [filteredDeliveries]
  );
  const outForDeliveryList = useMemo(
    () => filteredDeliveries.filter((d) => d.status === "out_for_delivery"),
    [filteredDeliveries]
  );
  const deliveredList = useMemo(
    () => filteredDeliveries.filter((d) => d.status === "delivered"),
    [filteredDeliveries]
  );
  const failedList = useMemo(
    () => filteredDeliveries.filter((d) => d.status === "failed"),
    [filteredDeliveries]
  );

  // Status Transition Action
  const handleUpdateStatus = async (
    deliveryId: string,
    newStatus: "assigned" | "out_for_delivery" | "delivered" | "failed",
    notes?: string
  ) => {
    try {
      await apiClient.patch<DeliveryItem>(`/deliveries/${deliveryId}/status`, {
        status: newStatus,
        notes: notes || undefined,
      });

      showToast(`Delivery status updated to ${newStatus.replace(/_/g, " ").toUpperCase()}`);
      fetchDeliveries();
      fetchPackedOrders();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update delivery status";
      showToast(msg);
    }
  };

  // Submit Assign Form
  const handleAssignDelivery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrderId || !driverName.trim() || !vehicleNo.trim()) {
      setAssignError("Please select a sales order and enter driver name and vehicle number.");
      return;
    }

    try {
      setSubmittingAssign(true);
      setAssignError(null);

      await apiClient.post<DeliveryItem>(`/sales-orders/${selectedOrderId}/delivery`, {
        driver_name: driverName.trim(),
        vehicle_no: vehicleNo.trim(),
        notes: assignNotes.trim() || undefined,
      });

      showToast("Driver & vehicle assigned successfully! Order dispatched.");
      setIsAssignModalOpen(false);
      setSelectedOrderId("");
      setDriverName("");
      setVehicleNo("");
      setAssignNotes("");
      fetchDeliveries();
      fetchPackedOrders();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to assign delivery";
      setAssignError(msg);
    } finally {
      setSubmittingAssign(false);
    }
  };

  // Submit Fail Reason Form
  const handleFailDelivery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!failModalDelivery) return;
    if (!failReason.trim()) {
      setFailError("Please provide a reason why the delivery could not be completed.");
      return;
    }

    try {
      setSubmittingFail(true);
      setFailError(null);

      await apiClient.patch<DeliveryItem>(`/deliveries/${failModalDelivery.id}/status`, {
        status: "failed",
        notes: failReason.trim(),
      });

      showToast("Delivery marked as failed with recorded notes. Operations notified.");
      setFailModalDelivery(null);
      setFailReason("");
      fetchDeliveries();
      fetchPackedOrders();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to record delivery failure";
      setFailError(msg);
    } finally {
      setSubmittingFail(false);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Toast Feedback */}
        {toastMessage && (
          <div className="fixed bottom-6 right-6 z-50 px-4 py-3 rounded-2xl bg-indigo-950/90 border border-indigo-500/30 text-indigo-200 text-sm font-medium shadow-2xl backdrop-blur-xl animate-fade-in flex items-center gap-2">
            <span>✓</span>
            <span>{toastMessage}</span>
          </div>
        )}

        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                Delivery & Logistics Board
              </h1>
              <GlassBadge variant="accent">Phase 12</GlassBadge>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Assign drivers and vehicles to packed orders, track live transit across fulfillment stages, and monitor delivery completions.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => {
                fetchDeliveries();
                fetchPackedOrders();
              }}
            >
              <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh
            </GlassButton>
            <GlassButton
              variant="primary"
              size="sm"
              onClick={() => {
                setIsAssignModalOpen(true);
                setAssignError(null);
              }}
            >
              <Plus className="w-4 h-4 mr-1.5" /> Assign Delivery
            </GlassButton>
          </div>
        </div>

        {/* KPI Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard className="p-4 flex items-center gap-3.5">
            <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Assigned / Queued</p>
              <p className="text-xl font-bold text-white mt-0.5">{assignedList.length}</p>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-3.5">
            <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Out for Delivery</p>
              <p className="text-xl font-bold text-amber-400 mt-0.5">{outForDeliveryList.length}</p>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-3.5">
            <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Delivered</p>
              <p className="text-xl font-bold text-emerald-400 mt-0.5">{deliveredList.length}</p>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-3.5">
            <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Delivery Exceptions</p>
              <p className="text-xl font-bold text-rose-400 mt-0.5">{failedList.length}</p>
            </div>
          </GlassCard>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by SO number, buyer, driver, or vehicle..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white text-xs placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all"
            />
          </div>

          <select
            value={driverFilter}
            onChange={(e) => setDriverFilter(e.target.value)}
            className="w-full sm:w-56 px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
          >
            <option value="">All Drivers</option>
            {driverOptions.map((d) => (
              <option key={d} value={d}>
                Driver: {d}
              </option>
            ))}
          </select>
        </div>

        {/* Kanban Board Columns */}
        {loading ? (
          <div className="p-16 flex items-center justify-center">
            <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5 items-start">
            {/* Column 1: Assigned */}
            <div className="space-y-3 bg-white/[0.02] p-3.5 rounded-3xl border border-white/10">
              <div className="flex items-center justify-between px-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 shadow-sm" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Assigned ({assignedList.length})
                  </h3>
                </div>
                <GlassBadge variant="neutral">Ready</GlassBadge>
              </div>

              <div className="space-y-3 min-h-[220px]">
                {assignedList.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500 border border-dashed border-white/10 rounded-2xl">
                    No orders in queue
                  </div>
                ) : (
                  assignedList.map((item) => (
                    <DeliveryCard
                      key={item.id}
                      item={item}
                      onOutForDelivery={() => handleUpdateStatus(item.id, "out_for_delivery")}
                    />
                  ))
                )}
              </div>
            </div>

            {/* Column 2: Out for Delivery */}
            <div className="space-y-3 bg-white/[0.02] p-3.5 rounded-3xl border border-white/10">
              <div className="flex items-center justify-between px-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-sm animate-pulse" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    In Transit ({outForDeliveryList.length})
                  </h3>
                </div>
                <GlassBadge variant="warning">On Road</GlassBadge>
              </div>

              <div className="space-y-3 min-h-[220px]">
                {outForDeliveryList.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500 border border-dashed border-white/10 rounded-2xl">
                    No active dispatches
                  </div>
                ) : (
                  outForDeliveryList.map((item) => (
                    <DeliveryCard
                      key={item.id}
                      item={item}
                      onDelivered={() => handleUpdateStatus(item.id, "delivered")}
                      onFailed={() => {
                        setFailModalDelivery(item);
                        setFailReason("");
                        setFailError(null);
                      }}
                    />
                  ))
                )}
              </div>
            </div>

            {/* Column 3: Delivered */}
            <div className="space-y-3 bg-white/[0.02] p-3.5 rounded-3xl border border-white/10">
              <div className="flex items-center justify-between px-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Delivered ({deliveredList.length})
                  </h3>
                </div>
                <GlassBadge variant="success">Completed</GlassBadge>
              </div>

              <div className="space-y-3 min-h-[220px]">
                {deliveredList.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500 border border-dashed border-white/10 rounded-2xl">
                    No completed deliveries
                  </div>
                ) : (
                  deliveredList.map((item) => <DeliveryCard key={item.id} item={item} />)
                )}
              </div>
            </div>

            {/* Column 4: Exceptions / Failed */}
            <div className="space-y-3 bg-white/[0.02] p-3.5 rounded-3xl border border-white/10">
              <div className="flex items-center justify-between px-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-400 shadow-sm" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Exceptions ({failedList.length})
                  </h3>
                </div>
                <GlassBadge variant="error">Action Req</GlassBadge>
              </div>

              <div className="space-y-3 min-h-[220px]">
                {failedList.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500 border border-dashed border-white/10 rounded-2xl">
                    No failed deliveries
                  </div>
                ) : (
                  failedList.map((item) => (
                    <DeliveryCard
                      key={item.id}
                      item={item}
                      onReschedule={() => {
                        setSelectedOrderId(item.sales_order_id);
                        setDriverName(item.driver_name || "");
                        setVehicleNo(item.vehicle_no || "");
                        setAssignNotes(item.notes || "");
                        setIsAssignModalOpen(true);
                      }}
                    />
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Assign Delivery Modal */}
        <GlassModal
          isOpen={isAssignModalOpen}
          onClose={() => setIsAssignModalOpen(false)}
          title="Assign Driver & Vehicle to Sales Order"
          maxWidth="lg"
        >
          <form onSubmit={handleAssignDelivery} className="space-y-4">
            {assignError && (
              <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{assignError}</span>
              </div>
            )}

            <div>
              <label htmlFor="so-select" className="block text-xs font-semibold text-slate-300 mb-1.5">
                Select Packed Sales Order *
              </label>
              <select
                id="so-select"
                value={selectedOrderId}
                onChange={(e) => setSelectedOrderId(e.target.value)}
                required
                className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-white text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
              >
                <option value="">-- Choose Packed Sales Order --</option>
                {packedOrders.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.so_number} - {o.buyer_name || o.retailer_name || "Buyer"} (₹
                    {o.total_amount?.toLocaleString("en-IN")})
                  </option>
                ))}
              </select>
              {packedOrders.length === 0 && (
                <p className="text-[11px] text-amber-400 mt-1">
                  No orders currently in &quot;packed&quot; status. Pack an order in Orders & Dispatch first.
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label htmlFor="driver-input" className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Driver Name *
                </label>
                <input
                  id="driver-input"
                  type="text"
                  placeholder="e.g. Ramesh Kumar"
                  value={driverName}
                  onChange={(e) => setDriverName(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                />
              </div>

              <div>
                <label htmlFor="vehicle-input" className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Vehicle Registration No. *
                </label>
                <input
                  id="vehicle-input"
                  type="text"
                  placeholder="e.g. MH-02-AB-1234"
                  value={vehicleNo}
                  onChange={(e) => setVehicleNo(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white text-xs font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                />
              </div>
            </div>

            <div>
              <label htmlFor="notes-input" className="block text-xs font-semibold text-slate-300 mb-1.5">
                Dispatch Instructions / Special Notes
              </label>
              <textarea
                id="notes-input"
                rows={2}
                placeholder="Gate delivery timing, fragile handling instructions..."
                value={assignNotes}
                onChange={(e) => setAssignNotes(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/40 resize-none"
              />
            </div>

            <div className="pt-2 flex items-center justify-end gap-2.5">
              <GlassButton
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setIsAssignModalOpen(false)}
              >
                Cancel
              </GlassButton>
              <GlassButton
                type="submit"
                variant="primary"
                size="sm"
                disabled={submittingAssign}
              >
                {submittingAssign ? "Dispatching..." : "Confirm & Dispatch"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>

        {/* Fail Reason Modal */}
        <GlassModal
          isOpen={!!failModalDelivery}
          onClose={() => setFailModalDelivery(null)}
          title={`Record Delivery Failure: ${failModalDelivery?.so_number || ""}`}
          maxWidth="md"
        >
          <form onSubmit={handleFailDelivery} className="space-y-4">
            {failError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {failError}
              </div>
            )}

            <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>
                Failing this delivery attempt keeps the sales order in <strong>shipped</strong> status without marking it completed. A clear reason is required for warehouse ops.
              </span>
            </div>

            <div>
              <label htmlFor="fail-reason" className="block text-xs font-semibold text-slate-300 mb-1.5">
                Reason for Delivery Failure *
              </label>
              <textarea
                id="fail-reason"
                rows={3}
                required
                placeholder="e.g. Retailer store closed for festival holiday, reschedule for tomorrow morning..."
                value={failReason}
                onChange={(e) => setFailReason(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white text-xs focus:outline-none focus:ring-2 focus:ring-rose-500/40 resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2.5">
              <GlassButton
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setFailModalDelivery(null)}
              >
                Cancel
              </GlassButton>
              <GlassButton
                type="submit"
                variant="destructive"
                size="sm"
                disabled={submittingFail}
              >
                {submittingFail ? "Recording..." : "Record Failure"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>
      </div>
    </AppLayout>
  );
}

interface DeliveryCardProps {
  item: DeliveryItem;
  onOutForDelivery?: () => void;
  onDelivered?: () => void;
  onFailed?: () => void;
  onReschedule?: () => void;
}

function DeliveryCard({
  item,
  onOutForDelivery,
  onDelivered,
  onFailed,
  onReschedule,
}: DeliveryCardProps) {
  return (
    <GlassCard className="p-4 space-y-3 hover:border-white/20 transition-all">
      {/* Top row: SO Number & Amount */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="font-mono text-xs font-bold text-white tracking-wide">
            {item.so_number || "SO-ORDER"}
          </span>
          <p className="text-[11px] font-semibold text-slate-300 line-clamp-1 mt-0.5">
            {item.buyer_name || "Wholesale Buyer"}
          </p>
        </div>
        {item.total_amount != null && (
          <span className="font-mono text-xs font-semibold text-emerald-400">
            ₹{item.total_amount.toLocaleString("en-IN")}
          </span>
        )}
      </div>

      {/* Driver & Vehicle */}
      <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 bg-white/[0.03] p-2.5 rounded-xl border border-white/5">
        <div className="flex items-center gap-1.5">
          <User className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          <span className="truncate text-slate-200">{item.driver_name || "Unassigned"}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Truck className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          <span className="truncate font-mono text-slate-200">{item.vehicle_no || "—"}</span>
        </div>
      </div>

      {/* Destination address if available */}
      {item.destination_address && (
        <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
          <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
          <span className="truncate">{item.destination_address}</span>
        </div>
      )}

      {/* Timestamps */}
      <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
        {item.delivered_at ? (
          <span>Delivered: {new Date(item.delivered_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
        ) : item.dispatched_at ? (
          <span>Dispatched: {new Date(item.dispatched_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
        ) : (
          <span>Assigned: {new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
        )}
      </div>

      {/* Notes / Failure reason */}
      {item.notes && (
        <p className={`text-[11px] p-2 rounded-lg ${item.status === "failed" ? "bg-rose-500/10 text-rose-300 border border-rose-500/20" : "bg-white/5 text-slate-400"}`}>
          {item.notes}
        </p>
      )}

      {/* Kanban Action Buttons */}
      <div className="pt-2 border-t border-white/10 flex items-center gap-2">
        {item.status === "assigned" && onOutForDelivery && (
          <GlassButton
            type="button"
            variant="primary"
            size="sm"
            className="w-full justify-center"
            onClick={onOutForDelivery}
          >
            <Send className="w-3 h-3 mr-1" /> Start Delivery
          </GlassButton>
        )}

        {item.status === "out_for_delivery" && (
          <>
            {onDelivered && (
              <GlassButton
                type="button"
                variant="primary"
                size="sm"
                className="flex-1 justify-center bg-emerald-600 hover:bg-emerald-500"
                onClick={onDelivered}
              >
                <CheckCircle2 className="w-3 h-3 mr-1" /> Delivered
              </GlassButton>
            )}
            {onFailed && (
              <GlassButton
                type="button"
                variant="destructive"
                size="sm"
                className="flex-1 justify-center"
                onClick={onFailed}
              >
                <XCircle className="w-3 h-3 mr-1" /> Failed
              </GlassButton>
            )}
          </>
        )}

        {item.status === "failed" && onReschedule && (
          <GlassButton
            type="button"
            variant="secondary"
            size="sm"
            className="w-full justify-center"
            onClick={onReschedule}
          >
            <RotateCcw className="w-3 h-3 mr-1" /> Reschedule / Reassign
          </GlassButton>
        )}
      </div>
    </GlassCard>
  );
}
