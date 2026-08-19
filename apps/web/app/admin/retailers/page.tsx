"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
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
  Store,
  Plus,
  Edit2,
  Phone,
  FileCheck,
  Crown,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  IndianRupee,
  ReceiptText,
} from "lucide-react";




export interface RetailerItem {
  id: string;
  name: string;
  contact_person: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  gstin: string | null;
  pricing_tier: "standard" | "silver" | "gold" | string;
  credit_limit: number;
  credit_balance: number;
  is_active: boolean;
  created_at?: string;
}

export default function RetailersAdminPage() {
  const [retailers, setRetailers] = useState<RetailerItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [tierFilter, setTierFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRetailer, setEditingRetailer] = useState<RetailerItem | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    contact_person: "",
    phone: "",
    email: "",
    address: "",
    gstin: "",
    pricing_tier: "standard",
    credit_limit: 0,
    is_active: true,
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchRetailers = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<RetailerItem[]>("/retailers");
      setRetailers(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load retailers.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      try {
        const data = await apiClient.get<RetailerItem[]>("/retailers");
        if (!ignore) {
          setRetailers(data);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load retailers.");
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
    setEditingRetailer(null);
    setFormData({
      name: "",
      contact_person: "",
      phone: "",
      email: "",
      address: "",
      gstin: "",
      pricing_tier: "standard",
      credit_limit: 0,
      is_active: true,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const handleOpenEdit = (retailer: RetailerItem) => {
    setEditingRetailer(retailer);
    setFormData({
      name: retailer.name,
      contact_person: retailer.contact_person || "",
      phone: retailer.phone || "",
      email: retailer.email || "",
      address: retailer.address || "",
      gstin: retailer.gstin || "",
      pricing_tier: retailer.pricing_tier || "standard",
      credit_limit: Number(retailer.credit_limit) || 0,
      is_active: retailer.is_active,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setFormError("Retailer name is required.");
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
      pricing_tier: formData.pricing_tier,
      credit_limit: Number(formData.credit_limit) || 0,
      is_active: formData.is_active,
    };

    try {
      if (editingRetailer) {
        await apiClient.patch(`/retailers/${editingRetailer.id}`, payload);
        setSuccess(`Retailer "${payload.name}" updated successfully.`);
      } else {
        await apiClient.post("/retailers", payload);
        setSuccess(`Retailer "${payload.name}" registered successfully.`);
      }
      setModalOpen(false);
      await fetchRetailers();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to save retailer.");
    } finally {
      setSubmitting(false);
    }
  };

  // Filtered dataset
  const filteredRetailers = useMemo(() => {
    return retailers.filter((r) => {
      const matchesSearch =
        r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (r.contact_person && r.contact_person.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (r.email && r.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (r.gstin && r.gstin.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesStatus =
        statusFilter === "all" ? true : statusFilter === "active" ? r.is_active : !r.is_active;

      const matchesTier =
        tierFilter === "all" ? true : r.pricing_tier.toLowerCase() === tierFilter.toLowerCase();

      return matchesSearch && matchesStatus && matchesTier;
    });
  }, [retailers, searchQuery, statusFilter, tierFilter]);

  // Metrics
  const totalCount = retailers.length;
  const activeCount = retailers.filter((r) => r.is_active).length;
  const goldCount = retailers.filter((r) => r.pricing_tier === "gold").length;
  const silverCount = retailers.filter((r) => r.pricing_tier === "silver").length;
  const totalCreditExtended = retailers.reduce(
    (sum, r) => sum + (Number(r.credit_limit) || 0),
    0,
  );

  const renderTierBadge = (tier: string) => {
    switch (tier.toLowerCase()) {
      case "gold":
        return (
          <span className="px-2 py-0.5 rounded-lg text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-fit">
            <Crown className="w-3 h-3 text-amber-400" />
            Gold Tier (10% Off)
          </span>
        );
      case "silver":
        return (
          <span className="px-2 py-0.5 rounded-lg text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 flex items-center gap-1 w-fit">
            <Sparkles className="w-3 h-3 text-cyan-300" />
            Silver Tier (5% Off)
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-lg text-xs font-medium bg-zinc-500/10 text-zinc-400 border border-zinc-500/20 flex items-center gap-1 w-fit">
            Standard Base
          </span>
        );
    }
  };

  const columns: DataTableColumn<RetailerItem>[] = [
    {
      key: "name",
      header: "Retailer / B2B Account",
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center shrink-0">
            <Store className="w-4 h-4" />
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
      key: "pricing_tier",
      header: "Bulk Pricing Tier",
      sortable: true,
      render: (row) => renderTierBadge(row.pricing_tier),
    },
    {
      key: "credit_limit",
      header: "Credit Line & Balance",
      sortable: true,
      render: (row) => {
        const limit = Number(row.credit_limit) || 0;
        const balance = Number(row.credit_balance) || 0;
        const available = Math.max(0, limit - balance);
        const utilizationPct = limit > 0 ? Math.min(100, Math.round((balance / limit) * 100)) : 0;
        const isWarning = utilizationPct >= 80;
        const isCritical = limit > 0 && balance >= limit;

        return (
          <div className="space-y-1.5 min-w-[170px]">
            <div className="flex items-center justify-between gap-1 text-xs font-mono font-semibold">
              <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${
                isCritical
                  ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                  : isWarning
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                  : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
              }`}>
                ₹{balance.toLocaleString("en-IN")} / ₹{limit.toLocaleString("en-IN")}
              </span>
              <span className="text-[10px] text-[var(--text-muted)] font-normal">{utilizationPct}%</span>
            </div>
            <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all rounded-full ${
                  isCritical ? "bg-rose-500" : isWarning ? "bg-amber-500" : "bg-emerald-500"
                }`}
                style={{ width: `${utilizationPct}%` }}
              />
            </div>
            <div className="text-[10px] text-[var(--text-muted)] flex items-center justify-between">
              <span>Avail: ₹{available.toLocaleString("en-IN")}</span>
            </div>
          </div>
        );
      },
    },
    {
      key: "gstin",
      header: "GSTIN Compliance",
      render: (row) =>
        row.gstin ? (
          <span className="px-2 py-0.5 rounded-lg text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1 w-fit">
            <FileCheck className="w-2.5 h-2.5" />
            {row.gstin}
          </span>
        ) : (
          <span className="px-2 py-0.5 rounded-lg text-[10px] bg-zinc-500/10 text-zinc-400 border border-zinc-500/20 w-fit">
            No GSTIN
          </span>
        ),
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
          {row.is_active ? "Active" : "Inactive"}
        </GlassBadge>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <Link href={`/admin/retailers/${row.id}/ledger`}>
            <GlassButton
              size="sm"
              variant="outline"
              className="h-8 px-2.5 text-xs text-cyan-400 hover:text-cyan-300 border-cyan-500/30 hover:bg-cyan-500/10"
            >
              <ReceiptText className="w-3.5 h-3.5 mr-1" />
              Ledger
            </GlassButton>
          </Link>
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
              <span>Total Retailers</span>
              <Store className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-[var(--text)]">{totalCount}</div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-medium mb-1">
              <span>Active Accounts</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-emerald-400">{activeCount}</div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-medium mb-1">
              <span>Gold & Silver Tiers</span>
              <Crown className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-amber-400">
              {goldCount + silverCount}
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] font-medium mb-1">
              <span>Credit Extended</span>
              <IndianRupee className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-cyan-400">
              ₹{totalCreditExtended >= 100000 ? `${(totalCreditExtended / 100000).toFixed(1)}L` : totalCreditExtended.toLocaleString("en-IN")}
            </div>
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
          title="Retailers & B2B Accounts"
          description="Manage wholesale shop accounts, tiered pricing schedules, GSTIN details, and authorized credit lines."
          searchPlaceholder="Search by name, contact person, email, or GSTIN..."
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          primaryAction={
            <GlassButton variant="primary" onClick={handleOpenCreate} className="gap-2">
              <Plus className="w-4 h-4" />
              Register Retailer
            </GlassButton>
          }
        >
          {/* Filters Tab Pills */}
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            {/* Status Pills */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setStatusFilter("all")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  statusFilter === "all"
                    ? "bg-purple-600/30 text-purple-300 border border-purple-500/40"
                    : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent"
                }`}
              >
                All Status ({totalCount})
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

            {/* Tier Filter Pills */}
            <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
              <span>Tier:</span>
              {(["all", "standard", "silver", "gold"] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setTierFilter(t)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium capitalize transition-all ${
                    tierFilter === t
                      ? "bg-white/10 text-[var(--text)] border border-[var(--border)]"
                      : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <DataTable
            columns={columns}
            data={filteredRetailers}
            keyExtractor={(item) => item.id}
            isLoading={loading}
            emptyTitle="No Retailers Found"
            emptyDescription={
              searchQuery
                ? `No retailers match your search query "${searchQuery}".`
                : "Get started by registering your first wholesale retailer or kirana store account."
            }
            emptyIcon={<Store className="w-12 h-12 text-purple-400/50" />}
            emptyAction={
              !searchQuery && (
                <GlassButton variant="primary" size="sm" onClick={handleOpenCreate}>
                  <Plus className="w-4 h-4 mr-1.5" />
                  Register First Retailer
                </GlassButton>
              )
            }
          />
        </ListViewTemplate>

        {/* Create / Edit Retailer Modal */}
        <GlassModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title={
            editingRetailer ? `Edit Retailer — ${editingRetailer.name}` : "Register Wholesale Retailer"
          }
          description="Enter business details, pricing tier for automated sales order discounts, and credit limits."
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
                Business / Retailer Name <span className="text-rose-400">*</span>
              </label>
              <GlassInput
                type="text"
                required
                placeholder="e.g. Apex Kirana & Provision Stores"
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
                  placeholder="e.g. Ramesh Patel"
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
                  placeholder="billing@apexkirana.com"
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
                Delivery / Shop Address
              </label>
              <textarea
                rows={2}
                placeholder="Shop number, market building, area, city..."
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl text-xs bg-[var(--surface)] text-[var(--text)] placeholder-[var(--text-muted)] border border-[var(--border)] focus:outline-none focus:ring-1 focus:ring-purple-500/50 transition-all resize-none"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  Bulk Pricing Tier <span className="text-rose-400">*</span>
                </label>
                <select
                  value={formData.pricing_tier}
                  onChange={(e) => setFormData({ ...formData, pricing_tier: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl text-xs bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] focus:outline-none focus:ring-1 focus:ring-purple-500/50 transition-all"
                >
                  <option value="standard">Standard Tier (0% Discount)</option>
                  <option value="silver">Silver Tier (5% Discount)</option>
                  <option value="gold">Gold Tier (10% Discount)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  Authorized Credit Limit (₹)
                </label>
                <GlassInput
                  type="number"
                  min={0}
                  step={1000}
                  placeholder="e.g. 50000"
                  value={formData.credit_limit}
                  onChange={(e) =>
                    setFormData({ ...formData, credit_limit: Math.max(0, Number(e.target.value) || 0) })
                  }
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
                <span>Active Account (Eligible for Sales Orders & Invoicing)</span>
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
                {submitting ? "Saving..." : editingRetailer ? "Save Changes" : "Submit Registration"}
              </GlassButton>

            </div>
          </form>
        </GlassModal>
      </div>
    </AppLayout>
  );
}
