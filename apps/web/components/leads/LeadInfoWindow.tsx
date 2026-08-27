"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  MapPin,
  Phone,
  ExternalLink,
  CheckCircle2,
  Sparkles,
  X,
  Store,
  UtensilsCrossed,
  ShoppingBag,
  Building2,
  Calendar,
  MessageSquare,
  UserPlus,
  ArrowUpRight,
} from "lucide-react";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";

export interface LeadItem {
  id: string;
  place_id: string;
  name: string;
  category: "gruh_udyog" | "snack_store" | "grocery_kirana" | "other" | string;
  address?: string | null;
  lat?: number | null;
  lng?: number | null;
  phone?: string | null;
  rating?: number | null;
  user_ratings_total?: number | null;
  google_maps_url?: string | null;
  first_seen_at?: string | null;
  is_new: boolean;
  contacted: boolean;
  notes?: string | null;
  contact_notes?: string | null;
  converted_retailer_id?: string | null;
  created_at?: string | null;
}

export interface LeadInfoWindowProps {
  lead: LeadItem;
  onClose?: () => void;
  onMarkContacted?: (leadId: string, notes?: string) => Promise<void>;
  onOpenConvertModal?: (lead: LeadItem) => void;
  isCompact?: boolean;
}

export function getCategoryMetadata(category: string) {
  switch (category) {
    case "gruh_udyog":
      return {
        label: "Gruh Udyog",
        color: "#F59E0B",
        badgeVariant: "warning" as const,
        icon: UtensilsCrossed,
        bgClass: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      };
    case "snack_store":
      return {
        label: "Snack / Namkeen",
        color: "#F43F5E",
        badgeVariant: "error" as const,
        icon: Store,
        bgClass: "bg-rose-500/10 text-rose-400 border-rose-500/20",
      };
    case "grocery_kirana":
      return {
        label: "Kirana / Grocery",
        color: "#10B981",
        badgeVariant: "success" as const,
        icon: ShoppingBag,
        bgClass: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      };
    default:
      return {
        label: "Retail Shop",
        color: "#8B5CF6",
        badgeVariant: "accent" as const,
        icon: Building2,
        bgClass: "bg-violet-500/10 text-violet-400 border-violet-500/20",
      };
  }
}

