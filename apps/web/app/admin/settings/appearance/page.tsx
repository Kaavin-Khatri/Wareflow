"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { useTheme } from "@/components/ThemeProvider";
import {
  GlassButton,
  GlassCard,
  GlassCardTitle,
  GlassCardDescription,
  GlassInput,
  GlassBadge,
} from "@/components/glass";

import { FadeIn } from "@/components/motion/GlassMotion";
import { AccentId } from "@/lib/theme-accents";
import {
  Sun,
  Moon,
  Laptop,
  Check,
  Sparkles,
  ShieldCheck,
  Plus,
  RefreshCw,
  ShoppingBag,
} from "lucide-react";

export default function AppearanceSettingsPage() {
  const { theme, resolvedTheme, accent, currentSwatch, availableAccents, setTheme, setAccent } =
    useTheme();

  const [isSaved, setIsSaved] = useState(false);

  const handleSave = () => {
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2500);
  };

  return (
    <AppLayout>
      <FadeIn className="max-w-5xl space-y-8 pb-16">
        {/* Header */}
        <div className="border-b border-[var(--border)] pb-5">
          <div className="flex items-center gap-2 mb-1.5">
            <GlassBadge variant="accent" dot>
              System Customization
            </GlassBadge>
            <span className="text-xs text-[var(--text-muted)] font-mono">WCAG AA Calibrated</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">
            Appearance & Theme Settings
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Personalize your workspace mode and primary accent. Your preference persists across
            devices.
          </p>
        </div>

        {/* Section 1: Color Mode Preference (Light / Dark / System) */}
        <section className="space-y-4">
          <div>
            <h2 className="text-base font-bold text-[var(--text)] tracking-tight">
              Interface Color Mode
            </h2>
            <p className="text-xs text-[var(--text-muted)]">
              Choose your visual base. The true black/white liquid glass foundation remains locked
              for optimal contrast.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Light Mode Card */}
            <div
              onClick={() => setTheme("light")}
              className={`p-5 rounded-2xl cursor-pointer transition-all duration-200 border text-left relative overflow-hidden ${
                theme === "light"
                  ? "bg-[var(--glass-bg)] border-[var(--accent)] shadow-[0_0_20px_-6px_var(--accent-glow)] ring-2 ring-[var(--accent)]"
                  : "bg-[var(--glass-bg)] border-[var(--glass-border)] hover:border-[var(--border-strong)] opacity-80 hover:opacity-100"
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center">
                  <Sun className="w-5 h-5" />
                </div>
                {theme === "light" && (
                  <span className="w-5 h-5 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-xs">
                    <Check className="w-3 h-3" />
                  </span>
                )}
              </div>
              <h3 className="text-sm font-bold text-[var(--text)]">Light Mode</h3>
              <p className="text-[11px] text-[var(--text-muted)] mt-1">
                Pure #FFFFFF / #FAFAFA paper surface with high-contrast obsidian typography.
              </p>
            </div>

            {/* Dark Mode Card */}
            <div
              onClick={() => setTheme("dark")}
              className={`p-5 rounded-2xl cursor-pointer transition-all duration-200 border text-left relative overflow-hidden ${
                theme === "dark"
                  ? "bg-[var(--glass-bg)] border-[var(--accent)] shadow-[0_0_20px_-6px_var(--accent-glow)] ring-2 ring-[var(--accent)]"
                  : "bg-[var(--glass-bg)] border-[var(--glass-border)] hover:border-[var(--border-strong)] opacity-80 hover:opacity-100"
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-9 h-9 rounded-xl bg-violet-500/10 text-violet-400 flex items-center justify-center">
                  <Moon className="w-5 h-5" />
                </div>
                {theme === "dark" && (
                  <span className="w-5 h-5 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-xs">
                    <Check className="w-3 h-3" />
                  </span>
                )}
              </div>
              <h3 className="text-sm font-bold text-[var(--text)]">Dark Mode</h3>
              <p className="text-[11px] text-[var(--text-muted)] mt-1">
                True #09090B deep OLED background with frosted translucent specular glass.
              </p>
            </div>

            {/* System Mode Card */}
            <div
              onClick={() => setTheme("system")}
              className={`p-5 rounded-2xl cursor-pointer transition-all duration-200 border text-left relative overflow-hidden ${
                theme === "system"
                  ? "bg-[var(--glass-bg)] border-[var(--accent)] shadow-[0_0_20px_-6px_var(--accent-glow)] ring-2 ring-[var(--accent)]"
                  : "bg-[var(--glass-bg)] border-[var(--glass-border)] hover:border-[var(--border-strong)] opacity-80 hover:opacity-100"
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-9 h-9 rounded-xl bg-[var(--surface-hover)] text-[var(--text-muted)] flex items-center justify-center">
                  <Laptop className="w-5 h-5" />
                </div>
                {theme === "system" && (
                  <span className="w-5 h-5 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-xs">
                    <Check className="w-3 h-3" />
                  </span>
                )}
              </div>
              <h3 className="text-sm font-bold text-[var(--text)]">System Match</h3>
              <p className="text-[11px] text-[var(--text-muted)] mt-1">
                Follows your operating system preference automatically ({resolvedTheme} active).
              </p>
            </div>
          </div>
        </section>

        {/* Section 2: Accent Color Picker (Curated Pre-Tested Swatches) */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-[var(--text)] tracking-tight">
                Accent Color Swatch
              </h2>
              <p className="text-xs text-[var(--text-muted)]">
                Selected from 7 pre-tested swatches. Every swatch passes WCAG AA contrast against
                both dark and light modes.
              </p>
            </div>
            <GlassBadge variant="accent" dot>
              Active: {currentSwatch.name}
            </GlassBadge>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {availableAccents.map((swatch) => {
              const isSelected = accent === swatch.id;
              return (
                <div
                  key={swatch.id}
                  onClick={() => setAccent(swatch.id as AccentId)}
                  className={`p-4 rounded-2xl cursor-pointer transition-all duration-200 border text-left relative overflow-hidden ${
                    isSelected
                      ? "bg-[var(--glass-bg)] border-[var(--accent)] shadow-lg ring-2 ring-[var(--accent)]"
                      : "bg-[var(--glass-bg)] border-[var(--glass-border)] hover:border-[var(--border-strong)] opacity-85 hover:opacity-100"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2.5">
                      <span
                        className="w-5 h-5 rounded-full shrink-0 shadow-sm"
                        style={{ backgroundColor: swatch.sampleHex }}
                      />
                      <span className="text-xs font-bold text-[var(--text)]">{swatch.name}</span>
                    </div>
                    {isSelected && (
                      <span className="w-4 h-4 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-[10px]">
                        <Check className="w-2.5 h-2.5" />
                      </span>
                    )}
                  </div>

                  <p className="text-[11px] text-[var(--text-muted)] leading-snug line-clamp-2">
                    {swatch.description}
                  </p>

                  <div className="mt-3 pt-2.5 border-t border-[var(--border)] flex items-center justify-between text-[10px] text-[var(--text-subtle)] font-mono">
                    <span className="flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      {swatch.wcagDarkContrast}
                    </span>
                    <span>{swatch.sampleHex}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Section 3: Live Component Preview */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-[var(--text)] tracking-tight">
                Live Interface Preview
              </h2>
              <p className="text-xs text-[var(--text-muted)]">
                See your selected theme and accent token applied live across real glass components.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <GlassButton
                variant="outline"
                size="sm"
                onClick={() => {
                  setTheme("dark");
                  setAccent("violet");
                }}
              >
                <RefreshCw className="w-3 h-3" />
                Reset Defaults
              </GlassButton>
              <GlassButton variant="primary" size="sm" onClick={handleSave}>
                <Sparkles className="w-3 h-3" />
                {isSaved ? "Saved to Profile!" : "Save Preferences"}
              </GlassButton>
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] space-y-6">
            {/* Live Component Preview Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Card 1: Interactive Buttons & Form */}
              <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                  Interactive Controls & Focus Glow
                </h3>
                <div className="flex flex-wrap gap-3">
                  <GlassButton variant="primary" size="md">
                    <Plus className="w-3.5 h-3.5" />
                    Primary Action
                  </GlassButton>
                  <GlassButton variant="secondary" size="md">
                    Secondary CTA
                  </GlassButton>
                  <GlassButton variant="outline" size="md">
                    Outline Glass
                  </GlassButton>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[11px] font-semibold text-[var(--text-muted)]">
                    Focus Glow Ring Demo
                  </label>
                  <GlassInput
                    defaultValue="Basmati Super Export Grade 25kg"
                    placeholder="Search wholesale catalog..."
                  />
                </div>
              </div>

              {/* Card 2: Luminous Card Container */}
              <GlassCard hoverable glow className="p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <GlassBadge variant="accent" dot>
                    Live Stock Alert
                  </GlassBadge>
                  <ShoppingBag className="w-4 h-4 text-[var(--accent)]" />
                </div>
                <GlassCardTitle className="text-sm">Wholesale Order Fulfillment</GlassCardTitle>
                <GlassCardDescription className="text-xs">
                  Real-time stock dispatch queue synced across Bhiwandi Central Hub and Vashi APMC
                  Terminal.
                </GlassCardDescription>
                <div className="flex items-center justify-between pt-2 border-t border-[var(--border)] text-xs">
                  <span className="text-[var(--text-muted)]">Allocated Credit:</span>
                  <span className="font-mono font-bold text-[var(--accent)]">₹1,50,000</span>
                </div>
              </GlassCard>
            </div>
          </div>
        </section>
      </FadeIn>
    </AppLayout>
  );
}
