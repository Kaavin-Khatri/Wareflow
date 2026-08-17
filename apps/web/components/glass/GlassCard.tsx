"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
  glow?: boolean;
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, hoverable = false, glow = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative rounded-3xl bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] shadow-[var(--glass-shadow)] transition-all duration-300 overflow-hidden",
          hoverable &&
            "hover:border-[var(--border-strong)] hover:shadow-xl hover:-translate-y-0.5 group",
          glow && "shadow-[0_0_30px_-8px_var(--accent-glow)] border-[var(--accent-border)]",
          className,
        )}
        {...props}
      >
        {/* Light-Edge Specular Highlight Sheen */}
        <div
          aria-hidden="true"
          className="absolute inset-x-0 top-0 h-[1px] bg-[var(--glass-highlight)] pointer-events-none z-10"
        />

        {/* Perimeter Lens Refraction Gradient */}
        <div
          aria-hidden="true"
          className="absolute inset-0 rounded-[inherit] pointer-events-none opacity-40 group-hover:opacity-70 transition-opacity bg-gradient-to-b from-white/5 via-transparent to-black/5 dark:from-white/10 dark:to-transparent"
        />

        <div className="relative z-10">{children}</div>
      </div>
    );
  },
);

GlassCard.displayName = "GlassCard";

export const GlassCardHeader = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex flex-col space-y-1.5 p-6 border-b border-[var(--border)]", className)}
      {...props}
    />
  ),
);
GlassCardHeader.displayName = "GlassCardHeader";

export const GlassCardTitle = forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("font-bold text-base tracking-tight text-[var(--text)]", className)}
    {...props}
  />
));
GlassCardTitle.displayName = "GlassCardTitle";

export const GlassCardDescription = forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-xs text-[var(--text-muted)] leading-relaxed", className)}
    {...props}
  />
));
GlassCardDescription.displayName = "GlassCardDescription";

export const GlassCardContent = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn("p-6", className)} {...props} />,
);
GlassCardContent.displayName = "GlassCardContent";

export const GlassCardFooter = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex items-center p-6 pt-0 border-t border-[var(--border)] pt-4", className)}
      {...props}
    />
  ),
);
GlassCardFooter.displayName = "GlassCardFooter";
