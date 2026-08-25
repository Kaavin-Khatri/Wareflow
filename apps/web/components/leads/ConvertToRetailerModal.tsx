"use client";

import React, { useState } from "react";
import { LeadItem } from "./LeadInfoWindow";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassModal } from "@/components/glass/GlassModal";
import {
  Store,
  User,
  Phone,
  Mail,
  MapPin,
  FileText,
  CreditCard,
  Layers,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";

export interface ConvertToRetailerModalProps {
  isOpen: boolean;
  lead: LeadItem;
  onClose: () => void;
  onSuccess: (updatedLead: LeadItem, createdRetailer: any) => void;
}

export function ConvertToRetailerModal({
  isOpen,
  lead,
  onClose,
  onSuccess,
}: ConvertToRetailerModalProps) {
  const [name, setName] = useState(lead.name);
  const [contactPerson, setContactPerson] = useState("");
  const [phone, setPhone] = useState(lead.phone || "");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState(lead.address || "");
  const [gstin, setGstin] = useState("");
  const [pricingTier, setPricingTier] = useState<"standard" | "silver" | "gold">("standard");
  const [creditLimit, setCreditLimit] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await apiClient.post<any>(`/leads/${lead.id}/convert-to-retailer`, {
        name: name.trim(),
        contact_person: contactPerson.trim() || null,
        phone: phone.trim() || null,
        email: email.trim() || null,
        address: address.trim() || null,
        gstin: gstin.trim() || null,
        pricing_tier: pricingTier,
        credit_limit: Number(creditLimit) || 0,
      });

      onSuccess(response.lead, response.retailer);
      onClose();
    } catch (err: any) {
      console.error("Failed to convert lead:", err);
      setErrorMessage(
        err?.detail || err?.message || "Failed to convert lead to retailer. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title="Convert Lead to Wholesale Retailer"
      description="Create a formal B2B Retailer account pre-filled from this scanned lead."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        {errorMessage && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 font-medium">
            {errorMessage}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Business Name */}
          <div className="space-y-1.5 md:col-span-2">
            <label className="font-semibold text-[var(--text)] flex items-center gap-1.5">
              <Store className="w-3.5 h-3.5 text-[var(--accent)]" />
              Business / Store Name *
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Rameshwar Farsan & Namkeen"
              className="w-full px-3 py-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
            />
          </div>

          {/* Contact Person */}
          <div className="space-y-1.5">
            <label className="font-semibold text-[var(--text)] flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              Proprietor / Contact Person
            </label>
            <input
              type="text"
              value={contactPerson}
              onChange={(e) => setContactPerson(e.target.value)}
              placeholder="e.g. Ramesh-bhai Patel"
              className="w-full px-3 py-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
            />
          </div>

          {/* Phone */}
          <div className="space-y-1.5">
            <label className="font-semibold text-[var(--text)] flex items-center gap-1.5">
              <Phone className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              Phone Number
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+91 98250 12345"
              className="w-full px-3 py-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
            />
          </div>

          {/* Email */}
          <div className="space-y-1.5">
            <label className="font-semibold text-[var(--text)] flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="retailer@example.com"
              className="w-full px-3 py-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
            />
          </div>

          {/* GSTIN */}
          <div className="space-y-1.5">
            <label className="font-semibold text-[var(--text)] flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              GSTIN (Optional)
            </label>
            <input
              type="text"
              value={gstin}
              onChange={(e) => setGstin(e.target.value.toUpperCase())}
              placeholder="24AAAAA0000A1Z5"
              maxLength={15}
              className="w-full px-3 py-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] font-mono focus:outline-none focus:border-[var(--accent)]"
            />
          </div>

          {/* Address */}
          <div className="space-y-1.5 md:col-span-2">
            <label className="font-semibold text-[var(--text)] flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              Store Address
            </label>
            <textarea
              rows={2}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Complete shop address..."
              className="w-full px-3 py-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
            />
          </div>

          {/* Pricing Tier */}
          <div className="space-y-1.5">
            <label className="font-semibold text-[var(--text)] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-[var(--accent)]" />
              Wholesale Pricing Tier
            </label>
            <select
              value={pricingTier}
              onChange={(e) => setPricingTier(e.target.value as any)}
              className="w-full px-3 py-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
            >
              <option value="standard">Standard (Base Pricing)</option>
              <option value="silver">Silver Tier (5% Discount)</option>
              <option value="gold">Gold Tier (10% VIP Discount)</option>
            </select>
          </div>

          {/* Credit Limit */}
          <div className="space-y-1.5">
            <label className="font-semibold text-[var(--text)] flex items-center gap-1.5">
              <CreditCard className="w-3.5 h-3.5 text-[var(--accent)]" />
              Authorized Credit Limit (INR)
            </label>
            <input
              type="number"
              min={0}
              step={1000}
              value={creditLimit}
              onChange={(e) => setCreditLimit(Number(e.target.value))}
              placeholder="0.00"
              className="w-full px-3 py-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] font-mono focus:outline-none focus:border-[var(--accent)]"
            />
          </div>
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--border)]">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text)]"
          >
            Cancel
          </button>
          <GlassButton
            variant="primary"
            disabled={isSubmitting || !name.trim()}
            className="flex items-center gap-2 font-bold"
          >
            <span>{isSubmitting ? "Converting..." : "Complete Conversion"}</span>
            <ArrowRight className="w-4 h-4" />
          </GlassButton>
        </div>
      </form>
    </GlassModal>
  );
}
