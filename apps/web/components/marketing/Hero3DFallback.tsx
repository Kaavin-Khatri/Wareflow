"use client";

import React from "react";
import { Package, Sparkles, Layers } from "lucide-react";

export function Hero3DFallback() {
  return (
    <div
      className="relative w-full h-[380px] sm:h-[480px] rounded-3xl overflow-hidden border border-[var(--glass-border)] bg-[var(--glass-bg)] backdrop-blur-2xl flex items-center justify-center p-6 select-none"
      aria-label="Abstract Wholesale Inventory 3D Illustration"
    >
      {/* Background Accent Radial Glow */}
      <div
        aria-hidden="true"
        className="absolute inset-0 opacity-40"
        style={{
          background:
            "radial-gradient(circle at center, var(--accent) 0%, rgba(124, 58, 237, 0.1) 45%, transparent 70%)",
        }}
      />

      {/* Floating Isometric Glass Wireframe Abstraction */}
      <div className="relative z-10 flex flex-col items-center justify-center space-y-6">
        <div className="relative w-36 h-36 sm:w-48 sm:h-48 flex items-center justify-center">
          {/* Outer Rotating Halo Ring */}
          <div className="absolute inset-0 rounded-full border border-dashed border-[var(--accent-border)] animate-[spin_25s_linear_infinite]" />

          {/* Primary Glass Isometric Cube */}
          <div className="relative w-24 h-24 sm:w-32 sm:h-32 rounded-3xl bg-[var(--surface-elevated)] border-2 border-[var(--accent-border)] shadow-[0_0_40px_-6px_var(--accent-glow)] flex items-center justify-center transform rotate-12 hover:rotate-0 transition-transform duration-500">
            <Package className="w-10 h-10 sm:w-14 sm:h-14 text-[var(--accent)]" />
          </div>

          {/* Secondary Floating Satellite Badges */}
          <div className="absolute -top-3 -right-3 p-2 rounded-xl bg-[var(--surface)] border border-[var(--border-strong)] shadow-lg text-[var(--accent)]">
            <Sparkles className="w-4 h-4" />
          </div>
          <div className="absolute -bottom-2 -left-2 p-2 rounded-xl bg-[var(--surface)] border border-[var(--border-strong)] shadow-lg text-emerald-400">
            <Layers className="w-4 h-4" />
          </div>
        </div>

        {/* Live Status Pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--surface-hover)] border border-[var(--glass-border)] text-[11px] font-mono text-[var(--text-muted)]">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Real-Time Node Telemetry Active</span>
        </div>
      </div>
    </div>
  );
}
