"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

export type StatusBadgeVariant =
  "accent" | "neutral" | "success" | "warning" | "error" | "info" | "purple";

const statusBadgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-lg font-medium border select-none transition-colors",
  {
    variants: {
      variant: {
        accent:
          "bg-[var(--accent-subtle)] text-[var(--accent)] border-[var(--accent-border)] font-semibold shadow-sm",
        neutral: "bg-[var(--surface-hover)] text-[var(--text-muted)] border-[var(--border)]",
        success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        error: "bg-rose-500/10 text-rose-400 border-rose-500/20",
        info: "bg-sky-500/10 text-sky-400 border-sky-500/20",
        purple: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      },
      size: {
        sm: "px-2 py-0.5 text-[10px]",
        md: "px-2.5 py-0.5 text-[11px]",
        lg: "px-3 py-1 text-xs",
      },
    },
    defaultVariants: {
      variant: "neutral",
      size: "md",
    },
  },
);

export interface StatusConfig {
  variant: StatusBadgeVariant;
  label: string;
  dot?: boolean;
}

/**
 * Universal status-to-color mapping for all schema enums across WareFlow.
 * Normalized to lowercase string keys for robust matching.
 */
export const STATUS_MAP: Record<string, StatusConfig> = {
  // --- Purchase Orders (PO) ---
  draft: { variant: "neutral", label: "Draft", dot: false },
  submitted: { variant: "info", label: "Submitted", dot: true },
  confirmed: { variant: "accent", label: "Confirmed", dot: true },
  partially_received: { variant: "warning", label: "Partially Received", dot: true },
  received: { variant: "success", label: "Received", dot: true },
  po_cancelled: { variant: "error", label: "Cancelled", dot: false },

  // --- Sales Orders (SO) ---
  processing: { variant: "info", label: "Processing", dot: true },
  packed: { variant: "purple", label: "Packed", dot: true },
  dispatched: { variant: "accent", label: "Dispatched", dot: true },
  delivered: { variant: "success", label: "Delivered", dot: true },
  so_cancelled: { variant: "error", label: "Cancelled", dot: false },
  cancelled: { variant: "error", label: "Cancelled", dot: false },

  // --- Invoices ---
  issued: { variant: "info", label: "Issued", dot: true },
  paid: { variant: "success", label: "Paid", dot: true },
  partially_paid: { variant: "warning", label: "Partially Paid", dot: true },
  overdue: { variant: "error", label: "Overdue", dot: true },
  void: { variant: "neutral", label: "Void", dot: false },

  // --- Payments & Methods ---
  cash: { variant: "neutral", label: "Cash" },
  upi: { variant: "accent", label: "UPI" },
  neft_rtgs: { variant: "info", label: "NEFT / RTGS" },
  cheque: { variant: "purple", label: "Cheque" },
  credit: { variant: "warning", label: "Credit Balance" },

  // --- Deliveries ---
  scheduled: { variant: "neutral", label: "Scheduled", dot: true },
  in_transit: { variant: "accent", label: "In Transit", dot: true },
  failed: { variant: "error", label: "Failed", dot: true },

  // --- Returns (Sales & Purchase) ---
  requested: { variant: "warning", label: "Requested", dot: true },
  approved: { variant: "accent", label: "Approved", dot: true },
  rejected: { variant: "error", label: "Rejected", dot: false },
  completed: { variant: "success", label: "Completed", dot: true },

  // --- Item Conditions ---
  good: { variant: "success", label: "Good Condition" },
  damaged: { variant: "error", label: "Damaged" },
  expired: { variant: "error", label: "Expired" },
  seal_broken: { variant: "warning", label: "Seal Broken" },

  // --- Stock Levels & Inventory Movement ---
  in_stock: { variant: "success", label: "In Stock", dot: true },
  low_stock: { variant: "warning", label: "Low Stock", dot: true },
  out_of_stock: { variant: "error", label: "Out of Stock", dot: true },
  overstocked: { variant: "info", label: "Overstocked", dot: true },
  inward: { variant: "success", label: "Inward (+)" },
  outward: { variant: "accent", label: "Outward (-)" },
  adjustment: { variant: "warning", label: "Adjustment" },
  transfer: { variant: "purple", label: "Transfer" },

  // --- Recalls & Severity ---
  initiated: { variant: "warning", label: "Initiated", dot: true },
  low: { variant: "info", label: "Low Severity" },
  medium: { variant: "warning", label: "Medium Severity" },
  high: { variant: "error", label: "High Severity", dot: true },
  critical: { variant: "error", label: "Critical Hazard", dot: true },

  // --- Auth, 2FA & Staff Status ---
  active: { variant: "success", label: "Active", dot: true },
  suspended: { variant: "error", label: "Suspended", dot: true },
  invited: { variant: "warning", label: "Invited", dot: true },
  enrolled: { variant: "success", label: "2FA Enrolled", dot: true },
  not_enrolled: { variant: "warning", label: "2FA Inactive", dot: true },
  required: { variant: "error", label: "2FA Required", dot: true },
};

export function getStatusConfig(rawStatus: string): StatusConfig {
  const normalized = rawStatus
    .toLowerCase()
    .trim()
    .replace(/[\s-]+/g, "_");
  if (STATUS_MAP[normalized]) {
    return STATUS_MAP[normalized];
  }

  // Humanize unknown status strings fallback
  const label = rawStatus.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return {
    variant: "neutral",
    label,
    dot: false,
  };
}

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof statusBadgeVariants> {
  status: string;
  overrideLabel?: string;
  overrideVariant?: StatusBadgeVariant;
  dot?: boolean;
}

export function StatusBadge({
  status,
  overrideLabel,
  overrideVariant,
  dot,
  size,
  className,
  ...props
}: StatusBadgeProps) {
  const config = getStatusConfig(status);
  const resolvedVariant = overrideVariant || config.variant;
  const resolvedLabel = overrideLabel || config.label;
  const showDot = dot !== undefined ? dot : config.dot;

  return (
    <span
      className={cn(statusBadgeVariants({ variant: resolvedVariant, size }), className)}
      {...props}
    >
      {showDot && (
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full shrink-0",
            resolvedVariant === "accent" && "bg-[var(--accent)]",
            resolvedVariant === "neutral" && "bg-[var(--text-muted)]",
            resolvedVariant === "success" && "bg-emerald-400",
            resolvedVariant === "warning" && "bg-amber-400 animate-pulse",
            resolvedVariant === "error" && "bg-rose-400",
            resolvedVariant === "info" && "bg-sky-400",
            resolvedVariant === "purple" && "bg-purple-400",
          )}
        />
      )}
      <span>{resolvedLabel}</span>
    </span>
  );
}

export default StatusBadge;
