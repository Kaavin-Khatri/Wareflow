"use client";

import { useEffect, useState, useMemo } from "react";
import AppLayout from "@/components/AppLayout";
import { ListViewTemplate } from "@/components/templates/ListViewTemplate";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassInput } from "@/components/glass/GlassInput";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassDatePicker } from "@/components/glass/GlassDatePicker";
import { apiClient } from "@/lib/api-client";
import {
  Truck,
  Plus,
  Edit2,
  Phone,
  Mail,
  FileCheck,
  ShieldCheck,
  Building2,
  CheckCircle2,
  AlertCircle,
  CalendarClock,
} from "lucide-react";

/**
 * Compute FSSAI license compliance status for a supplier.
 * Returns an object with status label, badge variant, and days remaining.
 */
function computeFssaiStatus(expiryDate: string | null): {
  label: string;
  variant: "success" | "warning" | "error" | "neutral";
  daysRemaining: number | null;
} {
  if (!expiryDate) {
    return { label: "No FSSAI", variant: "neutral", daysRemaining: null };
  }
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const parts = expiryDate.split("-");
  const expiry =
    parts.length === 3
      ? new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
      : new Date(expiryDate);
  expiry.setHours(0, 0, 0, 0);

  const diffMs = expiry.getTime() - today.getTime();
  const days = Math.round(diffMs / (1000 * 60 * 60 * 24));

  if (days < 0) {
    return { label: "Expired", variant: "error", daysRemaining: days };
  }
  if (days <= 30) {
    return { label: "Expiring Soon", variant: "warning", daysRemaining: days };
  }
  return { label: "Valid", variant: "success", daysRemaining: days };
}

export interface SupplierItem {
  id: string;
  name: string;
  contact_person: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  gstin: string | null;
  fssai_license_no: string | null;
  fssai_expiry_date: string | null;
  is_active: boolean;
  created_at?: string;
}

