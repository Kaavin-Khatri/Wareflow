"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { FadeIn } from "@/components/motion/GlassMotion";
import { AlertTriangle, RotateCcw, Home } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global runtime error caught by error boundary:", error);
  }, [error]);

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <FadeIn className="w-full max-w-lg">
        <GlassCard className="p-8 sm:p-10 text-center space-y-6 relative overflow-hidden border-rose-500/20 shadow-2xl">
          {/* Status Indicator */}
          <div className="mx-auto inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-xs font-mono font-semibold text-rose-400 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse" />
            SYSTEM EXCEPTION
          </div>

          {/* Icon */}
          <div className="mx-auto w-16 h-16 rounded-3xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 shadow-[0_0_30px_-4px_rgba(244,63,94,0.3)]">
            <AlertTriangle className="w-8 h-8" />
          </div>

          {/* Description */}
          <div className="space-y-2 max-w-sm mx-auto">
            <h1 className="text-xl sm:text-2xl font-bold text-[var(--text)] tracking-tight">
              Warehouse Processing Interrupted
            </h1>
            <p className="text-xs sm:text-sm text-[var(--text-muted)] leading-relaxed">
              An unexpected runtime exception occurred while rendering this view. Your database transactions and local offline queue remain intact.
            </p>
            {error?.message && (
              <p className="p-2.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)] text-[11px] font-mono text-rose-400/90 break-all text-left">
                {error.message}
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <GlassButton
              variant="primary"
              onClick={() => reset()}
              className="w-full sm:w-auto gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Retry Operation</span>
            </GlassButton>

            <Link href="/dashboard" className="w-full sm:w-auto">
              <GlassButton variant="secondary" className="w-full gap-2">
                <Home className="w-4 h-4" />
                <span>Return to Dashboard</span>
              </GlassButton>
            </Link>
          </div>
        </GlassCard>
      </FadeIn>
    </div>
  );
}
