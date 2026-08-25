"use client";

import React, { useState, useMemo, ReactNode } from "react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { GlassCard } from "./glass/GlassCard";
import { EmptyState } from "./EmptyState";
import { SkeletonTable } from "./SkeletonPrimitives";
import { cn } from "@/lib/utils";

export type SortDirection = "asc" | "desc" | null;

export interface DataTableColumn<T> {
  key: string;
  header: ReactNode;
  render?: (item: T, index: number) => ReactNode;
  sortable?: boolean;
  sortFn?: (a: T, b: T) => number;
  align?: "left" | "center" | "right";
  width?: string;
  mobilePrimary?: boolean; // Highlighted title in mobile card
  mobileHide?: boolean; // Omit from mobile key-value list
  mobileLabel?: string; // Custom label for mobile card row
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  keyExtractor: (item: T, index: number) => string;
  isLoading?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: ReactNode;
  emptyIcon?: ReactNode;
  onRowClick?: (item: T) => void;
  className?: string;
  mobileBreakpoint?: "sm" | "md" | "lg";
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  isLoading = false,
  emptyTitle = "No records found",
  emptyDescription = "There are no records matching your active criteria.",
  emptyAction,
  emptyIcon,
  onRowClick,
  className,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [tbodyRef] = useAutoAnimate();
  const [mobileCardsRef] = useAutoAnimate();

  const handleSort = (column: DataTableColumn<T>) => {
    if (!column.sortable) return;

    if (sortKey !== column.key) {
      setSortKey(column.key);
      setSortDirection("asc");
    } else if (sortDirection === "asc") {
      setSortDirection("desc");
    } else if (sortDirection === "desc") {
      setSortKey(null);
      setSortDirection(null);
    }
  };

