"use client";

import React, { ReactNode } from "react";
import Link from "next/link";
import { FadeIn } from "@/components/motion/GlassMotion";
import { ArrowLeft } from "lucide-react";

export interface DetailViewTemplateProps {
  /** Title of the record (e.g. PO #PO-2026-089) */
  title: string;
  /** Subtitle or identifier snippet */
  subtitle?: string;
  /** Link to navigate back to list */
  backHref: string;
  /** Label for back link (e.g. Back to Purchase Orders) */
  backLabel?: string;
  /** Primary status badge (e.g. GlassBadge variant="success") */
  statusBadge?: ReactNode;
  /** Primary action button (e.g. Dispatch Order, Pay Invoice) */
  primaryAction?: ReactNode;
  /** Secondary action buttons (e.g. Download PDF, Duplicate, Cancel) */
  secondaryActions?: ReactNode;
  /** Tab bar or sub-navigation header */
  tabs?: ReactNode;
  /** 8-Column Main Content (Line items, overview, ledger history) */
  children: ReactNode;
  /** 4-Column Sticky Side Panel (Metadata, supplier summary, audit info) */
  sidePanel: ReactNode;
}

export function DetailViewTemplate({
  title,
  subtitle,
  backHref,
  backLabel = "Back to List",
  statusBadge,
  primaryAction,
  secondaryActions,
  tabs,
  children,
  sidePanel,
}: DetailViewTemplateProps) {
  return (
    <FadeIn className="w-full space-y-6 pb-16">
      {/* 1. Back Navigation & Header */}
      <div className="space-y-3 border-b border-[var(--border)] pb-5">
        <Link
          href={backHref}
          className="inline-flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text)] transition-colors group"
        >
          <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
          <span>{backLabel}</span>
        </Link>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">{title}</h1>
              {statusBadge && <div>{statusBadge}</div>}
            </div>
            {subtitle && <p className="text-xs text-[var(--text-muted)] font-mono">{subtitle}</p>}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 flex-wrap">
            {secondaryActions}
            {primaryAction}
          </div>
        </div>

        {/* Optional Tabs */}
        {tabs && <div className="pt-2">{tabs}</div>}
      </div>

      {/* 2. 12-Column Responsive Split Layout */}
      <div className="grid grid-cols-12 gap-6 items-start">
        {/* 8-Column Main Workspace */}
        <div className="col-span-12 lg:col-span-8 space-y-6">{children}</div>

        {/* 4-Column Sticky Side Panel */}
        <div className="col-span-12 lg:col-span-4 space-y-6 lg:sticky lg:top-20">{sidePanel}</div>
      </div>
    </FadeIn>
  );
}
