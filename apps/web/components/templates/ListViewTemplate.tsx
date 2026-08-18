"use client";

import React, { ReactNode } from "react";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassInput } from "@/components/glass/GlassInput";
import { GlassButton } from "@/components/glass/GlassButton";
import { FadeIn } from "@/components/motion/GlassMotion";
import { Search, X } from "lucide-react";

export interface ListViewTemplateProps {
  /** Title of the list view screen */
  title: string;
  /** Subtitle or description */
  description?: string;
  /** Optional top status badge or count */
  badge?: ReactNode;
  /** Primary call-to-action button (e.g. + Add Product) */
  primaryAction?: ReactNode;
  /** Secondary action buttons (e.g. Export CSV, Import) */
  secondaryActions?: ReactNode;
  /** Search query state */
  searchQuery?: string;
  /** Callback when search input changes */
  onSearchChange?: (query: string) => void;
  /** Placeholder text for search bar */
  searchPlaceholder?: string;
  /** Filter component slots (e.g. category dropdown, status chips) */
  filters?: ReactNode;
  /** Count of active filters */
  activeFilterCount?: number;
  /** Callback to clear all active filters */
  onClearFilters?: () => void;
  /** Bulk selection banner (renders when 1 or more items are selected) */
  bulkActions?: ReactNode;
  /** Main table or grid content */
  children: ReactNode;
  /** Pagination controls slot */
  pagination?: ReactNode;
  /** Optional stats or summary bar rendered between header and filters */
  statsBar?: ReactNode;
}

export function ListViewTemplate({
  title,
  description,
  badge,
  primaryAction,
  secondaryActions,
  searchQuery = "",
  onSearchChange,
  searchPlaceholder = "Search records, SKU, or identifiers...",
  filters,
  activeFilterCount = 0,
  onClearFilters,
  bulkActions,
  children,
  pagination,
  statsBar,
}: ListViewTemplateProps) {
  return (
    <FadeIn className="w-full space-y-6">
      {/* 1. Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">{title}</h1>
            {badge && <div>{badge}</div>}
          </div>
          {description && (
            <p className="text-xs text-[var(--text-muted)] max-w-2xl">{description}</p>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {secondaryActions}
          {primaryAction}
        </div>
      </div>

      {/* 2. Optional Stats Summary Bar */}
      {statsBar && <div>{statsBar}</div>}

      {/* 3. Sticky Filter & Search Toolbar */}
      <div className="sticky top-16 z-20 backdrop-blur-xl bg-[var(--surface-overlay)] border border-[var(--glass-border)] rounded-2xl p-3 shadow-sm transition-all">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[240px]">
            <GlassInput
              value={searchQuery}
              onChange={(e) => onSearchChange?.(e.target.value)}
              placeholder={searchPlaceholder}
              icon={<Search className="w-4 h-4 text-[var(--text-muted)]" />}
              className="w-full text-xs"
            />
          </div>

          {/* Filter Slots & Clear Filter */}
          <div className="flex items-center gap-2 flex-wrap">
            {filters}

            {activeFilterCount > 0 && onClearFilters && (
              <GlassButton
                variant="ghost"
                size="sm"
                onClick={onClearFilters}
                className="text-xs text-[var(--text-muted)] hover:text-[var(--text)]"
              >
                <X className="w-3.5 h-3.5" />
                Clear Filters ({activeFilterCount})
              </GlassButton>
            )}
          </div>
        </div>

        {/* Bulk Actions Banner (appears when items are selected) */}
        {bulkActions && (
          <div className="mt-3 pt-3 border-t border-[var(--border)] flex items-center justify-between animate-in fade-in slide-in-from-top-1 duration-200">
            {bulkActions}
          </div>
        )}
      </div>

      {/* 4. Main Data Table or Card Grid */}
      <GlassCard className="p-0 overflow-hidden border-[var(--glass-border)]">
        <div className="overflow-x-auto">{children}</div>
      </GlassCard>

      {/* 5. Pagination Bar */}
      {pagination && <div className="flex items-center justify-between pt-2">{pagination}</div>}
    </FadeIn>
  );
}