  const sortedData = useMemo(() => {
    if (!sortKey || !sortDirection) return data;

    const column = columns.find((c) => c.key === sortKey);
    if (!column) return data;

    return [...data].sort((a, b) => {
      if (column.sortFn) {
        const res = column.sortFn(a, b);
        return sortDirection === "asc" ? res : -res;
      }

      const valA = (a as Record<string, unknown>)[sortKey];
      const valB = (b as Record<string, unknown>)[sortKey];

      if (valA == null && valB == null) return 0;
      if (valA == null) return 1;
      if (valB == null) return -1;

      if (typeof valA === "number" && typeof valB === "number") {
        return sortDirection === "asc" ? valA - valB : valB - valA;
      }

      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();
      if (strA < strB) return sortDirection === "asc" ? -1 : 1;
      if (strA > strB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
  }, [data, sortKey, sortDirection, columns]);

  // Loading State
  if (isLoading) {
    return <SkeletonTable rows={5} cols={columns.length} className={className} />;
  }

  // Empty State
  if (sortedData.length === 0) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        action={emptyAction}
        icon={emptyIcon}
        className={className}
      />
    );
  }

  // Identify Mobile Primary Column
  const primaryCol = columns.find((c) => c.mobilePrimary) || columns[0];
  const otherCols = columns.filter((c) => c !== primaryCol && !c.mobileHide);
  const actionCol = columns.find(
    (c) => c.key === "action" || c.key === "actions" || c.align === "right",
  );

  return (
    <div className={cn("w-full space-y-4", className)}>
      {/* 1. Desktop & Tablet View: Structured Frosted Data Table */}
      <div className="hidden md:block w-full overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface-overlay)]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[var(--border)] bg-[var(--surface-hover)] text-[var(--text-muted)] select-none">
                {columns.map((col) => {
                  const isSorted = sortKey === col.key;
                  return (
                    <th
                      key={col.key}
                      style={{ width: col.width }}
                      onClick={() => handleSort(col)}
                      className={cn(
                        "p-3.5 font-bold uppercase tracking-wider text-[10px] font-mono",
                        col.sortable &&
                          "cursor-pointer hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors",
                        col.align === "right" && "text-right",
                        col.align === "center" && "text-center",
                      )}
                    >
                      <div
                        className={cn(
                          "inline-flex items-center gap-1.5",
                          col.align === "right" && "justify-end w-full",
                          col.align === "center" && "justify-center w-full",
                        )}
                      >
                        <span>{col.header}</span>
                        {col.sortable && (
                          <span className="text-[var(--text-subtle)]">
                            {isSorted && sortDirection === "asc" ? (
                              <ArrowUp className="w-3 h-3 text-[var(--accent)]" />
                            ) : isSorted && sortDirection === "desc" ? (
                              <ArrowDown className="w-3 h-3 text-[var(--accent)]" />
                            ) : (
                              <ArrowUpDown className="w-3 h-3 opacity-40 hover:opacity-100" />
                            )}
                          </span>
                        )}
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody ref={tbodyRef} className="divide-y divide-[var(--border)]">
              {sortedData.map((item, idx) => (
                <tr
                  key={keyExtractor(item, idx)}
                  onClick={() => onRowClick && onRowClick(item)}
                  tabIndex={onRowClick ? 0 : undefined}
                  onKeyDown={(e) => {
                    if (onRowClick && (e.key === "Enter" || e.key === " ")) {
                      e.preventDefault();
                      onRowClick(item);
                    }
                  }}
                  className={cn(
                    "hover:bg-[var(--surface-hover)] transition-colors relative group",
                    onRowClick &&
                      "cursor-pointer focus-visible:bg-[var(--surface-hover)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-[var(--accent)]",
                  )}
                >
                  {columns.map((col) => {
                    const rawVal = (item as Record<string, unknown>)[col.key];
                    const content: ReactNode = col.render
                      ? col.render(item, idx)
                      : rawVal != null
                        ? String(rawVal)
                        : "—";

                    return (
                      <td
                        key={col.key}
                        className={cn(
                          "p-3.5 align-middle transition-colors",
                          col.align === "right" && "text-right font-mono tabular-nums tracking-tight",
                          col.align === "center" && "text-center",
                        )}
                      >
                        {content}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Mobile Responsive Card View (Auto-Restructured below md/768px) */}
      <div ref={mobileCardsRef} className="block md:hidden space-y-3">
        {sortedData.map((item, idx) => {
          const rawPrimary = (item as Record<string, unknown>)[primaryCol.key];
          const primaryContent: ReactNode = primaryCol.render
            ? primaryCol.render(item, idx)
            : rawPrimary != null
              ? String(rawPrimary)
              : "—";

          return (
            <GlassCard
              key={keyExtractor(item, idx)}
              hoverable={Boolean(onRowClick)}
              onClick={() => onRowClick && onRowClick(item)}
              className="p-4 space-y-3 text-xs"
            >
              {/* Primary Header Row */}
              <div className="flex items-start justify-between gap-2 pb-2.5 border-b border-[var(--border)]">
                <div className="font-bold text-[var(--text)] text-sm">{primaryContent}</div>
              </div>

              {/* Key-Value Detail Grid */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                {otherCols
                  .filter((c) => c !== actionCol)
                  .map((col) => {
                    const rawVal = (item as Record<string, unknown>)[col.key];
                    const cellContent: ReactNode = col.render
                      ? col.render(item, idx)
                      : rawVal != null
                        ? String(rawVal)
                        : "—";

                    return (
                      <div key={col.key} className="space-y-0.5 min-w-0">
                        <span className="text-[10px] text-[var(--text-subtle)] uppercase tracking-wider font-mono block">
                          {col.mobileLabel ||
                            (typeof col.header === "string" ? col.header : col.key)}
                        </span>
                        <div className="text-[var(--text)] font-medium truncate">{cellContent}</div>
                      </div>
                    );
                  })}
              </div>

              {/* Action Buttons Row */}
              {actionCol && (
                <div className="pt-2 border-t border-[var(--border)] flex items-center justify-end gap-2">
                  {actionCol.render
                    ? actionCol.render(item, idx)
                    : (item as Record<string, unknown>)[actionCol.key] != null
                      ? String((item as Record<string, unknown>)[actionCol.key])
                      : null}
                </div>
              )}
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}

export default DataTable;
