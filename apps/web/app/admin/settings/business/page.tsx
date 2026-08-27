"use client";

import { useEffect, useState, useMemo } from "react";
import AppLayout from "@/components/AppLayout";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassInput } from "@/components/glass/GlassInput";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassDatePicker } from "@/components/glass/GlassDatePicker";
import { apiClient } from "@/lib/api-client";
import {
  Building2,
  Save,
  ShieldCheck,
  FileCheck,
  CalendarClock,
  Phone,
  Mail,
  MapPin,
  AlertCircle,
  CheckCircle2,
  Loader2,
} from "lucide-react";

interface BusinessSettingsData {
  id: string;
  business_name: string;
  gstin: string | null;
  fssai_license_no: string | null;
  fssai_expiry_date: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  updated_at: string | null;
  fssai_status: string;
  days_until_fssai_expiry: number | null;
}

/**
 * Compute FSSAI compliance banner style based on status.
 */
function getFssaiBannerConfig(status: string, daysRemaining: number | null) {
  if (status === "expired") {
    return {
      variant: "error" as const,
      bgClass: "bg-rose-500/10 border-rose-500/30",
      textClass: "text-rose-400",
      title: "FSSAI License Expired",
      message: `Your FSSAI food safety license has expired${daysRemaining !== null ? ` ${Math.abs(daysRemaining)} days ago` : ""}. Immediate renewal is legally required to continue food distribution operations.`,
    };
  }
  if (status === "expiring_soon") {
    return {
      variant: "warning" as const,
      bgClass: "bg-amber-500/10 border-amber-500/30",
      textClass: "text-amber-400",
      title: "FSSAI License Expiring Soon",
      message: `Your FSSAI license expires in ${daysRemaining} day${daysRemaining !== 1 ? "s" : ""}. Please initiate the renewal process with the food safety authority.`,
    };
  }
  if (status === "valid") {
    return {
      variant: "success" as const,
      bgClass: "bg-emerald-500/10 border-emerald-500/30",
      textClass: "text-emerald-400",
      title: "FSSAI License Active",
      message: `Your FSSAI license is valid for ${daysRemaining} more day${daysRemaining !== 1 ? "s" : ""}.`,
    };
  }
  return {
    variant: "neutral" as const,
    bgClass: "bg-zinc-500/10 border-zinc-500/30",
    textClass: "text-zinc-400",
    title: "No FSSAI License Registered",
    message:
      "Register your FSSAI food safety license number and expiry date to enable compliance monitoring.",
  };
}

