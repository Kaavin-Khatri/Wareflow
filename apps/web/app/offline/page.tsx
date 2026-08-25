"use client";

import React from "react";
import Link from "next/link";
import { WifiOff, RefreshCw, Layers, ArrowLeft, Package, ArrowRightLeft } from "lucide-react";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";

export default function OfflinePage() {
  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--text)] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      <GlassCard className="max-w-md w-full p-8 text-center space-y-6 relative z-10 border-[var(--border)]">
        <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto shadow-inner">
          <WifiOff className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <h1 className="text-xl font-bold text-[var(--text)]">You are currently offline</h1>
          <p className="text-xs text-[var(--text-muted)] leading-relaxed">
            Warehouse connectivity is unavailable. You can continue browsing cached inventory and queuing floor operations.
          </p>
        </div>

        {/* Offline capabilities card */}
        <div className="p-4 rounded-2xl bg-[var(--surface-hover)] border border-[var(--border)] text-left space-y-2.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block">
            Offline Enabled Operations
          </span>
          <div className="space-y-2 text-xs text-[var(--text)]">
            <div className="flex items-center gap-2">
              <Package className="w-4 h-4 text-purple-400 shrink-0" />
              <span>Browse last-cached inventory & products</span>
            </div>
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Queue stock damage & recount adjustments</span>
            </div>
            <div className="flex items-center gap-2">
              <ArrowRightLeft className="w-4 h-4 text-cyan-400 shrink-0" />
              <span>Queue inter-warehouse stock transfers</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <GlassButton
            variant="secondary"
            size="md"
            onClick={handleRetry}
            className="w-full sm:w-auto font-semibold flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Check Connection</span>
          </GlassButton>
          <Link href="/admin/inventory" className="w-full sm:w-auto">
            <GlassButton
              variant="primary"
              size="md"
              className="w-full font-bold flex items-center justify-center gap-2 shadow-lg"
            >
              <span>View Cached Stock</span>
            </GlassButton>
          </Link>
        </div>
      </GlassCard>
    </div>
  );
}
