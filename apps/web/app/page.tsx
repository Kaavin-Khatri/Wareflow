"use client";

import React from "react";
import Link from "next/link";
import {
  GlassButton,
  GlassCard,
  GlassCardTitle,
  GlassCardDescription,
  GlassBadge,
} from "@/components/glass";
import { MarketingNav } from "@/components/marketing/MarketingNav";
import { MarketingFooter } from "@/components/marketing/MarketingFooter";
import { HeroScene } from "@/components/marketing/HeroScene";
import { AceternityBeams } from "@/components/marketing/AceternityBeams";
import { BentoGrid } from "@/components/marketing/BentoGrid";
import { ArrowRight, ShieldCheck, Layers, Sparkles, Lock, CheckCircle2 } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col justify-between selection:bg-[var(--accent)] selection:text-white">
      {/* Top Navbar */}
      <MarketingNav />

      {/* Main Content Sections */}
      <main className="flex-1 max-w-6xl mx-auto px-4 sm:px-6 w-full space-y-24 sm:space-y-32 pt-8 sm:pt-16 pb-12">
        {/* ==========================================================================
            HERO SECTION with Aceternity Beams + 3D Canvas
            ========================================================================== */}
        <section className="relative flex flex-col items-center text-center space-y-8 pt-4 sm:pt-8">
          {/* Dynamic Light Beams & Grid */}
          <AceternityBeams />

          {/* Live Telemetry Status Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[var(--surface-hover)] border border-[var(--glass-border)] text-xs text-[var(--text-muted)] backdrop-blur-xl shadow-sm hover:border-[var(--accent-border)] transition-colors">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-medium text-[var(--text)]">WareFlow v0.4.5</span>
            <span className="text-[var(--text-subtle)]">•</span>
            <span>Next-Gen Wholesale Architecture</span>
          </div>

          {/* Main Headline */}
          <div className="space-y-4 max-w-4xl">
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-[var(--text)] leading-[1.08]">
              Autonomous Wholesale{" "}
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-[var(--accent)] via-purple-400 to-[var(--accent-hover)]">
                Inventory & Order
              </span>{" "}
              Intelligence
            </h1>
            <p className="text-base sm:text-xl text-[var(--text-muted)] max-w-2xl mx-auto leading-relaxed">
              Real-time FIFO batch ledger, automated GST tax invoicing, Groq-assisted demand
              forecasting, and instant WhatsApp B2B dispatch routing.
            </p>
          </div>

          {/* Action Call-to-Actions */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 w-full max-w-md pt-2">
            <Link href="/login" className="w-full sm:w-auto">
              <GlassButton
                variant="primary"
                size="lg"
                className="w-full sm:w-auto px-8 py-3.5 text-sm font-bold gap-2 shadow-lg hover:scale-105 transition-all"
              >
                <span>Launch Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </GlassButton>
            </Link>
            <Link href="/styleguide" className="w-full sm:w-auto">
              <GlassButton
                variant="secondary"
                size="lg"
                className="w-full sm:w-auto px-6 py-3.5 text-sm font-semibold gap-2"
              >
                <Sparkles className="w-4 h-4 text-[var(--accent)]" />
                <span>Explore Design System</span>
              </GlassButton>
            </Link>
          </div>

          {/* 3D Scene / Low-Power Fallback */}
          <div className="w-full max-w-4xl pt-6">
            <HeroScene />
          </div>

          {/* Live Telemetry Strip */}
          <div
            id="telemetry"
            className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-4xl pt-4"
          >
            <div className="p-4 rounded-2xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-md text-left">
              <div className="text-xs text-[var(--text-muted)] font-medium">Daily Movement</div>
              <div className="text-xl sm:text-2xl font-black text-[var(--text)] font-mono mt-1">
                14,820 <span className="text-xs font-normal text-[var(--text-muted)]">bags</span>
              </div>
              <div className="text-[10px] text-emerald-400 font-mono mt-0.5">↑ 18.4% velocity</div>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-md text-left">
              <div className="text-xs text-[var(--text-muted)] font-medium">Daily GMV Volume</div>
              <div className="text-xl sm:text-2xl font-black text-[var(--text)] font-mono mt-1">
                ₹8.45M
              </div>
              <div className="text-[10px] text-emerald-400 font-mono mt-0.5">38 POs Cleared</div>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-md text-left">
              <div className="text-xs text-[var(--text-muted)] font-medium">Ledger Settlement</div>
              <div className="text-xl sm:text-2xl font-black text-[var(--text)] font-mono mt-1">
                0.02s
              </div>
              <div className="text-[10px] text-[var(--accent)] font-mono mt-0.5">
                Append-only DB
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-md text-left">
              <div className="text-xs text-[var(--text-muted)] font-medium">API Uptime</div>
              <div className="text-xl sm:text-2xl font-black text-[var(--text)] font-mono mt-1">
                99.98%
              </div>
              <div className="text-[10px] text-emerald-400 font-mono mt-0.5">
                Supabase + FastAPI
              </div>
            </div>
          </div>
        </section>

        {/* ==========================================================================
            BENTO GRID FEATURE SHOWCASE (GSAP ScrollTrigger Powered)
            ========================================================================== */}
        <div id="features">
          <BentoGrid />
        </div>

        {/* ==========================================================================
            ARCHITECTURE & SECURITY SECTION
            ========================================================================== */}
        <section id="architecture" className="space-y-8">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <GlassBadge variant="accent" dot>
              Enterprise Defense
            </GlassBadge>
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-[var(--text)]">
              Sovereign Security & Immutable Audit Logs
            </h2>
            <p className="text-xs sm:text-sm text-[var(--text-muted)]">
              Built on banking-grade cryptographic principles to ensure zero reconciliation drift
              and absolute data accountability.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <GlassCard hoverable className="p-6 space-y-4">
              <div className="w-10 h-10 rounded-2xl bg-[var(--accent-subtle)] border border-[var(--accent-border)] flex items-center justify-center text-[var(--accent)]">
                <Lock className="w-5 h-5" />
              </div>
              <GlassCardTitle className="text-base">RFC 6238 TOTP 2FA</GlassCardTitle>
              <GlassCardDescription className="text-xs leading-relaxed">
                Mandatory hardware-backed 2FA for Owner, Manager, and Accountant roles. TOTP secrets
                and single-use recovery codes encrypted with Fernet AES-128 at rest.
              </GlassCardDescription>
              <div className="pt-2 flex items-center gap-2 text-[11px] text-emerald-400 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Zero Paid SMS Dependency</span>
              </div>
            </GlassCard>

            <GlassCard hoverable className="p-6 space-y-4">
              <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <GlassCardTitle className="text-base">Immutable Audit Trail</GlassCardTitle>
              <GlassCardDescription className="text-xs leading-relaxed">
                Every sensitive change (product price alterations, retailer credit limit
                adjustments, staff role assignments) records complete before/after JSON diffs.
              </GlassCardDescription>
              <div className="pt-2 flex items-center gap-2 text-[11px] text-emerald-400 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Cryptographic Provenance</span>
              </div>
            </GlassCard>

            <GlassCard hoverable className="p-6 space-y-4">
              <div className="w-10 h-10 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <Layers className="w-5 h-5" />
              </div>
              <GlassCardTitle className="text-base">Append-Only Stock Ledger</GlassCardTitle>
              <GlassCardDescription className="text-xs leading-relaxed">
                Stock levels are never mutated in-place. Every inbound GRN, dispatch, return, and
                adjustment is stored as an immutable signed movement event.
              </GlassCardDescription>
              <div className="pt-2 flex items-center gap-2 text-[11px] text-cyan-400 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Zero Balancing Discrepancies</span>
              </div>
            </GlassCard>
          </div>
        </section>

        {/* ==========================================================================
            FINAL CTA BANNER
            ========================================================================== */}
        <section className="relative p-8 sm:p-12 rounded-3xl bg-[var(--surface-elevated)] border border-[var(--accent-border)] backdrop-blur-2xl text-center space-y-6 overflow-hidden shadow-[0_0_50px_-10px_var(--accent-glow)]">
          <div
            aria-hidden="true"
            className="absolute inset-0 opacity-20 pointer-events-none"
            style={{
              background: "radial-gradient(circle at center, var(--accent) 0%, transparent 70%)",
            }}
          />
          <div className="relative z-10 max-w-2xl mx-auto space-y-3">
            <h2 className="text-2xl sm:text-4xl font-black tracking-tight text-[var(--text)]">
              Modernize Your Wholesale Fleet Today
            </h2>
            <p className="text-xs sm:text-sm text-[var(--text-muted)]">
              Instant single-click Google/Apple sign-in with automatic first-user Owner
              bootstrapping.
            </p>
          </div>
          <div className="relative z-10 flex justify-center pt-2">
            <Link href="/login">
              <GlassButton
                variant="primary"
                size="lg"
                className="px-8 py-3.5 text-sm font-bold gap-2 shadow-xl hover:scale-105 transition-all"
              >
                <span>Enter Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </GlassButton>
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <MarketingFooter />
    </div>
  );
}