export default function BusinessSettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  const [formData, setFormData] = useState({
    business_name: "",
    gstin: "",
    fssai_license_no: "",
    fssai_expiry_date: "",
    address: "",
    phone: "",
    email: "",
  });

  const [fssaiStatus, setFssaiStatus] = useState("missing");
  const [daysRemaining, setDaysRemaining] = useState<number | null>(null);

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      try {
        const data = await apiClient.get<BusinessSettingsData>("/settings/business");
        if (!ignore) {
          setFormData({
            business_name: data.business_name || "",
            gstin: data.gstin || "",
            fssai_license_no: data.fssai_license_no || "",
            fssai_expiry_date: data.fssai_expiry_date || "",
            address: data.address || "",
            phone: data.phone || "",
            email: data.email || "",
          });
          setFssaiStatus(data.fssai_status);
          setDaysRemaining(data.days_until_fssai_expiry);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load business settings.");
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

  const updateField = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setIsDirty(true);
    setSuccess(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.business_name.trim()) {
      setError("Business name is required.");
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = {
        business_name: formData.business_name.trim(),
        gstin: formData.gstin.trim().toUpperCase() || null,
        fssai_license_no: formData.fssai_license_no.trim() || null,
        fssai_expiry_date: formData.fssai_expiry_date.trim() || null,
        address: formData.address.trim() || null,
        phone: formData.phone.trim() || null,
        email: formData.email.trim() || null,
      };

      const data = await apiClient.put<BusinessSettingsData>("/settings/business", payload);
      setFssaiStatus(data.fssai_status);
      setDaysRemaining(data.days_until_fssai_expiry);
      setIsDirty(false);
      setSuccess("Business settings saved successfully.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save business settings.");
    } finally {
      setSaving(false);
    }
  };

  const banner = useMemo(
    () => getFssaiBannerConfig(fssaiStatus, daysRemaining),
    [fssaiStatus, daysRemaining],
  );

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-6 pb-12">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text)] flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-purple-400" />
            </div>
            Business Settings
          </h1>
          <p className="text-sm text-[var(--text-muted)] mt-1.5">
            Manage your distributor legal profile, GSTIN, and FSSAI food safety license compliance.
            These details appear on invoices, purchase orders, and packing slips.
          </p>
        </div>

        {/* FSSAI Compliance Banner */}
        <GlassCard className={`p-4 border ${banner.bgClass}`}>
          <div className="flex items-start gap-3">
            <div className={`p-2 rounded-lg ${banner.bgClass}`}>
              <ShieldCheck className={`w-5 h-5 ${banner.textClass}`} />
            </div>
            <div>
              <div className={`font-semibold text-sm ${banner.textClass}`}>{banner.title}</div>
              <div className="text-xs text-[var(--text-muted)] mt-0.5">{banner.message}</div>
            </div>
            <GlassBadge variant={banner.variant} className="ml-auto shrink-0">
              {fssaiStatus === "missing" ? "N/A" : fssaiStatus.replace("_", " ").toUpperCase()}
            </GlassBadge>
          </div>
        </GlassCard>

        {/* Success / Error Alerts */}
        {success && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{success}</span>
          </div>
        )}
        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Settings Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Business Identity Section */}
          <GlassCard className="p-5 space-y-4">
            <h2 className="text-sm font-bold tracking-wider uppercase text-[var(--text-muted)] flex items-center gap-2">
              <Building2 className="w-4 h-4 text-purple-400" />
              Business Identity
            </h2>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                Business / Legal Entity Name <span className="text-rose-400">*</span>
              </label>
              <GlassInput
                type="text"
                required
                placeholder="e.g. Shree Ganesh Food Traders Pvt Ltd"
                value={formData.business_name}
                onChange={(e) => updateField("business_name", e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  <FileCheck className="w-3 h-3 inline mr-1 text-emerald-400" />
                  Indian GSTIN (15 Digits)
                </label>
                <GlassInput
                  type="text"
                  maxLength={15}
                  placeholder="27ABCDE1234F1Z5"
                  value={formData.gstin}
                  onChange={(e) => updateField("gstin", e.target.value.toUpperCase())}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  <MapPin className="w-3 h-3 inline mr-1 text-blue-400" />
                  Registered Business Address
                </label>
                <GlassInput
                  type="text"
                  placeholder="APMC Market, Vashi, Navi Mumbai"
                  value={formData.address}
                  onChange={(e) => updateField("address", e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  <Phone className="w-3 h-3 inline mr-1 text-purple-400" />
                  Contact Phone
                </label>
                <GlassInput
                  type="tel"
                  placeholder="+91 98765 43210"
                  value={formData.phone}
                  onChange={(e) => updateField("phone", e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  <Mail className="w-3 h-3 inline mr-1 text-purple-400" />
                  Official Email
                </label>
                <GlassInput
                  type="email"
                  placeholder="billing@yourcompany.com"
                  value={formData.email}
                  onChange={(e) => updateField("email", e.target.value)}
                />
              </div>
            </div>
          </GlassCard>

          {/* FSSAI Food Safety License */}
          <GlassCard overflowVisible className="p-5 space-y-4 overflow-visible relative z-30">
            <h2 className="text-sm font-bold tracking-wider uppercase text-[var(--text-muted)] flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              FSSAI Food Safety License
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  FSSAI License Number (14 Digits)
                </label>
                <GlassInput
                  type="text"
                  maxLength={14}
                  placeholder="10020030040050"
                  value={formData.fssai_license_no}
                  onChange={(e) => updateField("fssai_license_no", e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                  <CalendarClock className="w-3 h-3 inline mr-1 text-amber-400" />
                  License Expiry Date
                </label>
                <GlassDatePicker
                  value={formData.fssai_expiry_date}
                  onChange={(val) => updateField("fssai_expiry_date", val)}
                  size="sm"
                />
              </div>
            </div>

            <div className="text-xs text-[var(--text-muted)] bg-[var(--surface)] p-3 rounded-lg border border-[var(--border)]">
              <strong>Compliance Note:</strong> WareFlow will send WhatsApp + email alerts to
              Owner-role users starting <strong>30 days</strong> before expiry, escalating in the
              final <strong>7 days</strong>. License renewal is your legal responsibility — WareFlow
              monitors and alerts but does not file renewals.
            </div>
          </GlassCard>

          {/* Save Actions */}
          <div className="flex items-center justify-between pt-2">
            <div className="text-xs text-[var(--text-muted)]">
              {isDirty ? (
                <span className="text-amber-400">● Unsaved changes</span>
              ) : (
                <span className="text-emerald-400">● All changes saved</span>
              )}
            </div>
            <GlassButton type="submit" variant="primary" disabled={saving || !isDirty}>
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-1.5" />
                  Save Business Settings
                </>
              )}
            </GlassButton>
          </div>
        </form>
      </div>
    </AppLayout>
  );
}
