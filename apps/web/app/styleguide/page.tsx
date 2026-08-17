"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { useTheme } from "@/components/ThemeProvider";

export default function StyleguidePage() {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();
  const [modalOpen, setModalOpen] = useState(false);
  const [inputValue, setInputValue] = useState("Basmati Premium Super Rice 25kg");

  return (
    <AppLayout>
      <div className="space-y-12 max-w-6xl pb-16">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[var(--border)] pb-6">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] font-bold uppercase tracking-wider">
                Phase 4.1 System
              </span>
              <span className="text-xs text-[var(--text-muted)]">• Dev Styleguide</span>
            </div>
            <h1 className="text-3xl font-black tracking-tight text-[var(--text)]">
              Liquid Glass Design System
            </h1>
            <p className="text-sm text-[var(--text-muted)] mt-1">
              Black/White Foundation • Electric Violet Accent • Frosted Glass Overlays & Gradient
              Backdrop
            </p>
          </div>

          {/* Theme Switcher Widget */}
          <div className="flex items-center gap-3 glass-panel p-2 rounded-2xl">
            <button
              onClick={() => setTheme("light")}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                theme === "light"
                  ? "glass-button-primary"
                  : "text-[var(--text-muted)] hover:text-[var(--text)]"
              }`}
            >
              Light
            </button>
            <button
              onClick={() => setTheme("dark")}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                theme === "dark"
                  ? "glass-button-primary"
                  : "text-[var(--text-muted)] hover:text-[var(--text)]"
              }`}
            >
              Dark
            </button>
            <button
              onClick={() => setTheme("system")}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                theme === "system"
                  ? "glass-button-primary"
                  : "text-[var(--text-muted)] hover:text-[var(--text)]"
              }`}
            >
              System ({resolvedTheme})
            </button>
          </div>
        </div>

        {/* Section 1: Dual Theme Comparison Cards */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
              1. True Black / Pure White Foundations
            </h2>
            <span className="text-xs text-[var(--text-muted)] font-mono">Contrast: WCAG AAA</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Simulated Light Mode Card */}
            <div className="rounded-3xl p-6 bg-[#fafafa] text-[#0a0a0a] border border-black/10 shadow-xl space-y-4 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-[#71717a]">
                  Light Mode Archetype
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#7c3aed]/10 text-[#7c3aed] font-semibold border border-[#7c3aed]/20">
                  #7C3AED Accent
                </span>
              </div>
              <div className="space-y-1">
                <h3 className="text-xl font-bold tracking-tight text-[#0a0a0a]">
                  Pure Light Surface
                </h3>
                <p className="text-xs text-[#71717a] leading-relaxed">
                  Crisp near-white surfaces with deep near-black typography and high-contrast violet
                  CTA highlights.
                </p>
              </div>
              <div className="pt-2 flex items-center gap-3">
                <button className="px-4 py-2 rounded-xl bg-[#7c3aed] text-white text-xs font-medium shadow-md shadow-[#7c3aed]/30 hover:bg-[#6d28d9] transition">
                  Primary Action
                </button>
                <div className="px-3 py-2 rounded-xl bg-white border border-black/10 text-xs font-medium text-[#0a0a0a]">
                  Surface Layer
                </div>
              </div>
            </div>

            {/* Simulated Dark Mode Card */}
            <div className="rounded-3xl p-6 bg-[#09090b] text-[#f5f5f7] border border-white/10 shadow-2xl space-y-4 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-[#a1a1aa]">
                  Dark Mode Archetype
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#8b5cf6]/15 text-[#8b5cf6] font-semibold border border-[#8b5cf6]/30">
                  #8B5CF6 Accent
                </span>
              </div>
              <div className="space-y-1">
                <h3 className="text-xl font-bold tracking-tight text-[#f5f5f7]">
                  True Dark Surface
                </h3>
                <p className="text-xs text-[#a1a1aa] leading-relaxed">
                  Deep space near-black surfaces with luminous off-white typography and glowing
                  violet CTA highlights.
                </p>
              </div>
              <div className="pt-2 flex items-center gap-3">
                <button className="px-4 py-2 rounded-xl bg-[#8b5cf6] text-white text-xs font-medium shadow-lg shadow-[#8b5cf6]/40 hover:bg-[#9f75ff] transition">
                  Primary Action
                </button>
                <div className="px-3 py-2 rounded-xl bg-[#141418] border border-white/10 text-xs font-medium text-[#f5f5f7]">
                  Surface Layer
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 2: Accent Color Token Matrix */}
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
            2. Single Accent Color: Electric Violet Purple
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="glass-panel p-4 rounded-2xl space-y-2">
              <div className="h-12 rounded-xl bg-[var(--accent)] shadow-md flex items-center justify-center text-white font-mono text-xs font-bold" />
              <div>
                <span className="text-xs font-semibold block text-[var(--text)]">--accent</span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">
                  Primary Brand
                </span>
              </div>
            </div>

            <div className="glass-panel p-4 rounded-2xl space-y-2">
              <div className="h-12 rounded-xl bg-[var(--accent-hover)] shadow-md flex items-center justify-center text-white font-mono text-xs font-bold" />
              <div>
                <span className="text-xs font-semibold block text-[var(--text)]">
                  --accent-hover
                </span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">Hover State</span>
              </div>
            </div>

            <div className="glass-panel p-4 rounded-2xl space-y-2">
              <div className="h-12 rounded-xl bg-[var(--accent-subtle)] border border-[var(--accent-border)] flex items-center justify-center text-[var(--accent)] font-mono text-xs font-bold" />
              <div>
                <span className="text-xs font-semibold block text-[var(--text)]">
                  --accent-subtle
                </span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">
                  Tint / Badges
                </span>
              </div>
            </div>

            <div className="glass-panel p-4 rounded-2xl space-y-2">
              <div className="h-12 rounded-xl bg-[var(--surface)] border-2 border-[var(--accent-border)] flex items-center justify-center text-[var(--accent)] font-mono text-xs font-bold" />
              <div>
                <span className="text-xs font-semibold block text-[var(--text)]">
                  --accent-border
                </span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">
                  Focus / Outline
                </span>
              </div>
            </div>

            <div className="glass-panel p-4 rounded-2xl space-y-2">
              <div className="h-12 rounded-xl bg-[var(--accent)] glow-purple flex items-center justify-center text-white font-mono text-xs font-bold" />
              <div>
                <span className="text-xs font-semibold block text-[var(--text)]">
                  --accent-glow
                </span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">Bloom Layer</span>
              </div>
            </div>

            <div className="glass-panel p-4 rounded-2xl space-y-2">
              <div className="h-12 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)] flex items-center justify-center text-[var(--text)] font-mono text-xs font-bold">
                Aa
              </div>
              <div>
                <span className="text-xs font-semibold block text-[var(--text)]">
                  --surface-hover
                </span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">Interactive</span>
              </div>
            </div>
          </div>
        </section>

        {/* Section 3: Liquid Glass Panels & Specular Edges */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
              3. Liquid Glass Surfaces & Specular Sheen
            </h2>
            <span className="text-xs text-[var(--text-muted)]">Backdrop Filter 16-24px Blur</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Standard Glass Panel */}
            <div className="glass-panel p-6 rounded-3xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[var(--accent)]">.glass-panel</span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">
                  Standard Card
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Translucent frosted glass with a 1px top specular highlight edge and soft drop blur
                over drifting background blooms.
              </p>
              <div className="pt-2">
                <button className="glass-button-secondary px-3 py-1.5 rounded-xl text-xs font-medium cursor-pointer">
                  Secondary Action
                </button>
              </div>
            </div>

            {/* Elevated Glass Panel */}
            <div className="glass-panel-elevated p-6 rounded-3xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[var(--accent)]">
                  .glass-panel-elevated
                </span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">
                  Modals / Popovers
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Higher opacity with 24px backdrop blur, elevated specular sheen, and deeper drop
                shadow for hierarchy.
              </p>
              <div className="pt-2">
                <button
                  onClick={() => setModalOpen(true)}
                  className="glass-button-primary px-3 py-1.5 rounded-xl text-xs font-medium cursor-pointer"
                >
                  Trigger Modal Demo
                </button>
              </div>
            </div>

            {/* Glowing Accent Glass Panel */}
            <div className="glass-panel p-6 rounded-3xl space-y-3 glow-purple border-[var(--accent-border)]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[var(--accent)]">.glow-purple</span>
                <span className="text-[10px] text-[var(--accent)] font-mono font-semibold">
                  Active Highlight
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Subtle violet luminescence applied to critical stats, live alerts, and active
                workflows.
              </p>
              <div className="pt-2 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-ping" />
                <span className="text-xs font-medium text-[var(--accent)]">
                  Live Real-time State
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Section 4: Interactive Components Showcase */}
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
            4. Interactive UI Components
          </h2>

          <div className="glass-panel p-8 rounded-3xl space-y-8">
            {/* Buttons Row */}
            <div className="space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-subtle)]">
                Button States
              </span>
              <div className="flex flex-wrap items-center gap-4">
                <button className="glass-button-primary px-5 py-2.5 rounded-2xl text-xs font-semibold cursor-pointer">
                  Primary Glass Button
                </button>
                <button className="glass-button-secondary px-5 py-2.5 rounded-2xl text-xs font-semibold cursor-pointer">
                  Secondary Glass Button
                </button>
                <button
                  disabled
                  className="glass-button-secondary px-5 py-2.5 rounded-2xl text-xs font-semibold opacity-40 cursor-not-allowed"
                >
                  Disabled Button
                </button>
                <button
                  onClick={toggleTheme}
                  className="glass-button-secondary p-2.5 rounded-2xl text-xs font-medium cursor-pointer"
                  title="Toggle Theme"
                >
                  Toggle Theme ({resolvedTheme})
                </button>
              </div>
            </div>

            {/* Inputs Row */}
            <div className="space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-subtle)]">
                Form Inputs & Search
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[var(--text-muted)]">
                    Product SKU Name
                  </label>
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    className="glass-input w-full px-4 py-2.5 rounded-xl text-xs text-[var(--text)]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[var(--text-muted)]">
                    Wholesale Filter
                  </label>
                  <select className="glass-input w-full px-4 py-2.5 rounded-xl text-xs text-[var(--text)] cursor-pointer">
                    <option className="bg-[var(--bg)] text-[var(--text)]">
                      All Warehouses (Active)
                    </option>
                    <option className="bg-[var(--bg)] text-[var(--text)]">
                      North Delhi Central Hub
                    </option>
                    <option className="bg-[var(--bg)] text-[var(--text)]">
                      Bhiwandi West Logistics
                    </option>
                  </select>
                </div>
              </div>
            </div>

            {/* Badges & Status Chips */}
            <div className="space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-subtle)]">
                Status Chips & Badges
              </span>
              <div className="flex flex-wrap items-center gap-3">
                <span className="px-3 py-1 rounded-lg text-xs font-medium bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]">
                  Electric Violet Active
                </span>
                <span className="px-3 py-1 rounded-lg text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Stock Verified
                </span>
                <span className="px-3 py-1 rounded-lg text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Reorder Pending
                </span>
                <span className="px-3 py-1 rounded-lg text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  Critical Low Stock
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Modal Demo */}
        {modalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
            <div className="w-full max-w-lg rounded-3xl glass-panel-elevated p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
                <div className="space-y-0.5">
                  <h3 className="text-base font-bold text-[var(--text)]">Liquid Glass Modal</h3>
                  <p className="text-xs text-[var(--text-muted)]">
                    Elevated frosted surface with specular top sheen.
                  </p>
                </div>
                <button
                  onClick={() => setModalOpen(false)}
                  className="text-[var(--text-muted)] hover:text-[var(--text)] text-sm cursor-pointer"
                >
                  ✕
                </button>
              </div>

              <div className="p-4 rounded-2xl glass-panel text-xs text-[var(--text-muted)] leading-relaxed space-y-2">
                <p>
                  This modal demonstrates high-opacity frosted glass floating directly above the
                  slowly animated gradient backdrop.
                </p>
                <div className="font-mono text-[11px] text-[var(--accent)]">
                  --glass-bg-elevated:{" "}
                  {resolvedTheme === "dark"
                    ? "rgba(24, 24, 32, 0.82)"
                    : "rgba(255, 255, 255, 0.88)"}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setModalOpen(false)}
                  className="glass-button-secondary px-4 py-2 rounded-xl text-xs font-medium cursor-pointer"
                >
                  Dismiss
                </button>
                <button
                  onClick={() => setModalOpen(false)}
                  className="glass-button-primary px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Confirm Action
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
