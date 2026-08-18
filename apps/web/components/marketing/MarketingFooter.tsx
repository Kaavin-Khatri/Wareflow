"use client";

import React from "react";
import Link from "next/link";
import { GlassBadge } from "@/components/glass";

export function MarketingFooter() {
  return (
    <footer className="border-t border-[var(--glass-border)] bg-[var(--surface-elevated)] backdrop-blur-xl mt-24 py-12 px-4 sm:px-6">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-[var(--text-muted)]">
        {/* Brand & Mission */}
        <div className="flex flex-col sm:flex-row items-center gap-3 text-center sm:text-left">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] flex items-center justify-center text-white font-black text-xs">
              W
            </div>
            <span className="font-bold text-[var(--text)]">WareFlow ERP</span>
          </div>
          <span className="hidden sm:inline">•</span>
          <span>Next-Generation Wholesale Inventory & Order Telemetry</span>
        </div>

        {/* Links */}
        <div className="flex flex-wrap justify-center items-center gap-6">
          <Link href="/login" className="hover:text-[var(--text)] transition-colors">
            Sign In
          </Link>
          <Link href="/styleguide" className="hover:text-[var(--text)] transition-colors">
            Design System
          </Link>
          <a
            href="https://github.com/Kaavin-Khatri/Wareflow"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[var(--text)] transition-colors"
          >
            GitHub Repository
          </a>
          <GlassBadge variant="neutral" className="font-mono text-[10px]">
            v0.4.5-preview
          </GlassBadge>
        </div>
      </div>
    </footer>
  );
}

export default MarketingFooter;
