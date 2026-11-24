"use client";

import React, { useState } from "react";
import Link from "next/link";
import { GlassButton, GlassBadge } from "@/components/glass";
import ThemeToggle from "@/components/ThemeToggle";
import { ArrowRight, Menu, X, Sparkles, Layers, ShieldCheck, Activity } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { SPRING_PRESETS } from "@/components/motion/MotionProvider";

export function MarketingNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 inset-x-0 z-50 w-full bg-[var(--surface-elevated)]/70 dark:bg-[#09090b]/70 backdrop-blur-2xl backdrop-saturate-150 border-b border-[var(--glass-border)] shadow-[0_4px_30px_rgba(0,0,0,0.1)] transition-all duration-300">
      {/* Top Specular Sheen Highlight */}
      <div
        aria-hidden="true"
        className="absolute inset-x-0 top-0 h-[1px] bg-[var(--glass-highlight)] pointer-events-none"
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] flex items-center justify-center text-white font-black text-sm shadow-[0_0_20px_-2px_var(--accent-glow)] group-hover:scale-105 group-hover:shadow-[0_0_25px_var(--accent)] transition-all duration-300">
            W
          </div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold tracking-tight text-[var(--text)] text-base sm:text-lg">
              WareFlow
            </span>
            <GlassBadge variant="accent" className="text-[10px] py-0 px-1.5 font-mono">
              B2B
            </GlassBadge>
          </div>
        </Link>

        {/* Section Navigation Links (Desktop) */}
        <nav className="hidden md:flex items-center gap-1 bg-[var(--surface)]/40 border border-[var(--glass-border)] p-1 rounded-full backdrop-blur-xl">
          <a
            href="#features"
            className="px-3.5 py-1.5 rounded-full text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-all"
          >
            Capabilities
          </a>
          <a
            href="#architecture"
            className="px-3.5 py-1.5 rounded-full text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-all"
          >
            Architecture
          </a>
          <a
            href="#telemetry"
            className="px-3.5 py-1.5 rounded-full text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-all"
          >
            Live Metrics
          </a>
          <Link
            href="/styleguide"
            className="px-3.5 py-1.5 rounded-full text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-all"
          >
            Design Tokens
          </Link>
        </nav>

        {/* Action Controls & Sign-In */}
        <div className="flex items-center gap-2.5">
          <ThemeToggle />

          <Link href="/login" className="hidden sm:inline-flex">
            <GlassButton
              variant="primary"
              size="sm"
              className="font-semibold gap-1.5 px-4 shadow-[0_0_20px_-3px_var(--accent-glow)] hover:scale-105 transition-all"
            >
              <span>Enter Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </GlassButton>
          </Link>

          {/* Mobile Menu Trigger Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle Navigation Menu"
            className="md:hidden w-9 h-9 rounded-xl flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-[var(--glass-border)] transition-colors"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={SPRING_PRESETS.snappy}
            className="md:hidden border-t border-[var(--glass-border)] bg-[var(--surface-elevated)]/90 backdrop-blur-2xl px-5 py-5 space-y-4 overflow-hidden"
          >
            <div className="flex flex-col space-y-2">
              <a
                href="#features"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
              >
                <Sparkles className="w-4 h-4 text-[var(--accent)]" />
                <span>Capabilities</span>
              </a>
              <a
                href="#architecture"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
              >
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Architecture</span>
              </a>
              <a
                href="#telemetry"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
              >
                <Activity className="w-4 h-4 text-cyan-400" />
                <span>Live Metrics</span>
              </a>
              <Link
                href="/styleguide"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
              >
                <Layers className="w-4 h-4 text-purple-400" />
                <span>Design Tokens</span>
              </Link>
            </div>

            <div className="pt-2 border-t border-[var(--border)]">
              <Link href="/login" onClick={() => setMobileMenuOpen(false)} className="w-full">
                <GlassButton variant="primary" size="md" className="w-full justify-center gap-2">
                  <span>Enter Workspace</span>
                  <ArrowRight className="w-4 h-4" />
                </GlassButton>
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}

export default MarketingNav;
