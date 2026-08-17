"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const glassBadgeVariants = cva(
  "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[11px] font-medium border transition-colors select-none",
  {
    variants: {
      variant: {
        accent:
          "bg-[var(--accent-subtle)] text-[var(--accent)] border-[var(--accent-border)] font-semibold shadow-sm",
        neutral: "bg-[var(--surface-hover)] text-[var(--text-muted)] border-[var(--border)]",
        success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        error: "bg-rose-500/10 text-rose-400 border-rose-500/20",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  },
);

export interface GlassBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof glassBadgeVariants> {
  dot?: boolean;
}

export function GlassBadge({
  className,
  variant,
  dot = false,
  children,
  ...props
}: GlassBadgeProps) {
  return (
    <span className={cn(glassBadgeVariants({ variant }), className)} {...props}>
      {dot && (
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full shrink-0",
            variant === "accent" && "bg-[var(--accent)]",
            variant === "neutral" && "bg-[var(--text-muted)]",
            variant === "success" && "bg-emerald-400",
            variant === "warning" && "bg-amber-400",
            variant === "error" && "bg-rose-400",
          )}
        />
      )}
      {children}
    </span>
  );
}