export default function SuppliersAdminPage() {
  const [suppliers, setSuppliers] = useState<SupplierItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<SupplierItem | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    contact_person: "",
    phone: "",
    email: "",
    address: "",
    gstin: "",
    fssai_license_no: "",
    fssai_expiry_date: "",
    is_active: true,
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchSuppliers = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<SupplierItem[]>("/suppliers");
      setSuppliers(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load suppliers.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      try {
        const data = await apiClient.get<SupplierItem[]>("/suppliers");
        if (!ignore) {
          setSuppliers(data);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load suppliers.");
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

  const handleOpenCreate = () => {
    setEditingSupplier(null);
    setFormData({
      name: "",
      contact_person: "",
      phone: "",
      email: "",
      address: "",
      gstin: "",
      fssai_license_no: "",
      fssai_expiry_date: "",
      is_active: true,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const handleOpenEdit = (supplier: SupplierItem) => {
    setEditingSupplier(supplier);
    setFormData({
      name: supplier.name,
      contact_person: supplier.contact_person || "",
      phone: supplier.phone || "",
      email: supplier.email || "",
      address: supplier.address || "",
      gstin: supplier.gstin || "",
      fssai_license_no: supplier.fssai_license_no || "",
      fssai_expiry_date: supplier.fssai_expiry_date || "",
      is_active: supplier.is_active,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setFormError("Supplier name is required.");
      return;
    }

    setSubmitting(true);
    setFormError(null);
    setError(null);
    setSuccess(null);

    const payload = {
      name: formData.name.trim(),
      contact_person: formData.contact_person.trim() || null,
      phone: formData.phone.trim() || null,
      email: formData.email.trim() || null,
      address: formData.address.trim() || null,
      gstin: formData.gstin.trim().toUpperCase() || null,
      fssai_license_no: formData.fssai_license_no.trim() || null,
      fssai_expiry_date: formData.fssai_expiry_date.trim() || null,
      is_active: formData.is_active,
    };

    try {
      if (editingSupplier) {
        await apiClient.patch(`/suppliers/${editingSupplier.id}`, payload);
        setSuccess(`Supplier "${payload.name}" updated successfully.`);
      } else {
        await apiClient.post("/suppliers", payload);
        setSuccess(`Supplier "${payload.name}" registered successfully.`);
      }
      setModalOpen(false);
      await fetchSuppliers();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to save supplier.");
    } finally {
      setSubmitting(false);
    }
  };

  // Filtered dataset
  const filteredSuppliers = useMemo(() => {
    return suppliers.filter((s) => {
      const matchesSearch =
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (s.contact_person && s.contact_person.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (s.email && s.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (s.gstin && s.gstin.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesStatus =
        statusFilter === "all" ? true : statusFilter === "active" ? s.is_active : !s.is_active;

      return matchesSearch && matchesStatus;
    });
  }, [suppliers, searchQuery, statusFilter]);

  // Metrics
  const totalCount = suppliers.length;
  const activeCount = suppliers.filter((s) => s.is_active).length;
  const gstinCount = suppliers.filter((s) => Boolean(s.gstin)).length;
  const fssaiCount = suppliers.filter((s) => Boolean(s.fssai_license_no)).length;

  const columns: DataTableColumn<SupplierItem>[] = [
    {
      key: "name",
      header: "Supplier Company",
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center shrink-0">
            <Building2 className="w-4 h-4" />
          </div>
          <div>
            <div className="font-semibold text-sm text-[var(--text)] tracking-tight">
              {row.name}
            </div>
            {row.address && (
              <div className="text-xs text-[var(--text-muted)] truncate max-w-xs">
                {row.address}
              </div>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "contact_person",
      header: "Primary Contact",
      sortable: true,
      render: (row) => (
        <div className="space-y-1">
          <div className="text-xs font-medium text-[var(--text)]">
            {row.contact_person || <span className="text-[var(--text-muted)]">—</span>}
          </div>
          {row.phone && (
            <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
              <Phone className="w-3 h-3 text-purple-400" />
              <span>{row.phone}</span>
            </div>
          )}
        </div>
      ),
    },
    {
      key: "email",
      header: "Email",
      render: (row) =>
        row.email ? (
          <div className="flex items-center gap-1.5 text-xs text-[var(--text)] font-mono">
            <Mail className="w-3 h-3 text-purple-400" />
            <a href={`mailto:${row.email}`} className="hover:underline hover:text-purple-400">
              {row.email}
            </a>
          </div>
        ) : (
          <span className="text-xs text-[var(--text-muted)]">—</span>
        ),
    },
    {
      key: "gstin",
      header: "Tax & Compliance",
      render: (row) => {
        const fssai = computeFssaiStatus(row.fssai_expiry_date);
        return (
          <div className="flex flex-col gap-1.5">
            <div className="flex flex-wrap gap-1.5">
              {row.gstin ? (
                <span className="px-2 py-0.5 rounded-lg text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                  <FileCheck className="w-2.5 h-2.5" />
                  GSTIN: {row.gstin}
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-lg text-[10px] bg-zinc-500/10 text-zinc-400 border border-zinc-500/20">
                  No GSTIN
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <GlassBadge variant={fssai.variant} className="text-[10px] px-2 py-0.5">
                <ShieldCheck className="w-2.5 h-2.5 mr-0.5" />
                {row.fssai_license_no ? `FSSAI: ${fssai.label}` : fssai.label}
              </GlassBadge>
              {fssai.daysRemaining !== null && (
                <span className="text-[10px] text-[var(--text-muted)] flex items-center gap-0.5">
                  <CalendarClock className="w-2.5 h-2.5" />
                  {fssai.daysRemaining < 0
                    ? `${Math.abs(fssai.daysRemaining)}d overdue`
                    : `${fssai.daysRemaining}d left`}
                </span>
              )}
            </div>
          </div>
        );
      },
    },

    {
      key: "is_active",
      header: "Status",
      sortable: true,
      render: (row) => (
        <GlassBadge
          variant={row.is_active ? "success" : "neutral"}
          className="capitalize text-xs font-semibold px-2.5 py-0.5"
        >
          {row.is_active ? "Active Vendor" : "Inactive"}
        </GlassBadge>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (row) => (
        <div className="flex items-center justify-end gap-2">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={() => handleOpenEdit(row)}
            className="h-8 px-2.5 text-xs text-purple-400 hover:text-purple-300 hover:bg-purple-500/10"
          >
            <Edit2 className="w-3.5 h-3.5 mr-1" />
            Edit
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
              <span>Total Vendors</span>
              <Building2 className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-[var(--text)]">{totalCount}</div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-medium mb-1">
              <span>Active Suppliers</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-emerald-400">{activeCount}</div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-medium mb-1">
              <span>GSTIN Verified</span>
              <FileCheck className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-blue-400">{gstinCount}</div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-medium mb-1">
              <span>FSSAI Certified</span>
              <ShieldCheck className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-purple-400">{fssaiCount}</div>
          </GlassCard>
        </div>

        {/* Success Alert */}
        {success && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{success}</span>
            </div>
            <button
              onClick={() => setSuccess(null)}
              className="text-xs hover:underline opacity-80 hover:opacity-100"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-xs hover:underline opacity-80 hover:opacity-100"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* List View Template with DataTable */}
        <ListViewTemplate
          title="Suppliers & Vendors"
          description="Manage goods manufacturers, procurement vendors, GSTIN compliance, and contact details."
          searchPlaceholder="Search by name, contact person, email, or GSTIN..."
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          primaryAction={
            <GlassButton variant="primary" onClick={handleOpenCreate} className="gap-2">
              <Plus className="w-4 h-4" />
              Add Supplier
            </GlassButton>
          }
        >
          {/* Status Filter Tab Pills */}
          <div className="flex items-center gap-2 mb-4">
            <button
              type="button"
              onClick={() => setStatusFilter("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === "all"
                  ? "bg-purple-600/30 text-purple-300 border border-purple-500/40"
                  : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent"
              }`}
            >
              All ({totalCount})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("active")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === "active"
                  ? "bg-emerald-600/30 text-emerald-300 border border-emerald-500/40"
                  : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent"
              }`}
            >
              Active ({activeCount})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("inactive")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === "inactive"
                  ? "bg-rose-600/30 text-rose-300 border border-rose-500/40"
                  : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent"
              }`}
            >
              Inactive ({totalCount - activeCount})
            </button>
          </div>

          <DataTable
            columns={columns}
            data={filteredSuppliers}
            keyExtractor={(item) => item.id}
            isLoading={loading}
            emptyTitle="No Suppliers Found"
            emptyDescription={
              searchQuery
                ? `No suppliers match your search query "${searchQuery}".`
                : "Get started by registering your first supplier or goods manufacturer."
            }
            emptyIcon={<Truck className="w-12 h-12 text-purple-400/50" />}
            emptyAction={
              !searchQuery && (
                <GlassButton variant="primary" size="sm" onClick={handleOpenCreate}>
                  <Plus className="w-4 h-4 mr-1.5" />
                  Add First Supplier
                </GlassButton>
              )
            }
          />
        </ListViewTemplate>

        {/* Create / Edit Supplier Modal */}
        <GlassModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title={
            editingSupplier ? `Edit Supplier — ${editingSupplier.name}` : "Register New Supplier"
          }
          description="Enter vendor company credentials, primary contact info, and tax compliance identifiers."
        >
          <form onSubmit={handleSubmit} className="space-y-4 pt-2">
            {formError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                Company / Vendor Name <span className="text-rose-400">*</span>
              </label>
              <GlassInput
                type="text"
                required
                placeholder="e.g. Hindustan Unilever Ltd"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  Contact Person
                </label>
                <GlassInput
                  type="text"
                  placeholder="e.g. Rajesh Sharma"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  Phone Number
                </label>
                <GlassInput
                  type="tel"
                  placeholder="e.g. +91 98765 43210"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <GlassInput
                  type="email"
                  placeholder="vendor@company.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  Indian GSTIN (15 Digits)
                </label>
                <GlassInput
                  type="text"
                  maxLength={15}
                  placeholder="27ABCDE1234F1Z5"
                  value={formData.gstin}
                  onChange={(e) =>
                    setFormData({ ...formData, gstin: e.target.value.toUpperCase() })
                  }
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                Physical / Billing Address
              </label>
              <textarea
                rows={2}
                placeholder="Warehouse / Corporate Office location..."
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl text-xs bg-[var(--surface)] text-[var(--text)] placeholder-[var(--text-muted)] border border-[var(--border)] focus:outline-none focus:ring-1 focus:ring-purple-500/50 transition-all resize-none"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  FSSAI License No
                </label>
                <GlassInput
                  type="text"
                  placeholder="14-digit FSSAI number"
                  value={formData.fssai_license_no}
                  onChange={(e) => setFormData({ ...formData, fssai_license_no: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  FSSAI Expiry Date
                </label>
                <GlassDatePicker
                  value={formData.fssai_expiry_date}
                  onChange={(val) => setFormData({ ...formData, fssai_expiry_date: val })}
                  size="sm"
                />
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-[var(--text)]">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="rounded border-[var(--border)] text-purple-500 focus:ring-purple-500/40 bg-[var(--surface)]"
                />
                <span>Active for Procurement & Purchase Orders</span>
              </label>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--glass-border)]">
              <GlassButton
                type="button"
                variant="ghost"
                onClick={() => setModalOpen(false)}
                disabled={submitting}
              >
                Cancel
              </GlassButton>
              <GlassButton type="submit" variant="primary" disabled={submitting}>
                {submitting ? "Saving..." : editingSupplier ? "Save Changes" : "Create Supplier"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>
      </div>
    </AppLayout>
  );
}
