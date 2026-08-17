"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
}

export const GlassPanel = forwardRef<HTMLDivElement, GlassPanelProps>(
  ({ className, elevated = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative rounded-2xl transition-all duration-200 overflow-hidden",
          elevated
            ? "bg-[var(--glass-bg-elevated)] backdrop-blur-2xl border border-[var(--glass-border)] shadow-2xl"
            : "bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] shadow-[var(--glass-shadow)]",
          className,
        )}
        {...props}
      >
        {/* Specular Highlight Sheen */}
        <div
          aria-hidden="true"
          className="absolute inset-x-0 top-0 h-[1px] bg-[var(--glass-highlight)] pointer-events-none z-10"
        />

        <div className="relative z-10">{children}</div>
      </div>
    );
  },
);

GlassPanel.displayName = "GlassPanel";
