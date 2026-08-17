"use client";

import React, { forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const glassButtonVariants = cva(
  "relative inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium text-xs tracking-tight transition-all duration-200 select-none cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-40 will-change-transform active:scale-[0.97] group overflow-hidden",
  {
    variants: {
      variant: {
        primary:
          "bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] text-white border border-[var(--accent-border)] shadow-[0_0_20px_-4px_var(--accent-glow)] hover:shadow-[0_0_28px_0px_var(--accent-glow)] hover:brightness-105 active:brightness-95",
        secondary:
          "bg-[var(--glass-bg)] text-[var(--text)] backdrop-blur-md border border-[var(--glass-border)] shadow-[var(--glass-shadow)] hover:bg-[var(--surface-hover)] hover:border-[var(--border-strong)] active:bg-[var(--surface)]",
        outline:
          "bg-transparent text-[var(--text)] border border-[var(--border)] hover:bg-[var(--glass-bg)] hover:border-[var(--accent-border)] hover:text-[var(--accent)]",
        ghost:
          "bg-transparent text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent",
        destructive:
          "bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 hover:border-rose-500/40 shadow-sm",
      },
      size: {
        sm: "h-8 px-3 rounded-xl text-[11px]",
        md: "h-9 px-4 rounded-xl text-xs",
        lg: "h-11 px-5 rounded-2xl text-sm font-semibold",
        icon: "h-9 w-9 p-0 rounded-xl flex items-center justify-center",
        iconSm: "h-7 w-7 p-0 rounded-lg flex items-center justify-center text-xs",
      },
    },
    defaultVariants: {
      variant: "secondary",
      size: "md",
    },
  },
);

export interface GlassButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof glassButtonVariants> {
  asChild?: boolean;
}

export const GlassButton = forwardRef<HTMLButtonElement, GlassButtonProps>(
  ({ className, variant, size, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(glassButtonVariants({ variant, size, className }))}
        {...props}
      >
        {/* Specular Refraction Top Sheen Layer */}
        <span
          aria-hidden="true"
          className="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-white/40 dark:via-white/20 to-transparent pointer-events-none transition-opacity duration-300 opacity-80 group-hover:opacity-100 group-hover:h-[1.5px]"
        />

        {/* Optical Glass Perimeter Lensing Highlight */}
        <span
          aria-hidden="true"
          className="absolute inset-0 rounded-[inherit] pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-b from-white/10 to-transparent dark:from-white/5"
        />

        {/* Button Content */}
        <span className="relative z-10 flex items-center gap-2">{children}</span>
      </button>
    );
  },
);

GlassButton.displayName = "GlassButton";
