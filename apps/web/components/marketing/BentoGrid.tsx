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
    <section ref={gridRef} className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <GlassBadge variant="accent" dot>
              Architected for Scale
            </GlassBadge>
            <span className="text-xs text-[var(--text-muted)] font-mono">
              FMCG & Agro Wholesale Standard
            </span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-[var(--text)]">
            Intelligence Layer Built Into Every SKU
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-[var(--text-muted)] max-w-md">
          Replace fragmented spreadsheets with an append-only stock ledger, automated GST tax
          invoicing, and real-time dispatch routing.
        </p>
      </div>

      <div className="grid grid-cols-12 gap-4 lg:gap-6">
        {/* Cell 1: 7-Column Hero Card — Reorder Velocity Engine */}
        <div className="bento-cell col-span-12 lg:col-span-7">
          <GlassCard
            hoverable
            glow
            className="p-6 sm:p-8 h-full flex flex-col justify-between space-y-6"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <GlassBadge variant="warning" dot>
                  Automated PO Trigger
                </GlassBadge>
              </div>
              <GlassCardTitle className="text-xl">
                Predictive Reordering & Low-Stock Alerts
              </GlassCardTitle>
              <GlassCardDescription className="text-xs sm:text-sm leading-relaxed">
                Tracks daily consumption run-rates across Bhiwandi Central and APMC terminals.
                Automatically drafts Purchase Orders when stock dips below safe buffer thresholds.
              </GlassCardDescription>
            </div>

            {/* Visual Micro-Ledger Mockup */}
            <div className="p-4 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] space-y-2.5">
              <div className="flex justify-between items-center text-xs">
                <span className="font-medium text-[var(--text)]">
                  Basmati Extra Long Grain 25kg
                </span>
                <span className="font-mono text-amber-500 font-bold">120 bags remaining</span>
              </div>
              <div className="w-full bg-[var(--border)] h-2 rounded-full overflow-hidden">
                <div className="bg-amber-500 h-full w-[24%]" />
              </div>
              <div className="flex justify-between items-center text-[11px] text-[var(--text-muted)] font-mono">
                <span>Threshold: 200 bags</span>
                <span className="text-[var(--accent)] font-semibold flex items-center gap-1">
                  <Zap className="w-3 h-3" /> Draft PO #894 Generated
                </span>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Cell 2: 5-Column AI Forecasting Card */}
        <div className="bento-cell col-span-12 lg:col-span-5">
          <GlassCard
            hoverable
            glow
            className="p-6 sm:p-8 h-full flex flex-col justify-between space-y-6"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-2xl bg-[var(--accent-subtle)] border border-[var(--accent-border)] flex items-center justify-center text-[var(--accent)]">
                  <Sparkles className="w-5 h-5" />
                </div>
                <GlassBadge variant="accent">LLM Assisted</GlassBadge>
              </div>
              <GlassCardTitle className="text-xl">Seasonal Demand Forecast</GlassCardTitle>
              <GlassCardDescription className="text-xs sm:text-sm leading-relaxed">
                Synthesizes festival buying spikes, monsoon transport delays, and commodity pricing
                trends to recommend optimum procurement lot sizes.
              </GlassCardDescription>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] text-xs flex items-center justify-between">
              <div className="space-y-1">
                <div className="text-[var(--text-muted)]">Diwali Rice Surge Buffer</div>
                <div className="font-bold text-[var(--text)] text-sm">+38.5% Recommended</div>
              </div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
                <TrendingUp className="w-5 h-5" />
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Cell 3: 4-Column WhatsApp Telemetry */}
        <div className="bento-cell col-span-12 sm:col-span-6 lg:col-span-4">
          <GlassCard hoverable className="p-6 h-full flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="w-9 h-9 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <MessageSquare className="w-4 h-4" />
              </div>
              <GlassCardTitle className="text-base">WhatsApp B2B Dispatches</GlassCardTitle>
              <GlassCardDescription className="text-xs">
                Instant delivery of tax invoice PDFs, driver vehicle numbers, and live payment links
                directly to retailer WhatsApp inboxes.
              </GlassCardDescription>
            </div>
            <div className="p-3 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)] text-[11px] text-[var(--text-muted)] font-mono flex items-center justify-between">
              <span>Driver: Raju Yadav (MH-04-AB-1290)</span>
              <span className="text-emerald-400 font-semibold">Sent</span>
            </div>
          </GlassCard>
        </div>

        {/* Cell 4: 4-Column GST & FSSAI Compliance */}
        <div className="bento-cell col-span-12 sm:col-span-6 lg:col-span-4">
          <GlassCard hoverable className="p-6 h-full flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="w-9 h-9 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-[var(--accent)]">
                <FileCheck className="w-4 h-4" />
              </div>
              <GlassCardTitle className="text-base">GST & FSSAI Guardrails</GlassCardTitle>
              <GlassCardDescription className="text-xs">
                Automated HSN code tax classification, IRN e-invoice generation, and supplier
                mandatory FSSAI food-license expiry checks.
              </GlassCardDescription>
            </div>
            <div className="p-3 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)] text-[11px] text-[var(--text-muted)] font-mono flex items-center justify-between">
              <span>NIC IRN Verified #9042</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
          </GlassCard>
        </div>

        {/* Cell 5: 4-Column APMC Lead Radar */}
        <div className="bento-cell col-span-12 sm:col-span-12 lg:col-span-4">
          <GlassCard hoverable className="p-6 h-full flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="w-9 h-9 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <MapPin className="w-4 h-4" />
              </div>
              <GlassCardTitle className="text-base">APMC Wholesale Map</GlassCardTitle>
              <GlassCardDescription className="text-xs">
                Map-based territory visualization across Navi Mumbai, Bhiwandi, and Pune APMC
                wholesalers with credit balance indicators.
              </GlassCardDescription>
            </div>
            <div className="p-3 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)] text-[11px] text-[var(--text-muted)] font-mono flex items-center justify-between">
              <span>32 Active Wholesale Hubs</span>
              <span className="text-cyan-400 flex items-center gap-1">
                Live <ArrowUpRight className="w-3 h-3" />
              </span>
            </div>
          </GlassCard>
        </div>
      </div>
    </section>
  );
}

export default BentoGrid;
