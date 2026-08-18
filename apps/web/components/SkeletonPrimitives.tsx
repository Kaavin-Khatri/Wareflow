"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export function SkeletonBox({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl bg-[var(--surface-hover)] before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.8s_infinite] before:bg-gradient-to-r before:from-transparent before:via-[var(--border-strong)] before:to-transparent",
        className,
      )}
      {...props}
    />
  );
}

export function SkeletonText({ lines = 2, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("space-y-2 w-full", className)}>
      {Array.from({ length: lines }).map((_, idx) => (
        <SkeletonBox
          key={idx}
          className={cn("h-3.5 rounded-md", idx === lines - 1 && lines > 1 ? "w-3/4" : "w-full")}
        />
      ))}
    </div>
  );
}

export function SkeletonBadge({ className }: SkeletonProps) {
  return <SkeletonBox className={cn("h-5 w-16 rounded-md", className)} />;
}

export function SkeletonCard({
  variant = "kpi",
  className,
}: {
  variant?: "kpi" | "detail" | "table";
  className?: string;
}) {
  if (variant === "kpi") {
    return (
      <div
        className={cn(
          "p-5 rounded-2xl border border-[var(--border)] bg-[var(--surface-overlay)] space-y-3",
          className,
        )}
      >
        <div className="flex items-center justify-between">
          <SkeletonBox className="h-3 w-28" />
          <SkeletonBox className="h-7 w-7 rounded-lg" />
        </div>
        <SkeletonBox className="h-7 w-36" />
        <SkeletonBox className="h-3 w-20" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface-overlay)] space-y-4",
        className,
      )}
    >
      <div className="flex items-center justify-between">
        <SkeletonBox className="h-5 w-44" />
        <SkeletonBadge />
      </div>
      <SkeletonText lines={3} />
      <div className="pt-2 flex gap-3">
        <SkeletonBox className="h-9 w-24 rounded-xl" />
        <SkeletonBox className="h-9 w-24 rounded-xl" />
      </div>
    </div>
  );
}

export function SkeletonTable({
  rows = 5,
  cols = 5,
  className,
}: {
  rows?: number;
  cols?: number;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "w-full rounded-2xl border border-[var(--border)] bg-[var(--surface-overlay)] overflow-hidden",
        className,
      )}
    >
      {/* Table Header Skeleton */}
      <div className="p-4 border-b border-[var(--border)] flex items-center justify-between gap-4 bg-[var(--surface-hover)]">
        {Array.from({ length: cols }).map((_, cIdx) => (
          <SkeletonBox
            key={cIdx}
            className={cn(
              "h-3.5",
              cIdx === 0 ? "w-28" : cIdx === cols - 1 ? "w-16 ml-auto" : "w-20",
            )}
          />
        ))}
      </div>

      {/* Table Rows Skeleton */}
      <div className="divide-y divide-[var(--border)]">
        {Array.from({ length: rows }).map((_, rIdx) => (
          <div key={rIdx} className="p-4 flex items-center justify-between gap-4">
            {Array.from({ length: cols }).map((_, cIdx) => (
              <div
                key={cIdx}
                className={cn(
                  "flex items-center",
                  cIdx === cols - 1 ? "justify-end" : "justify-start",
                  cIdx === 0 ? "w-28" : "w-20",
                )}
              >
                {cIdx === cols - 2 ? (
                  <SkeletonBadge />
                ) : cIdx === cols - 1 ? (
                  <SkeletonBox className="h-7 w-16 rounded-lg" />
                ) : (
                  <SkeletonBox className={cn("h-3.5", cIdx === 0 ? "w-24 font-bold" : "w-16")} />
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export default SkeletonCard;