export function LeadInfoWindow({
  lead,
  onClose,
  onMarkContacted,
  onOpenConvertModal,
  isCompact = false,
}: LeadInfoWindowProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showNotesInput, setShowNotesInput] = useState(false);
  const [notes, setNotes] = useState(lead.contact_notes || "");

  const catMeta = getCategoryMetadata(lead.category);
  const IconComponent = catMeta.icon;

  const handleContactSubmit = async () => {
    if (!onMarkContacted) return;
    setIsSubmitting(true);
    try {
      await onMarkContacted(lead.id, notes);
      setShowNotesInput(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formattedDate = lead.first_seen_at
    ? new Date(lead.first_seen_at).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : null;

  const mapsUrl =
    lead.google_maps_url ||
    `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
      `${lead.name} ${lead.address || ""}`,
    )}`;

  const isConverted = Boolean(lead.converted_retailer_id);

  return (
    <div
      className={`relative rounded-2xl bg-[var(--surface-overlay)] backdrop-blur-xl border border-[var(--glass-border)] shadow-2xl p-4 text-[var(--text)] select-text transition-all ${
        isCompact ? "max-w-sm" : "w-full max-w-md"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-2.5 min-w-0">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-0.5 border"
            style={{
              backgroundColor: `${catMeta.color}15`,
              borderColor: `${catMeta.color}30`,
              color: catMeta.color,
            }}
          >
            <IconComponent className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-bold text-sm text-[var(--text)] tracking-tight leading-snug truncate">
                {lead.name}
              </h3>
              {lead.is_new && !lead.contacted && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-gradient-to-r from-amber-500 to-orange-500 text-black shadow-[0_0_12px_rgba(245,158,11,0.5)] animate-pulse">
                  <Sparkles className="w-2.5 h-2.5" />
                  New
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span
                className={`text-[10px] px-2 py-0.5 rounded-md font-medium border ${catMeta.bgClass}`}
              >
                {catMeta.label}
              </span>
              {lead.contacted && (
                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-medium bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                  <CheckCircle2 className="w-3 h-3" />
                  Contacted
                </span>
              )}
              {isConverted && (
                <span className="inline-flex items-center gap-1 text-[10px] text-cyan-400 font-bold bg-cyan-500/10 px-2 py-0.5 rounded-md border border-cyan-500/30 shadow-[0_0_10px_rgba(6,182,212,0.2)]">
                  <Store className="w-3 h-3 text-cyan-400" />
                  Converted Retailer
                </span>
              )}
            </div>
          </div>
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close lead info"
            className="p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Address & Meta */}
      <div className="space-y-2 py-2 border-y border-[var(--glass-border)] text-xs text-[var(--text-muted)]">
        {lead.address && (
          <div className="flex items-start gap-2">
            <MapPin className="w-3.5 h-3.5 text-[var(--text-subtle)] shrink-0 mt-0.5" />
            <span className="leading-relaxed text-[var(--text)]">{lead.address}</span>
          </div>
        )}

        {formattedDate && (
          <div className="flex items-center gap-2 text-[11px] text-[var(--text-subtle)] font-mono">
            <Calendar className="w-3.5 h-3.5 shrink-0" />
            <span>Discovered: {formattedDate}</span>
          </div>
        )}

        {lead.contact_notes && (
          <div className="p-2.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)] text-[11px]">
            <div className="flex items-center gap-1.5 font-semibold text-[var(--text)] mb-1">
              <MessageSquare className="w-3 h-3 text-[var(--accent)]" />
              <span>Contact Notes</span>
            </div>
            <p className="text-[var(--text-muted)] italic leading-relaxed">
              &quot;{lead.contact_notes}&quot;
            </p>
          </div>
        )}
      </div>

      {/* Contact Notes Inline Form */}
      {showNotesInput && (
        <div className="my-3 p-3 rounded-xl bg-[var(--surface-hover)] border border-[var(--accent-border)] space-y-2">
          <label
            htmlFor={`notes-${lead.id}`}
            className="text-[11px] font-bold text-[var(--text)] block"
          >
            Record Contact Outcome / Notes:
          </label>
          <textarea
            id={`notes-${lead.id}`}
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Spoke to proprietor Ramesh-bhai, sent catalogue & price list on WhatsApp"
            className="w-full text-xs p-2 rounded-lg bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] placeholder-[var(--text-subtle)] focus:outline-none focus:border-[var(--accent)]"
          />
          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowNotesInput(false)}
              className="text-xs px-2.5 py-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text)]"
            >
              Cancel
            </button>
            <GlassButton
              size="sm"
              variant="primary"
              onClick={handleContactSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Saving..." : "Save Contacted Status"}
            </GlassButton>
          </div>
        </div>
      )}

      {/* Primary Action Buttons */}
      <div className="space-y-2 mt-3">
        <div className="flex items-center gap-2 flex-wrap">
          {lead.phone && (
            <a
              href={`tel:${lead.phone}`}
              className="flex-1 min-w-[110px] inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25 transition-all shadow-sm active:scale-95"
            >
              <Phone className="w-3.5 h-3.5" />
              <span>Call ({lead.phone})</span>
            </a>
          )}

          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 min-w-[110px] inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-[var(--surface-hover)] text-[var(--text)] border border-[var(--border)] hover:bg-[var(--surface-active)] transition-all active:scale-95"
          >
            <ExternalLink className="w-3.5 h-3.5 text-[var(--text-muted)]" />
            <span>Directions</span>
          </a>
        </div>

        {/* Growth actions: Mark Contacted / Convert to Retailer */}
        <div className="pt-1 space-y-1.5">
          {!lead.contacted && onMarkContacted && !showNotesInput && (
            <button
              type="button"
              onClick={() => setShowNotesInput(true)}
              className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-[var(--text)] hover:bg-[var(--surface-hover)] border border-[var(--border)] transition-colors"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Mark as Contacted</span>
            </button>
          )}

          {isConverted ? (
            <Link
              href={
                lead.converted_retailer_id
                  ? `/admin/retailers/${lead.converted_retailer_id}/ledger`
                  : "/admin/retailers"
              }
              className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/25 transition-all"
            >
              <Store className="w-3.5 h-3.5" />
              <span>View Retailer Account</span>
              <ArrowUpRight className="w-3.5 h-3.5 ml-0.5" />
            </Link>
          ) : (
            <GlassButton
              variant="primary"
              size="sm"
              onClick={() => onOpenConvertModal && onOpenConvertModal(lead)}
              className="w-full flex items-center justify-center gap-1.5 font-bold shadow-md"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Convert to Wholesale Retailer</span>
            </GlassButton>
          )}
        </div>
      </div>
    </div>
  );
}
