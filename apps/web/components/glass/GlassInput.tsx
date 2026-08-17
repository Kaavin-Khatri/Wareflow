"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface GlassInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
}

export const GlassInput = forwardRef<HTMLInputElement, GlassInputProps>(
  ({ className, icon, type, ...props }, ref) => {
    return (
      <div className="relative w-full">
        {icon && (
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] pointer-events-none w-4 h-4 flex items-center justify-center">
            {icon}
          </div>
        )}
        <input
          type={type}
          ref={ref}
          className={cn(
            "w-full rounded-xl bg-[var(--glass-bg)] backdrop-blur-md border border-[var(--glass-border)] px-3.5 py-2 text-xs text-[var(--text)] transition-all duration-200 placeholder:text-[var(--text-subtle)] outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent-subtle)] focus:shadow-[0_0_16px_-2px_var(--accent-glow)] disabled:cursor-not-allowed disabled:opacity-50",
            icon && "pl-10",
            className,
          )}
          {...props}
        />
      </div>
    );
  },
);

GlassInput.displayName = "GlassInput";
