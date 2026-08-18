"use client";

import React, { useState, useEffect, useMemo } from "react";
import { ListViewTemplate } from "@/components/templates/ListViewTemplate";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassModal } from "@/components/glass/GlassModal";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { apiClient } from "@/lib/api-client";
import {
  Users,
  UserPlus,
  ShoppingBag,
  IndianRupee,
  Phone,
  Mail,
  MapPin,
  Edit2,
  Trash2,
  AlertCircle,
  Eye,
  CheckCircle2,
} from "lucide-react";

export interface Customer {
  id: string;
  name: string;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  notes?: string | null;
  created_at: string;
  total_orders_count?: number;
  total_spend?: number;
}

const MOCK_CUSTOMERS: Customer[] = [
  {
    id: "cust-1",
    name: "Ramesh Gupta",
    phone: "+91 98765 43210",
    email: "ramesh.gupta@gmail.com",
    address: "Shop 4, Chandni Chowk, Delhi - 110006",
    notes: "Walk-in cash buyer for bulk spices and pulses",
    created_at: new Date(Date.now() - 86400000 * 15).toISOString(),
    total_orders_count: 3,
    total_spend: 14500,
  },
  {
    id: "cust-2",
    name: "Sunita Sharma",
    phone: "+91 98112 23344",
    email: "sunita.sharma@yahoo.com",
    address: "B-42, Sector 18, Noida, UP",
    notes: "Regular retail walk-in for organic flour & grains",
    created_at: new Date(Date.now() - 86400000 * 8).toISOString(),
    total_orders_count: 2,
    total_spend: 8200,
  },
  {
    id: "cust-3",
    name: "Anil Verma",
    phone: "+91 99887 76655",
    email: "anil.verma@outlook.com",
    address: "Plot 12, Indirapuram, Ghaziabad",
    notes: "Instant UPI settlement",
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    total_orders_count: 1,
    total_spend: 3500,
  },
];

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Modal States
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    email: "",
    address: "",
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      try {
        setLoading(true);
        const res = await apiClient.get<Customer[]>("/customers");
        if (!isMounted) return;
        if (res && Array.isArray(res)) {
          setCustomers(res);
        } else {
          setCustomers(MOCK_CUSTOMERS);
        }
      } catch {
        if (isMounted) setCustomers(MOCK_CUSTOMERS);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadData();
    return () => {
      isMounted = false;
    };
  }, []);


  // Filtered list
  const filteredCustomers = useMemo(() => {
    return customers.filter((c) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        c.name.toLowerCase().includes(q) ||
        (c.phone && c.phone.toLowerCase().includes(q)) ||
        (c.email && c.email.toLowerCase().includes(q)) ||
        (c.notes && c.notes.toLowerCase().includes(q)) ||
        (c.address && c.address.toLowerCase().includes(q))
      );
    });
  }, [customers, searchQuery]);

  // KPI Metrics
  const metrics = useMemo(() => {
    const totalCount = customers.length;
    const activeBuyers = customers.filter((c) => (c.total_orders_count || 0) > 0).length;
    const totalOrders = customers.reduce((sum, c) => sum + (c.total_orders_count || 0), 0);
    const totalRevenue = customers.reduce((sum, c) => sum + (c.total_spend || 0), 0);

    return { totalCount, activeBuyers, totalOrders, totalRevenue };
  }, [customers]);

  const openCreateModal = () => {
    setFormData({ name: "", phone: "", email: "", address: "", notes: "" });
    setErrorMessage(null);
    setIsCreateOpen(true);
  };

  const openEditModal = (c: Customer) => {
    setSelectedCustomer(c);
    setFormData({
      name: c.name,
      phone: c.phone || "",
      email: c.email || "",
      address: c.address || "",
      notes: c.notes || "",
    });
    setErrorMessage(null);
    setIsEditOpen(true);
  };

  const openDetailModal = (c: Customer) => {
    setSelectedCustomer(c);
    setIsDetailOpen(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSubmitting(true);
    try {
      const payload = {
        name: formData.name.trim(),
        phone: formData.phone.trim() || undefined,
        email: formData.email.trim() || undefined,
        address: formData.address.trim() || undefined,
        notes: formData.notes.trim() || undefined,
      };

      const res = await apiClient.post<Customer>("/customers", payload);
      if (res && res.id) {
        setCustomers((prev) => [res, ...prev]);
        setIsCreateOpen(false);
        setSuccessMessage("Customer registered successfully.");
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
          ? String((err as { message: unknown }).message)
          : "Failed to register customer.";
      setErrorMessage(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomer) return;
    setErrorMessage(null);
    setSubmitting(true);
    try {
      const payload = {
        name: formData.name.trim(),
        phone: formData.phone.trim() || undefined,
        email: formData.email.trim() || undefined,
        address: formData.address.trim() || undefined,
        notes: formData.notes.trim() || undefined,
      };

      const res = await apiClient.patch<Customer>(`/customers/${selectedCustomer.id}`, payload);
      if (res && res.id) {
        setCustomers((prev) => prev.map((c) => (c.id === res.id ? { ...c, ...res } : c)));
        setIsEditOpen(false);
        setSuccessMessage("Customer profile updated successfully.");
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
          ? String((err as { message: unknown }).message)
          : "Failed to update customer.";
      setErrorMessage(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (customer: Customer) => {
    if (
      !window.confirm(
        `Are you sure you want to delete customer "${customer.name}"? This action cannot be undone.`
      )
    ) {
      return;
    }
    try {
      await apiClient.delete(`/customers/${customer.id}`);
      setCustomers((prev) => prev.filter((c) => c.id !== customer.id));
      setSuccessMessage("Customer deleted successfully.");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
          ? String((err as { message: unknown }).message)
          : "Cannot delete customer with active order history.";
      alert(errorMsg);
    }
  };

  const columns: DataTableColumn<Customer>[] = [
    {
      key: "name",
      header: "Customer",
      sortable: true,
      render: (c) => (
        <div className="flex flex-col">
          <span className="font-semibold text-[var(--text)]">{c.name}</span>
          {c.notes && (
            <span className="text-[11px] text-[var(--text-muted)] line-clamp-1 italic">
              &ldquo;{c.notes}&rdquo;
            </span>
          )}
        </div>
      ),
    },
    {
      key: "phone",
      header: "Contact Info",
      render: (c) => (
        <div className="flex flex-col gap-0.5 text-xs text-[var(--text-muted)]">
          {c.phone ? (
            <span className="flex items-center gap-1.5 font-mono text-[var(--text)]">
              <Phone className="w-3 h-3 text-purple-400" /> {c.phone}
            </span>
          ) : (
            <span className="text-[11px] text-[var(--text-muted)]">No phone</span>
          )}
          {c.email && (
            <span className="flex items-center gap-1.5 text-[11px]">
              <Mail className="w-3 h-3 text-cyan-400" /> {c.email}
            </span>
          )}
        </div>
      ),
    },
    {
      key: "address",
      header: "Location / Address",
      render: (c) => (
        <div className="max-w-xs text-xs text-[var(--text-muted)]">
          {c.address ? (
            <span className="flex items-start gap-1">
              <MapPin className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
              <span className="line-clamp-2">{c.address}</span>
            </span>
          ) : (
            <span className="text-[11px] italic text-[var(--text-muted)]">No address listed</span>
          )}
        </div>
      ),
    },
    {
      key: "total_orders_count",
      header: "Orders",
      align: "center",
      sortable: true,
      render: (c) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
          {c.total_orders_count || 0} orders
        </span>
      ),
    },
    {
      key: "total_spend",
      header: "Total Spend",
      align: "right",
      sortable: true,
      render: (c) => (
        <span className="font-mono font-bold text-xs text-[var(--text)]">
          ₹{(c.total_spend || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: "created_at",
      header: "Registered",
      align: "right",
      render: (c) => (
        <span className="text-xs text-[var(--text-muted)]">
          {new Date(c.created_at).toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          })}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (c) => (
        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => openDetailModal(c)}
            title="View Details"
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-cyan-400 hover:bg-cyan-500/10 transition-colors"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => openEditModal(c)}
            title="Edit Customer"
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-purple-400 hover:bg-purple-500/10 transition-colors"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleDelete(c)}
            title="Delete Customer"
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--text)]">
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        {/* KPI Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)] font-medium">Direct Customers</p>
              <h3 className="text-2xl font-bold font-mono text-[var(--text)]">{metrics.totalCount}</h3>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <UserPlus className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)] font-medium">Active Buyers</p>
              <h3 className="text-2xl font-bold font-mono text-emerald-400">{metrics.activeBuyers}</h3>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <ShoppingBag className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)] font-medium">Direct Orders Placed</p>
              <h3 className="text-2xl font-bold font-mono text-cyan-400">{metrics.totalOrders}</h3>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <IndianRupee className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)] font-medium">Direct Sales Volume</p>
              <h3 className="text-2xl font-bold font-mono text-amber-400">
                ₹{metrics.totalRevenue.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
              </h3>
            </div>
          </GlassCard>
        </div>

        {successMessage && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-400 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* List View Container */}
        <ListViewTemplate
          title="Direct Customers & Walk-In Buyers"
          description="Manage walk-in and individual direct buyers without credit terms, trading seamlessly on the shared wholesale sales order pipeline."
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          searchPlaceholder="Search customers by name, phone, email, notes..."
          primaryAction={
            <GlassButton
              variant="primary"
              size="md"
              onClick={openCreateModal}
            >
              <UserPlus className="w-4 h-4 mr-2" /> Add Direct Customer
            </GlassButton>
          }

        >
          <DataTable
            data={filteredCustomers}
            columns={columns}
            keyExtractor={(cust) => cust.id}
            isLoading={loading}
            onRowClick={openDetailModal}
            emptyTitle="No direct customer records found."
            emptyDescription="When individual or walk-in buyers register or place sales orders, they will appear here."
          />
        </ListViewTemplate>

        {/* Create Customer Modal */}
        <GlassModal
          isOpen={isCreateOpen}
          onClose={() => setIsCreateOpen(false)}
          title="Register Direct Walk-In Customer"
        >
          <form onSubmit={handleCreateSubmit} className="space-y-4">
            {errorMessage && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div className="space-y-1">
              <label htmlFor="create-cust-name" className="block text-xs font-medium text-[var(--text-muted)]">
                Customer Name *
              </label>
              <input
                id="create-cust-name"
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g. Ramesh Gupta"
                className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label htmlFor="create-cust-phone" className="block text-xs font-medium text-[var(--text-muted)]">
                  Phone Number
                </label>
                <input
                  id="create-cust-phone"
                  type="text"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+91 98765 43210"
                  className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="space-y-1">
                <label htmlFor="create-cust-email" className="block text-xs font-medium text-[var(--text-muted)]">
                  Email Address
                </label>
                <input
                  id="create-cust-email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="ramesh.gupta@example.com"
                  className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label htmlFor="create-cust-address" className="block text-xs font-medium text-[var(--text-muted)]">
                Delivery / Billing Address
              </label>
              <textarea
                id="create-cust-address"
                rows={2}
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                placeholder="Shop/Apartment, Street, City, Pincode"
                className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500 resize-none"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="create-cust-notes" className="block text-xs font-medium text-[var(--text-muted)]">
                Internal Buyer Notes
              </label>
              <textarea
                id="create-cust-notes"
                rows={2}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="e.g. Cash walk-in buyer, prefers Saturday morning collection"
                className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500 resize-none"
              />
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-[var(--glass-border)]">
              <GlassButton variant="ghost" size="sm" type="button" onClick={() => setIsCreateOpen(false)}>
                Cancel
              </GlassButton>
              <GlassButton variant="primary" size="sm" type="submit" disabled={submitting}>
                {submitting ? "Saving..." : "Register Customer"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>

        {/* Edit Customer Modal */}
        <GlassModal
          isOpen={isEditOpen}
          onClose={() => setIsEditOpen(false)}
          title={`Edit Customer — ${selectedCustomer?.name || ""}`}
        >
          <form onSubmit={handleEditSubmit} className="space-y-4">
            {errorMessage && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div className="space-y-1">
              <label htmlFor="edit-cust-name" className="block text-xs font-medium text-[var(--text-muted)]">
                Customer Name *
              </label>
              <input
                id="edit-cust-name"
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label htmlFor="edit-cust-phone" className="block text-xs font-medium text-[var(--text-muted)]">
                  Phone Number
                </label>
                <input
                  id="edit-cust-phone"
                  type="text"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="space-y-1">
                <label htmlFor="edit-cust-email" className="block text-xs font-medium text-[var(--text-muted)]">
                  Email Address
                </label>
                <input
                  id="edit-cust-email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label htmlFor="edit-cust-address" className="block text-xs font-medium text-[var(--text-muted)]">
                Address
              </label>
              <textarea
                id="edit-cust-address"
                rows={2}
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500 resize-none"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="edit-cust-notes" className="block text-xs font-medium text-[var(--text-muted)]">
                Internal Notes
              </label>
              <textarea
                id="edit-cust-notes"
                rows={2}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500 resize-none"
              />
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-[var(--glass-border)]">
              <GlassButton variant="ghost" size="sm" type="button" onClick={() => setIsEditOpen(false)}>
                Cancel
              </GlassButton>
              <GlassButton variant="primary" size="sm" type="submit" disabled={submitting}>
                {submitting ? "Saving..." : "Update Profile"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>

        {/* Customer Detail Inspection Modal */}
        <GlassModal
          isOpen={isDetailOpen}
          onClose={() => setIsDetailOpen(false)}
          title="Direct Customer Details"
        >
          {selectedCustomer && (
            <div className="space-y-5">
              <div className="p-4 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-[var(--text)]">{selectedCustomer.name}</h3>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    Walk-In Customer
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-[var(--text-muted)]">Phone:</span>
                    <p className="font-mono text-[var(--text)]">{selectedCustomer.phone || "—"}</p>
                  </div>
                  <div>
                    <span className="text-[var(--text-muted)]">Email:</span>
                    <p className="text-[var(--text)]">{selectedCustomer.email || "—"}</p>
                  </div>
                  <div className="sm:col-span-2">
                    <span className="text-[var(--text-muted)]">Address:</span>
                    <p className="text-[var(--text)]">{selectedCustomer.address || "—"}</p>
                  </div>
                  {selectedCustomer.notes && (
                    <div className="sm:col-span-2 p-2.5 rounded-xl bg-purple-500/5 border border-purple-500/20 text-purple-300">
                      <span className="text-[10px] uppercase font-bold text-purple-400 block mb-0.5">Notes</span>
                      <p className="italic">&ldquo;{selectedCustomer.notes}&rdquo;</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Order Telemetry */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-center">
                  <span className="text-[11px] text-[var(--text-muted)] block">Orders Placed</span>
                  <span className="text-xl font-bold font-mono text-[var(--text)]">
                    {selectedCustomer.total_orders_count || 0}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-center">
                  <span className="text-[11px] text-[var(--text-muted)] block">Total Spend</span>
                  <span className="text-xl font-bold font-mono text-amber-400">
                    ₹{(selectedCustomer.total_spend || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center pt-3 border-t border-[var(--glass-border)]">
                <GlassButton
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setIsDetailOpen(false);
                    openEditModal(selectedCustomer);
                  }}
                >
                  <Edit2 className="w-3.5 h-3.5 mr-1.5" /> Edit Profile
                </GlassButton>
                <GlassButton variant="primary" size="sm" onClick={() => setIsDetailOpen(false)}>
                  Close
                </GlassButton>
              </div>

            </div>
          )}
        </GlassModal>
      </div>
    </div>
  );
}
