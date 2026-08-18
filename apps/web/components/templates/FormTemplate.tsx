"use client";

import React, { ReactNode } from "react";
import Link from "next/link";
import { GlassButton } from "@/components/glass/GlassButton";
import { FadeIn } from "@/components/motion/GlassMotion";
import { ArrowLeft, Check, Loader2 } from "lucide-react";

export interface FormTemplateProps {
  /** Form title (e.g. Add Wholesale Product, Edit Supplier Profile) */
  title: string;
  /** Subtitle or instructions */
  description?: string;
  /** Link to cancel / navigate back */
  backHref: string;
  /** Label for back link */
  backLabel?: string;
  /** Form submission handler */
  onSubmit?: (e: React.FormEvent) => void;
  /** Form fields and grouped sections */
  children: ReactNode;
  /** Submit button text */
  submitLabel?: string;
  /** Discard button text */
  discardLabel?: string;
  /** Callback for discard button */
  onDiscard?: () => void;
  /** Loading/submitting state */
  isSubmitting?: boolean;
  /** Status or validation feedback string */
  statusFeedback?: string;
  /** Whether the form has unsaved changes */
  isDirty?: boolean;
  /** Custom extra actions for the bottom bar */
  extraActions?: ReactNode;
}

export function FormTemplate({
  title,
  description,
  backHref,
  backLabel = "Cancel & Back",
  onSubmit,
  children,
  submitLabel = "Save Changes",
  discardLabel = "Discard",
  onDiscard,
  isSubmitting = false,
  statusFeedback,
  isDirty = false,
  extraActions,
}: FormTemplateProps) {
  return (
    <FadeIn className="w-full max-w-4xl mx-auto space-y-8 pb-32">
      {/* 1. Header */}
      <div className="space-y-2 border-b border-[var(--border)] pb-5">
        <Link
          href={backHref}
          className="inline-flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text)] transition-colors group mb-1"
        >
          <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
          <span>{backLabel}</span>
        </Link>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">{title}</h1>
        {description && <p className="text-xs text-[var(--text-muted)]">{description}</p>}
      </div>

      {/* 2. Grouped Form Content */}
      <form onSubmit={onSubmit} className="space-y-8">
        {children}

        {/* 3. Sticky Bottom Action Bar */}
        <div className="fixed bottom-0 inset-x-0 z-40 bg-[var(--surface-overlay)] backdrop-blur-2xl border-t border-[var(--glass-border)] py-4 px-6 shadow-2xl">
          <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
            {/* Status / Dirty Indicator */}
            <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
              {isDirty ? (
                <span className="flex items-center gap-1.5 text-amber-500 font-medium">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  Unsaved changes
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-[var(--text-subtle)]">
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  {statusFeedback || "All changes synced"}
                </span>
              )}
            </div>

            {/* Buttons */}
            <div className="flex items-center gap-3">
              {extraActions}

              {onDiscard ? (
                <GlassButton
                  type="button"
                  variant="ghost"
                  size="md"
                  onClick={onDiscard}
                  disabled={isSubmitting}
                >
                  {discardLabel}
                </GlassButton>
              ) : (
                <Link href={backHref}>
                  <GlassButton type="button" variant="ghost" size="md" disabled={isSubmitting}>
                    {discardLabel}
                  </GlassButton>
                </Link>
              )}

              <GlassButton
                type="submit"
                variant="primary"
                size="md"
                disabled={isSubmitting}
                className="min-w-[140px]"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
                    Saving...
                  </>
                ) : (
                  <>
                    {submitLabel}
                    <span className="ml-1.5 text-[10px] opacity-70 border border-white/20 rounded px-1 py-0.5 hidden sm:inline">
                      ⌘S
                    </span>
                  </>
                )}
              </GlassButton>
            </div>
          </div>
        </div>
      </form>
    </FadeIn>
  );
}

export interface FormSectionProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

/**
 * Reusable card section for grouping related fields inside FormTemplate.
 */
export function FormSection({ title, description, children, className = "" }: FormSectionProps) {
  return (
    <div
      className={`p-6 rounded-3xl bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] space-y-5 ${className}`}
    >
      <div className="border-b border-[var(--border)] pb-3">
        <h2 className="text-sm font-bold text-[var(--text)] tracking-tight">{title}</h2>
        {description && <p className="text-xs text-[var(--text-muted)] mt-0.5">{description}</p>}
      </div>
      <div className="grid grid-cols-12 gap-4">{children}</div>
    </div>
  );
}
