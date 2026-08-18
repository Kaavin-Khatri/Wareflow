"use client";

import React, { ReactNode } from "react";
import { PackageOpen } from "lucide-react";
import { FadeIn } from "./motion/GlassMotion";
import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  icon?: ReactNode;
  title?: string;
  description?: string;
  action?: ReactNode;
  secondaryAction?: ReactNode;
  compact?: boolean;
  className?: string;
}

export function EmptyState({
  icon,
  title = "No wholesale records found",
  description = "There are no records matching your current filter criteria or search query.",
  action,
  secondaryAction,
  compact = false,
  className,
}: EmptyStateProps) {
  return (
    <FadeIn
      className={cn(
        "flex flex-col items-center justify-center text-center rounded-2xl border border-[var(--border)] bg-[var(--surface-overlay)] select-none",
        compact ? "p-6 sm:p-8 space-y-3" : "p-8 sm:p-14 space-y-4",
        className,
      )}
    >
      {/* Frosted Icon Receptacle */}
      <div
        className={cn(
          "rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] flex items-center justify-center text-[var(--accent)] shadow-[0_0_20px_-4px_var(--accent-glow)] shrink-0",
          compact ? "w-10 h-10" : "w-14 h-14",
        )}
      >
        {icon || <PackageOpen className={compact ? "w-5 h-5" : "w-7 h-7"} />}
      </div>

      {/* Typography */}
      <div className="space-y-1 max-w-sm">
        <h3
          className={cn(
            "font-bold tracking-tight text-[var(--text)]",
            compact ? "text-sm" : "text-base",
          )}
        >
          {title}
        </h3>
        {description && (
          <p
            className={cn(
              "text-[var(--text-muted)] leading-relaxed",
              compact ? "text-xs" : "text-xs sm:text-sm",
            )}
          >
            {description}
          </p>
        )}
      </div>

      {/* Action Controls */}
      {(action || secondaryAction) && (
        <div className="flex items-center gap-3 pt-2 flex-wrap justify-center">
          {secondaryAction}
          {action}
        </div>
      )}
    </FadeIn>
  );
}

export default EmptyState;
