"use client";

import React from "react";
import Link from "next/link";
import { GlassButton, GlassBadge } from "@/components/glass";
import ThemeToggle from "@/components/ThemeToggle";
import { ArrowRight } from "lucide-react";

export function MarketingNav() {
  return (
    <header className="sticky top-4 z-50 max-w-6xl mx-auto px-4 sm:px-6">
      <nav className="flex items-center justify-between p-3 sm:px-5 rounded-3xl bg-[var(--glass-bg-elevated)] border border-[var(--glass-border)] backdrop-blur-2xl shadow-[var(--glass-shadow)] transition-all duration-300">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] flex items-center justify-center text-white font-black text-sm shadow-[0_0_16px_-2px_var(--accent-glow)] group-hover:scale-105 transition-transform">
            W
          </div>
          <div className="flex items-center gap-1.5">
            <span className="font-extrabold tracking-tight text-[var(--text)] text-base">
              WareFlow
            </span>
            <GlassBadge variant="accent" className="hidden sm:inline-flex text-[10px] py-0 px-1.5">
              B2B
            </GlassBadge>
          </div>
        </Link>

        {/* Section Navigation Links */}
        <div className="hidden md:flex items-center gap-6 text-xs font-medium text-[var(--text-muted)]">
          <a href="#features" className="hover:text-[var(--text)] transition-colors">
            Platform Capabilities
          </a>
          <a href="#architecture" className="hover:text-[var(--text)] transition-colors">
            Architecture
          </a>
          <a href="#telemetry" className="hover:text-[var(--text)] transition-colors">
            Live Metrics
          </a>
          <Link href="/styleguide" className="hover:text-[var(--text)] transition-colors">
            Design Tokens
          </Link>
        </div>

        {/* Action Controls & Sign-In */}
        <div className="flex items-center gap-2.5">
          <ThemeToggle />
          <Link href="/login">
            <GlassButton variant="primary" size="sm" className="font-semibold gap-1.5">
              <span>Enter Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </GlassButton>
          </Link>
        </div>
      </nav>
    </header>
  );
}

export default MarketingNav;
