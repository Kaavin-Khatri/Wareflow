"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { GlassCard, GlassCardTitle, GlassCardDescription, GlassBadge } from "@/components/glass";
import {
  TrendingUp,
  AlertTriangle,
  MessageSquare,
  FileCheck,
  MapPin,
  Sparkles,
  ArrowUpRight,
  ShieldCheck,
  Zap,
} from "lucide-react";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

export function BentoGrid() {
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!gridRef.current) return;

    // Respect user's motion preferences
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.from(".bento-cell", {
        scrollTrigger: {
          trigger: gridRef.current,
          start: "top 82%",
          once: true, // Only trigger ONCE to eliminate scroll-up/down jank
        },
        opacity: 0,
        y: 35,
        duration: 0.7,
        stagger: 0.12,
        ease: "power3.out",
        clearProps: "transform,opacity",
      });
    }, gridRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={gridRef} className="space-y-8">
      {/* Section Header with generous breathing room and refined alignment */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-[var(--glass-border)]/40">
        <div className="space-y-3 max-w-xl text-left">
          <div className="flex flex-wrap items-center gap-2">
            <GlassBadge variant="accent" dot>
              Architected for Scale
            </GlassBadge>
            <span className="text-xs text-[var(--text-muted)] font-mono">
              FMCG & Agro Wholesale Standard
            </span>
          </div>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight text-[var(--text)] leading-tight">
            Intelligence Layer Built Into Every SKU
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-[var(--text-muted)] max-w-md text-left md:text-right leading-relaxed">
          Replace fragmented spreadsheets with an append-only stock ledger, automated GST tax
          invoicing, and real-time dispatch routing.
        </p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Cell 1: 7-Column Hero Card — Reorder Velocity Engine */}
        <div className="bento-cell col-span-12 lg:col-span-7 flex">
          <GlassCard
            hoverable
            glow
            className="p-7 sm:p-9 w-full flex flex-col justify-between"
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="w-11 h-11 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 shadow-sm">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <GlassBadge variant="warning" dot>
                  Automated PO Trigger
                </GlassBadge>
              </div>
              <div className="space-y-2.5">
                <GlassCardTitle className="text-xl sm:text-2xl font-bold">
                  Predictive Reordering & Low-Stock Alerts
                </GlassCardTitle>
                <GlassCardDescription className="text-xs sm:text-sm leading-relaxed text-[var(--text-muted)]">
                  Tracks daily consumption run-rates across Bhiwandi Central and APMC terminals.
                  Automatically drafts Purchase Orders when stock dips below safe buffer thresholds.
                </GlassCardDescription>
              </div>
            </div>

            {/* Visual Micro-Ledger Mockup with ample margin-top separation */}
            <div className="mt-8 p-5 rounded-2xl bg-[var(--surface-elevated)]/50 border border-[var(--glass-border)] space-y-3.5 shadow-inner">
              <div className="flex justify-between items-center text-xs sm:text-sm gap-2">
                <span className="font-semibold text-[var(--text)] truncate">
                  Basmati Extra Long Grain 25kg
                </span>
                <span className="font-mono text-amber-500 font-bold shrink-0">120 bags remaining</span>
              </div>
              <div className="w-full bg-[var(--border)] h-2 rounded-full overflow-hidden">
                <div className="bg-gradient-to-r from-amber-500 to-orange-500 h-full w-[24%] rounded-full" />
              </div>
              <div className="flex justify-between items-center text-xs text-[var(--text-muted)] font-mono pt-0.5">
                <span>Threshold: 200 bags</span>
                <span className="text-[var(--accent)] font-semibold flex items-center gap-1">
                  <Zap className="w-3.5 h-3.5" /> Draft PO #894 Generated
                </span>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Cell 2: 5-Column AI Forecasting Card */}
        <div className="bento-cell col-span-12 lg:col-span-5 flex">
          <GlassCard
            hoverable
            glow
            className="p-7 sm:p-9 w-full flex flex-col justify-between"
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="w-11 h-11 rounded-2xl bg-[var(--accent-subtle)] border border-[var(--accent-border)] flex items-center justify-center text-[var(--accent)] shadow-sm">
                  <Sparkles className="w-5 h-5" />
                </div>
                <GlassBadge variant="accent">LLM Assisted</GlassBadge>
              </div>
              <div className="space-y-2.5">
                <GlassCardTitle className="text-xl sm:text-2xl font-bold">
                  Seasonal Demand Forecast
                </GlassCardTitle>
                <GlassCardDescription className="text-xs sm:text-sm leading-relaxed text-[var(--text-muted)]">
                  Synthesizes festival buying spikes, monsoon transport delays, and commodity pricing
                  trends to recommend optimum procurement lot sizes.
                </GlassCardDescription>
              </div>
            </div>

            {/* Metric Chip with ample margin-top separation */}
            <div className="mt-8 p-5 rounded-2xl bg-[var(--surface-elevated)]/50 border border-[var(--glass-border)] text-xs sm:text-sm flex items-center justify-between gap-4 shadow-inner">
              <div className="space-y-1">
                <div className="text-xs text-[var(--text-muted)]">Diwali Rice Surge Buffer</div>
                <div className="font-bold text-[var(--text)] text-base">+38.5% Recommended</div>
              </div>
              <div className="w-11 h-11 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold shrink-0">
                <TrendingUp className="w-5 h-5" />
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Cell 3: 4-Column WhatsApp Telemetry */}
        <div className="bento-cell col-span-12 sm:col-span-6 lg:col-span-4 flex">
          <GlassCard hoverable className="p-6 sm:p-8 w-full flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div className="space-y-2">
                <GlassCardTitle className="text-base sm:text-lg font-bold">
                  WhatsApp B2B Dispatches
                </GlassCardTitle>
                <GlassCardDescription className="text-xs leading-relaxed text-[var(--text-muted)]">
                  Instant delivery of tax invoice PDFs, driver vehicle numbers, and live payment links
                  directly to retailer WhatsApp inboxes.
                </GlassCardDescription>
              </div>
            </div>
            <div className="mt-6 p-3.5 rounded-xl bg-[var(--surface-elevated)]/50 border border-[var(--border)] text-xs text-[var(--text-muted)] font-mono flex items-center justify-between gap-2">
              <span className="truncate">Driver: Raju Yadav (MH-04)</span>
              <span className="text-emerald-400 font-semibold shrink-0">Sent</span>
            </div>
          </GlassCard>
        </div>

        {/* Cell 4: 4-Column GST & FSSAI Compliance */}
        <div className="bento-cell col-span-12 sm:col-span-6 lg:col-span-4 flex">
          <GlassCard hoverable className="p-6 sm:p-8 w-full flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-10 h-10 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-[var(--accent)]">
                <FileCheck className="w-5 h-5" />
              </div>
              <div className="space-y-2">
                <GlassCardTitle className="text-base sm:text-lg font-bold">
                  GST & FSSAI Guardrails
                </GlassCardTitle>
                <GlassCardDescription className="text-xs leading-relaxed text-[var(--text-muted)]">
                  Automated HSN code tax classification, IRN e-invoice generation, and supplier
                  mandatory FSSAI food-license expiry checks.
                </GlassCardDescription>
              </div>
            </div>
            <div className="mt-6 p-3.5 rounded-xl bg-[var(--surface-elevated)]/50 border border-[var(--border)] text-xs text-[var(--text-muted)] font-mono flex items-center justify-between gap-2">
              <span className="truncate">NIC IRN Verified #9042</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            </div>
          </GlassCard>
        </div>

        {/* Cell 5: 4-Column APMC Lead Radar */}
        <div className="bento-cell col-span-12 sm:col-span-12 lg:col-span-4 flex">
          <GlassCard hoverable className="p-6 sm:p-8 w-full flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-10 h-10 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <MapPin className="w-5 h-5" />
              </div>
              <div className="space-y-2">
                <GlassCardTitle className="text-base sm:text-lg font-bold">
                  APMC Wholesale Map
                </GlassCardTitle>
                <GlassCardDescription className="text-xs leading-relaxed text-[var(--text-muted)]">
                  Map-based territory visualization across Navi Mumbai, Bhiwandi, and Pune APMC
                  wholesalers with credit balance indicators.
                </GlassCardDescription>
              </div>
            </div>
            <div className="mt-6 p-3.5 rounded-xl bg-[var(--surface-elevated)]/50 border border-[var(--border)] text-xs text-[var(--text-muted)] font-mono flex items-center justify-between gap-2">
              <span>32 Active Wholesale Hubs</span>
              <span className="text-cyan-400 flex items-center gap-1 shrink-0 font-semibold">
                Live <ArrowUpRight className="w-3.5 h-3.5" />
              </span>
            </div>
          </GlassCard>
        </div>
      </div>
    </section>
  );
}

export default BentoGrid;
