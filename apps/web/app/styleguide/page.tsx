"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { useTheme } from "@/components/ThemeProvider";
import {
  GlassButton,
  GlassCard,
  GlassCardHeader,
  GlassCardTitle,
  GlassCardDescription,
  GlassCardContent,
  GlassCardFooter,
  GlassModal,
  GlassDropdown,
  GlassInput,
  GlassBadge,
} from "@/components/glass";
import { FadeIn } from "@/components/motion/GlassMotion";
import {
  Search,
  SlidersHorizontal,
  MoreVertical,
  CheckCircle,
  Flame,
  FileSpreadsheet,
  Plus,
  Trash2,
  Edit3,
  ExternalLink,
} from "lucide-react";

export default function StyleguidePage() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [modalOpen, setModalOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("Basmati Premium Export 25kg");
  const [denseItems, setDenseItems] = useState(
    Array.from({ length: 24 }, (_, i) => ({
      id: `item-${i + 1}`,
      name: `Wholesale Item SKU-00${i + 1}`,
      stock: (i + 1) * 35,
      price: (i + 1) * 1200,
      status: i % 4 === 0 ? "critical" : i % 3 === 0 ? "warning" : "verified",
    })),
  );

  return (
    <AppLayout>
      <FadeIn className="space-y-12 max-w-6xl pb-20">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[var(--border)] pb-6">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <GlassBadge variant="accent" dot>
                Phase 4.2 Primitives
              </GlassBadge>
              <span className="text-xs text-[var(--text-muted)] font-mono">
                Real Specular Refraction + Motion Stack
              </span>
            </div>
            <h1 className="text-3xl font-black tracking-tight text-[var(--text)]">
              Glass Component System
            </h1>
            <p className="text-sm text-[var(--text-muted)] mt-1">
              Refractive Edge Lensing • Motion Spring Choreography • 60 FPS Dense Surface Budget
            </p>
          </div>

          {/* Theme Switcher Widget */}
          <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-md">
            <GlassButton
              variant={theme === "light" ? "primary" : "ghost"}
              size="sm"
              onClick={() => setTheme("light")}
            >
              Light
            </GlassButton>
            <GlassButton
              variant={theme === "dark" ? "primary" : "ghost"}
              size="sm"
              onClick={() => setTheme("dark")}
            >
              Dark
            </GlassButton>
            <GlassButton
              variant={theme === "system" ? "primary" : "ghost"}
              size="sm"
              onClick={() => setTheme("system")}
            >
              System ({resolvedTheme})
            </GlassButton>
          </div>
        </div>

        {/* Section 1: GlassButton Suite (Flagship Primitive) */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
              1. GlassButton — Real Specular Refraction & Tactile Compression
            </h2>
            <span className="text-xs text-[var(--text-muted)] font-mono">
              Hover for specular sheen • Press for tactile spring
            </span>
          </div>

          <div className="p-6 rounded-3xl bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Primary */}
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-[var(--text-muted)] block">
                  Primary (Electric Violet)
                </span>
                <GlassButton variant="primary" size="md" className="w-full">
                  <Plus className="w-3.5 h-3.5" />
                  Primary Action
                </GlassButton>
              </div>

              {/* Secondary */}
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-[var(--text-muted)] block">
                  Secondary (Frosted)
                </span>
                <GlassButton variant="secondary" size="md" className="w-full">
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                  Secondary CTA
                </GlassButton>
              </div>

              {/* Outline */}
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-[var(--text-muted)] block">
                  Outline Glass
                </span>
                <GlassButton variant="outline" size="md" className="w-full">
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                  Filter Options
                </GlassButton>
              </div>

              {/* Destructive */}
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-[var(--text-muted)] block">
                  Destructive Frosted
                </span>
                <GlassButton variant="destructive" size="md" className="w-full">
                  <Trash2 className="w-3.5 h-3.5" />
                  Delete Item
                </GlassButton>
              </div>

              {/* Ghost / Icon */}
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-[var(--text-muted)] block">
                  Ghost / Icon Buttons
                </span>
                <div className="flex items-center gap-2">
                  <GlassButton variant="ghost" size="icon">
                    <Edit3 className="w-4 h-4" />
                  </GlassButton>
                  <GlassButton variant="secondary" size="icon">
                    <ExternalLink className="w-4 h-4" />
                  </GlassButton>
                  <GlassDropdown
                    trigger={
                      <GlassButton variant="secondary" size="icon">
                        <MoreVertical className="w-4 h-4" />
                      </GlassButton>
                    }
                    items={[
                      { id: "1", label: "View Details", onClick: () => {} },
                      { id: "2", label: "Edit Pricing", onClick: () => {} },
                      { id: "3", label: "Archive SKU", destructive: true, onClick: () => {} },
                    ]}
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 2: GlassCard & GlassPanel Primitives */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
              2. GlassCard & GlassPanel — Light-Edge Specular Contours
            </h2>
            <span className="text-xs text-[var(--text-muted)]">
              Thinner refraction perimeter tuned for large surface fill rates
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <GlassCard hoverable>
              <GlassCardHeader>
                <div className="flex items-center justify-between">
                  <GlassBadge variant="accent">Standard Card</GlassBadge>
                  <span className="text-xs font-mono text-[var(--text-muted)]">#001</span>
                </div>
                <GlassCardTitle className="mt-2">Inventory Batch FIFO</GlassCardTitle>
                <GlassCardDescription>
                  Tracks aging lots and automatically directs pickers to earliest expiry date.
                </GlassCardDescription>
              </GlassCardHeader>
              <GlassCardContent>
                <div className="p-3 rounded-2xl bg-[var(--surface-hover)] border border-[var(--border)] text-xs text-[var(--text)] flex justify-between items-center">
                  <span>Available Stock</span>
                  <span className="font-mono font-bold text-[var(--accent)]">1,420 units</span>
                </div>
              </GlassCardContent>
              <GlassCardFooter className="justify-between">
                <span className="text-[11px] text-[var(--text-muted)]">Updated 2m ago</span>
                <GlassButton variant="secondary" size="sm">
                  Inspect
                </GlassButton>
              </GlassCardFooter>
            </GlassCard>

            <GlassCard hoverable glow>
              <GlassCardHeader>
                <div className="flex items-center justify-between">
                  <GlassBadge variant="accent" dot>
                    Active Lensing
                  </GlassBadge>
                  <Flame className="w-4 h-4 text-[var(--accent)]" />
                </div>
                <GlassCardTitle className="mt-2">Glow Highlight Card</GlassCardTitle>
                <GlassCardDescription>
                  Luminous Electric Violet bloom perimeter for high-priority alerts and live
                  actions.
                </GlassCardDescription>
              </GlassCardHeader>
              <GlassCardContent>
                <div className="p-3 rounded-2xl bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-xs text-[var(--accent)] flex justify-between items-center font-medium">
                  <span>Credit Utilization</span>
                  <span className="font-mono font-bold">₹75,000 / ₹1,00,000</span>
                </div>
              </GlassCardContent>
              <GlassCardFooter className="justify-between">
                <span className="text-[11px] text-[var(--accent)]">Critical Threshold</span>
                <GlassButton variant="primary" size="sm" onClick={() => setModalOpen(true)}>
                  Adjust Limit
                </GlassButton>
              </GlassCardFooter>
            </GlassCard>

            <GlassCard hoverable>
              <GlassCardHeader>
                <div className="flex items-center justify-between">
                  <GlassBadge variant="success" dot>
                    GST Compliant
                  </GlassBadge>
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                </div>
                <GlassCardTitle className="mt-2">Tax Invoicing Engine</GlassCardTitle>
                <GlassCardDescription>
                  Real-time E-Invoicing IRN generation with automated QR payload freezing.
                </GlassCardDescription>
              </GlassCardHeader>
              <GlassCardContent>
                <div className="p-3 rounded-2xl bg-[var(--surface-hover)] border border-[var(--border)] text-xs text-[var(--text)] flex justify-between items-center">
                  <span>Current Month Total</span>
                  <span className="font-mono font-bold text-emerald-400">₹14,20,500</span>
                </div>
              </GlassCardContent>
              <GlassCardFooter className="justify-between">
                <span className="text-[11px] text-[var(--text-muted)]">34 Invoices Generated</span>
                <GlassButton variant="secondary" size="sm">
                  View Ledger
                </GlassButton>
              </GlassCardFooter>
            </GlassCard>
          </div>
        </section>

        {/* Section 3: Dense Surface Performance Test (20+ Interactive Buttons) */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                3. Dense Surface Performance Benchmark
              </h2>
              <p className="text-xs text-[var(--text-muted)]">
                24 live refractive buttons rendered simultaneously — verifying locked 60 FPS fill
                rate.
              </p>
            </div>
            <GlassButton
              variant="outline"
              size="sm"
              onClick={() =>
                setDenseItems((prev) => [
                  ...prev,
                  {
                    id: `item-${prev.length + 1}`,
                    name: `Dynamic SKU-00${prev.length + 1}`,
                    stock: 50,
                    price: 2500,
                    status: "verified",
                  },
                ])
              }
            >
              <Plus className="w-3 h-3" />
              Add Row
            </GlassButton>
          </div>

          <div className="rounded-3xl bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] overflow-hidden">
            <div className="p-4 border-b border-[var(--border)] flex items-center justify-between gap-4">
              <div className="w-72">
                <GlassInput
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  icon={<Search className="w-3.5 h-3.5" />}
                  placeholder="Search wholesale products..."
                />
              </div>
              <span className="text-xs text-[var(--text-muted)] font-mono">
                {denseItems.length} active rows • 24 GlassButtons
              </span>
            </div>

            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-xs text-left">
                <thead className="text-[11px] text-[var(--text-muted)] uppercase tracking-wider bg-[var(--surface-hover)] border-b border-[var(--border)] sticky top-0 backdrop-blur-md">
                  <tr>
                    <th className="px-5 py-3">Product / SKU</th>
                    <th className="px-5 py-3">Stock Units</th>
                    <th className="px-5 py-3">Wholesale Price</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Quick Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {denseItems.map((item) => (
                    <tr
                      key={item.id}
                      className="hover:bg-[var(--surface-hover)] transition-colors group"
                    >
                      <td className="px-5 py-3.5 font-medium text-[var(--text)]">{item.name}</td>
                      <td className="px-5 py-3.5 font-mono text-[var(--text-muted)]">
                        {item.stock} bags
                      </td>
                      <td className="px-5 py-3.5 font-mono font-semibold text-[var(--text)]">
                        ₹{item.price.toLocaleString("en-IN")}
                      </td>
                      <td className="px-5 py-3.5">
                        {item.status === "verified" && (
                          <GlassBadge variant="success" dot>
                            In Stock
                          </GlassBadge>
                        )}
                        {item.status === "warning" && (
                          <GlassBadge variant="warning" dot>
                            Reorder
                          </GlassBadge>
                        )}
                        {item.status === "critical" && (
                          <GlassBadge variant="error" dot>
                            Low Stock
                          </GlassBadge>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <GlassButton
                          variant="secondary"
                          size="sm"
                          onClick={() => setModalOpen(true)}
                        >
                          Quick Edit
                        </GlassButton>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Modal Demo */}
        <GlassModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Adjust Retailer Terms & Credit Limit"
          description="Elevated glass surface demonstrating full-strength specular border refraction and spring motion choreography."
        >
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-[var(--surface-hover)] border border-[var(--border)] space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Retailer:</span>
                <span className="font-semibold text-[var(--text)]">Supreme Mart Wholesale</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Current Term:</span>
                <span className="font-mono text-[var(--accent)] font-bold">15 Days Net</span>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-[var(--text-muted)]">
                New Authorized Credit Limit (₹)
              </label>
              <GlassInput defaultValue="75000" type="number" />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <GlassButton variant="secondary" size="md" onClick={() => setModalOpen(false)}>
                Cancel
              </GlassButton>
              <GlassButton variant="primary" size="md" onClick={() => setModalOpen(false)}>
                Save Terms
              </GlassButton>
            </div>
          </div>
        </GlassModal>
      </FadeIn>
    </AppLayout>
  );
}
