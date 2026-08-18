"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { useTheme } from "@/components/ThemeProvider";
import {
  GlassButton,
  GlassCard,
  GlassCardTitle,
  GlassCardDescription,
  GlassModal,
  GlassDropdown,
  GlassInput,
  GlassBadge,
} from "@/components/glass";

import {
  ListViewTemplate,
  DetailViewTemplate,
  FormTemplate,
  FormSection,
  DashboardTemplate,
} from "@/components/templates";
import { AnimeCheckIcon, AnimeMorphIcon, AnimeMicroPress } from "@/components/motion/AnimeMicro";
import { FadeIn } from "@/components/motion/GlassMotion";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import {
  MoreVertical,
  FileSpreadsheet,
  Plus,
  Trash2,
  Edit3,
  Layers,
  Sparkles,
  LayoutGrid,
  Activity,
  Package,
  TrendingUp,
  AlertTriangle,
  Truck,
} from "lucide-react";

export default function StyleguidePage() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState<"primitives" | "templates" | "motion">("primitives");
  const [activeTemplatePreview, setActiveTemplatePreview] = useState<
    "list" | "detail" | "form" | "dashboard"
  >("list");

  // Primitive States
  const [modalOpen, setModalOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("Basmati Premium Export 25kg");
  const denseItems = Array.from({ length: 12 }, (_, i) => ({
    id: `item-${i + 1}`,
    name: `Wholesale Item SKU-00${i + 1}`,
    stock: (i + 1) * 35,
    price: (i + 1) * 1200,
    status: (i % 4 === 0 ? "error" : i % 3 === 0 ? "warning" : "success") as
      "error" | "warning" | "success",
  }));

  // Motion & Anime.js States

  const [animeChecked, setAnimeChecked] = useState(false);
  const [animeMorphed, setAnimeMorphed] = useState(false);
  const [autoListRef] = useAutoAnimate();
  const [interactiveList, setInteractiveList] = useState([
    { id: "1", title: "PO #894 — Basmati Rice 500 Bags", status: "In Transit", priority: "High" },
    {
      id: "2",
      title: "SO #102 — APMC Vashi Grocery Hub",
      status: "Dispatched",
      priority: "Normal",
    },
    {
      id: "3",
      title: "Recall Batch #B-409 (Quarantined)",
      status: "Critical",
      priority: "Immediate",
    },
  ]);

  const addItem = () => {
    const newId = String(Date.now());
    setInteractiveList((prev) => [
      {
        id: newId,
        title: `SO #${Math.floor(Math.random() * 900 + 100)} — Fast Order`,
        status: "Pending",
        priority: "Normal",
      },
      ...prev,
    ]);
  };

  const removeItem = (id: string) => {
    setInteractiveList((prev) => prev.filter((item) => item.id !== id));
  };

  return (
    <AppLayout>
      <FadeIn className="space-y-8 max-w-6xl pb-24">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[var(--border)] pb-6">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <GlassBadge variant="accent" dot>
                Phase 4 Design & Motion
              </GlassBadge>
              <span className="text-xs text-[var(--text-muted)] font-mono">
                Linear / Stripe B2B Benchmark Architecture
              </span>
            </div>
            <h1 className="text-3xl font-black tracking-tight text-[var(--text)]">
              Design System & Motion Showcase
            </h1>
            <p className="text-sm text-[var(--text-muted)] mt-1">
              Liquid Glass Primitives • Four Locked Page Templates • 5-Engine Layered Motion Stack
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

        {/* Master Section Tabs */}
        <div className="flex items-center gap-3 border-b border-[var(--border)] pb-3">
          <GlassButton
            variant={activeTab === "primitives" ? "primary" : "outline"}
            size="sm"
            onClick={() => setActiveTab("primitives")}
          >
            <Layers className="w-3.5 h-3.5" />
            Glass Primitives
          </GlassButton>
          <GlassButton
            variant={activeTab === "templates" ? "primary" : "outline"}
            size="sm"
            onClick={() => setActiveTab("templates")}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            Four Locked Page Templates
          </GlassButton>
          <GlassButton
            variant={activeTab === "motion" ? "primary" : "outline"}
            size="sm"
            onClick={() => setActiveTab("motion")}
          >
            <Activity className="w-3.5 h-3.5" />
            Motion & Anime.js Layer
          </GlassButton>
        </div>

        {/* TAB 1: GLASS PRIMITIVES */}
        {activeTab === "primitives" && (
          <div className="space-y-10">
            {/* 1. GlassButton Suite */}
            <section className="space-y-4">
              <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                1. GlassButton — Specular Refraction & Tactile Compression
              </h2>
              <div className="p-6 rounded-3xl bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] space-y-4">
                <div className="flex flex-wrap gap-4 items-center">
                  <GlassButton variant="primary" size="md">
                    Primary Refractive
                  </GlassButton>
                  <GlassButton variant="secondary" size="md">
                    Secondary Translucent
                  </GlassButton>
                  <GlassButton variant="outline" size="md">
                    Outline Border
                  </GlassButton>
                  <GlassButton variant="ghost" size="md">
                    Ghost Surface
                  </GlassButton>
                  <GlassButton variant="destructive" size="md">
                    Destructive Action
                  </GlassButton>
                </div>
              </div>
            </section>

            {/* 2. GlassCards & Panels */}
            <section className="space-y-4">
              <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                2. GlassCards & Surface Elevation
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <GlassCard hoverable glow className="p-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <GlassBadge variant="accent" dot>
                      Live Telemetry
                    </GlassBadge>
                    <Sparkles className="w-4 h-4 text-[var(--accent)]" />
                  </div>
                  <GlassCardTitle className="text-base">Luminous Specular Bevel</GlassCardTitle>
                  <GlassCardDescription className="text-xs">
                    Tuned for large viewport surface fill rates without GPU texture thrashing.
                  </GlassCardDescription>
                </GlassCard>

                <GlassCard className="p-6 space-y-3">
                  <GlassCardTitle className="text-base">
                    Interactive Controls & Dialogs
                  </GlassCardTitle>
                  <GlassCardDescription className="text-xs">
                    Modal dialogs and dropdown menus render with elevated z-index glass layers.
                  </GlassCardDescription>
                  <div className="flex items-center gap-3 pt-2">
                    <GlassButton variant="primary" size="sm" onClick={() => setModalOpen(true)}>
                      Open GlassModal
                    </GlassButton>
                    <GlassDropdown
                      trigger={
                        <GlassButton variant="outline" size="sm">
                          <MoreVertical className="w-3.5 h-3.5" />
                          Options
                        </GlassButton>
                      }
                      items={[
                        {
                          id: "export",
                          label: "Export CSV Report",
                          icon: <FileSpreadsheet className="w-3.5 h-3.5" />,
                          onClick: () => {},
                        },
                        {
                          id: "duplicate",
                          label: "Duplicate Record",
                          icon: <Edit3 className="w-3.5 h-3.5" />,
                          onClick: () => {},
                        },
                        {
                          id: "archive",
                          label: "Archive Item",
                          icon: <Trash2 className="w-3.5 h-3.5 text-rose-400" />,
                          destructive: true,
                          onClick: () => {},
                        },
                      ]}
                    />
                  </div>
                </GlassCard>
              </div>
            </section>
          </div>
        )}

        {/* TAB 2: FOUR LOCKED PAGE TEMPLATES */}
        {activeTab === "templates" && (
          <div className="space-y-8">
            <div className="flex items-center justify-between p-3 rounded-2xl bg-[var(--surface-overlay)] border border-[var(--glass-border)]">
              <span className="text-xs font-semibold text-[var(--text-muted)]">
                Previewing Template Blueprint:
              </span>
              <div className="flex items-center gap-2">
                <GlassButton
                  variant={activeTemplatePreview === "list" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setActiveTemplatePreview("list")}
                >
                  1. ListView
                </GlassButton>
                <GlassButton
                  variant={activeTemplatePreview === "detail" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setActiveTemplatePreview("detail")}
                >
                  2. DetailView (8/4 Grid)
                </GlassButton>
                <GlassButton
                  variant={activeTemplatePreview === "form" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setActiveTemplatePreview("form")}
                >
                  3. Form (Sticky Bar)
                </GlassButton>
                <GlassButton
                  variant={activeTemplatePreview === "dashboard" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setActiveTemplatePreview("dashboard")}
                >
                  4. Dashboard (KPIs)
                </GlassButton>
              </div>
            </div>

            {/* Template 1: ListView Demo */}
            {activeTemplatePreview === "list" && (
              <div className="p-6 rounded-3xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-xl">
                <ListViewTemplate
                  title="Wholesale Inventory Catalog"
                  description="Real-time stock ledger, batch tracking, and automatic reorder thresholds."
                  badge={<GlassBadge variant="accent">320 Total SKUs</GlassBadge>}
                  primaryAction={
                    <GlassButton variant="primary" size="md">
                      <Plus className="w-3.5 h-3.5" />
                      Add Product
                    </GlassButton>
                  }
                  secondaryActions={
                    <GlassButton variant="outline" size="md">
                      <FileSpreadsheet className="w-3.5 h-3.5" />
                      Export CSV
                    </GlassButton>
                  }
                  searchQuery={searchValue}
                  onSearchChange={setSearchValue}
                  filters={
                    <div className="flex items-center gap-2">
                      <GlassBadge variant="neutral" className="cursor-pointer">
                        All Categories
                      </GlassBadge>
                      <GlassBadge variant="warning" className="cursor-pointer">
                        Low Stock (4)
                      </GlassBadge>
                      <GlassBadge variant="error" className="cursor-pointer">
                        Quarantined (1)
                      </GlassBadge>
                    </div>
                  }
                  pagination={
                    <>
                      <span className="text-xs text-[var(--text-muted)]">
                        Showing 1-12 of 320 records
                      </span>
                      <div className="flex gap-2">
                        <GlassButton variant="outline" size="sm" disabled>
                          Previous
                        </GlassButton>
                        <GlassButton variant="outline" size="sm">
                          Next
                        </GlassButton>
                      </div>
                    </>
                  }
                >
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[var(--border)] text-[var(--text-muted)]">
                        <th className="p-3">SKU</th>
                        <th className="p-3">Item Description</th>
                        <th className="p-3">Stock Units</th>
                        <th className="p-3">Wholesale Price</th>
                        <th className="p-3 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {denseItems.slice(0, 5).map((item) => (
                        <tr
                          key={item.id}
                          className="border-b border-[var(--border)] hover:bg-[var(--surface-hover)] transition-colors"
                        >
                          <td className="p-3 font-mono text-[var(--accent)] font-semibold">
                            {item.name.split(" ")[2]}
                          </td>
                          <td className="p-3 font-medium text-[var(--text)]">{item.name}</td>
                          <td className="p-3 font-mono">{item.stock} bags</td>
                          <td className="p-3 font-mono font-semibold">
                            ₹{item.price.toLocaleString("en-IN")}
                          </td>
                          <td className="p-3 text-right">
                            <GlassBadge variant={item.status} dot>
                              {item.status}
                            </GlassBadge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </ListViewTemplate>
              </div>
            )}

            {/* Template 2: DetailView Demo */}
            {activeTemplatePreview === "detail" && (
              <div className="p-6 rounded-3xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-xl">
                <DetailViewTemplate
                  title="Purchase Order #PO-2026-089"
                  subtitle="Supplier: Royal Agro Foods Pvt Ltd • FSSAI #11521018000492"
                  backHref="/styleguide"
                  backLabel="Back to Styleguide"
                  statusBadge={
                    <GlassBadge variant="success" dot>
                      Confirmed by Supplier
                    </GlassBadge>
                  }
                  primaryAction={
                    <GlassButton variant="primary" size="md">
                      <Truck className="w-3.5 h-3.5" />
                      Receive Stock (GRN)
                    </GlassButton>
                  }
                  secondaryActions={
                    <GlassButton variant="outline" size="md">
                      Download PDF
                    </GlassButton>
                  }
                  sidePanel={
                    <div className="space-y-4">
                      <GlassCard className="p-5 space-y-3">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                          Supplier Coordinates
                        </h3>
                        <div className="space-y-2 text-xs">
                          <div>
                            <span className="text-[var(--text-muted)] block">GSTIN:</span>
                            <span className="font-mono font-semibold">27AAACR1234F1Z5</span>
                          </div>
                          <div>
                            <span className="text-[var(--text-muted)] block">
                              Dispatch Terminal:
                            </span>
                            <span className="font-medium">Bhiwandi Central Hub #4</span>
                          </div>
                        </div>
                      </GlassCard>

                      <GlassCard className="p-5 space-y-3">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                          Order Financials
                        </h3>
                        <div className="space-y-1.5 text-xs">
                          <div className="flex justify-between">
                            <span className="text-[var(--text-muted)]">Subtotal:</span>
                            <span className="font-mono">₹4,50,000</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[var(--text-muted)]">GST (5%):</span>
                            <span className="font-mono">₹22,500</span>
                          </div>
                          <div className="flex justify-between pt-2 border-t border-[var(--border)] font-bold text-[var(--accent)] text-sm">
                            <span>Total Payable:</span>
                            <span className="font-mono">₹4,72,500</span>
                          </div>
                        </div>
                      </GlassCard>
                    </div>
                  }
                >
                  <GlassCard className="p-6 space-y-4">
                    <h3 className="text-sm font-bold text-[var(--text)]">
                      PO Line Items (500 Bags Total)
                    </h3>
                    <div className="p-3 rounded-2xl bg-[var(--surface-hover)] text-xs flex justify-between">
                      <span>Basmati Premium Extra Long 25kg</span>
                      <span className="font-mono font-bold">500 units @ ₹900/unit</span>
                    </div>
                  </GlassCard>
                </DetailViewTemplate>
              </div>
            )}

            {/* Template 3: FormTemplate Demo */}
            {activeTemplatePreview === "form" && (
              <div className="p-6 rounded-3xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-xl">
                <FormTemplate
                  title="Onboard Wholesale Retailer Account"
                  description="Configure credit limits, pricing tier, and KYC compliance."
                  backHref="/styleguide"
                  backLabel="Back to Styleguide"
                  isDirty={true}
                  submitLabel="Save Retailer Account"
                >
                  <FormSection
                    title="1. Retailer Identity & Legal"
                    description="Official business name and GSTIN coordinates."
                  >
                    <div className="col-span-12 sm:col-span-6 space-y-1.5">
                      <label className="text-xs font-medium text-[var(--text-muted)]">
                        Business Name
                      </label>
                      <GlassInput defaultValue="Vashi APMC Wholesale Traders" />
                    </div>
                    <div className="col-span-12 sm:col-span-6 space-y-1.5">
                      <label className="text-xs font-medium text-[var(--text-muted)]">
                        GSTIN Number
                      </label>
                      <GlassInput defaultValue="27AABCU9603R1ZM" className="font-mono" />
                    </div>
                  </FormSection>

                  <FormSection
                    title="2. Credit Terms & Pricing Tier"
                    description="Configure default credit limits and pricing multiplier."
                  >
                    <div className="col-span-12 sm:col-span-6 space-y-1.5">
                      <label className="text-xs font-medium text-[var(--text-muted)]">
                        Credit Limit (₹)
                      </label>
                      <GlassInput defaultValue="500000" className="font-mono" />
                    </div>
                    <div className="col-span-12 sm:col-span-6 space-y-1.5">
                      <label className="text-xs font-medium text-[var(--text-muted)]">
                        Pricing Tier
                      </label>
                      <GlassInput defaultValue="Tier-A (High Volume)" />
                    </div>
                  </FormSection>
                </FormTemplate>
              </div>
            )}

            {/* Template 4: DashboardTemplate Demo */}
            {activeTemplatePreview === "dashboard" && (
              <div className="p-6 rounded-3xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-xl">
                <DashboardTemplate
                  title="Executive Wholesale Overview"
                  description="Live telemetry synced across Bhiwandi Hub and APMC Terminal."
                  kpiMetrics={[
                    {
                      id: "1",
                      title: "Daily Revenue",
                      value: "₹8,45,200",
                      change: "+18.4%",
                      trend: "up",
                      icon: <TrendingUp className="w-4 h-4" />,
                    },
                    {
                      id: "2",
                      title: "Active Dispatches",
                      value: "38 Orders",
                      change: "+4 pending",
                      trend: "neutral",
                      icon: <Truck className="w-4 h-4" />,
                    },
                    {
                      id: "3",
                      title: "Low Stock Alerts",
                      value: "4 SKUs",
                      change: "-2 reordered",
                      trend: "down",
                      icon: <AlertTriangle className="w-4 h-4 text-amber-500" />,
                    },
                    {
                      id: "4",
                      title: "Total Warehouse Bags",
                      value: "14,820",
                      change: "+98.2% cap",
                      trend: "up",
                      icon: <Package className="w-4 h-4" />,
                    },
                  ]}
                  mainContent={
                    <GlassCard className="p-6 space-y-3 h-64 flex flex-col justify-center items-center text-center">
                      <TrendingUp className="w-8 h-8 text-[var(--accent)] mb-2" />
                      <GlassCardTitle>Revenue Run-Rate & Order Velocity</GlassCardTitle>
                      <GlassCardDescription className="max-w-md text-xs">
                        Real-time revenue charting container utilizing 8-column layout span.
                      </GlassCardDescription>
                    </GlassCard>
                  }
                  sideContent={
                    <GlassCard className="p-6 space-y-3">
                      <GlassCardTitle className="text-xs uppercase tracking-wider text-[var(--text-muted)]">
                        Urgent Operations Queue
                      </GlassCardTitle>
                      <div className="space-y-2 text-xs">
                        <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
                          Reorder 500 bags Basmati Export (Warehouse 1)
                        </div>
                        <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-[var(--accent)]">
                          Schedule Vehicle Run MH-04-AB-1290
                        </div>
                      </div>
                    </GlassCard>
                  }
                />
              </div>
            )}
          </div>
        )}

        {/* TAB 3: MOTION & ANIME.JS LAYER */}
        {activeTab === "motion" && (
          <div className="space-y-8">
            {/* Anime.js Demo */}
            <section className="space-y-4">
              <div className="flex items-center gap-2">
                <GlassBadge variant="accent" dot>
                  anime.js 5th Motion Engine
                </GlassBadge>
                <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                  SVG Path Morphing & Micro-Interaction Demos
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* 1. Animated Check Draw */}
                <GlassCard className="p-6 space-y-4 text-center flex flex-col items-center">
                  <div className="w-12 h-12 rounded-2xl bg-[var(--surface-hover)] flex items-center justify-center text-[var(--accent)] border border-[var(--border)]">
                    <AnimeCheckIcon checked={animeChecked} size={26} />
                  </div>
                  <GlassCardTitle className="text-sm">SVG Path Draw-In</GlassCardTitle>
                  <GlassCardDescription className="text-xs">
                    strokeDashoffset animated via anime.js easing curves.
                  </GlassCardDescription>
                  <GlassButton
                    variant="outline"
                    size="sm"
                    onClick={() => setAnimeChecked((c) => !c)}
                  >
                    Toggle Check ({animeChecked ? "Checked" : "Unchecked"})
                  </GlassButton>
                </GlassCard>

                {/* 2. Geometric Path Morph */}
                <GlassCard className="p-6 space-y-4 text-center flex flex-col items-center">
                  <div className="w-12 h-12 rounded-2xl bg-[var(--surface-hover)] flex items-center justify-center text-[var(--accent)] border border-[var(--border)]">
                    <AnimeMorphIcon active={animeMorphed} size={26} />
                  </div>
                  <GlassCardTitle className="text-sm">SVG Shape Morphing</GlassCardTitle>
                  <GlassCardDescription className="text-xs">
                    Numeric d-path coordinate interpolation between Box & Octagon.
                  </GlassCardDescription>
                  <GlassButton
                    variant="outline"
                    size="sm"
                    onClick={() => setAnimeMorphed((m) => !m)}
                  >
                    Morph Shape ({animeMorphed ? "Diamond" : "Square"})
                  </GlassButton>
                </GlassCard>

                {/* 3. Micro Elastic Press */}
                <GlassCard className="p-6 space-y-4 text-center flex flex-col items-center">
                  <AnimeMicroPress className="p-4 rounded-2xl bg-[var(--surface-hover)] border border-[var(--accent-border)] text-[var(--accent)] font-semibold text-xs shadow-md">
                    Click & Hold For Elastic Snap
                  </AnimeMicroPress>
                  <GlassCardTitle className="text-sm">Elastic Button Press</GlassCardTitle>
                  <GlassCardDescription className="text-xs">
                    Direct scale interpolation with easeOutElastic solver.
                  </GlassCardDescription>
                </GlassCard>
              </div>
            </section>

            {/* AutoAnimate List Diffing Demo */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                    @formkit/auto-animate — Zero-Config List Mutations
                  </h2>
                  <p className="text-xs text-[var(--text-muted)]">
                    Smoothly inserts and removes elements from the DOM without layout jump.
                  </p>
                </div>
                <GlassButton variant="primary" size="sm" onClick={addItem}>
                  <Plus className="w-3.5 h-3.5" />
                  Add Item
                </GlassButton>
              </div>

              <div ref={autoListRef} className="space-y-3">
                {interactiveList.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 rounded-2xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-md flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-[var(--text)]">{item.title}</span>
                      <GlassBadge variant={item.status === "Critical" ? "error" : "neutral"}>
                        {item.status}
                      </GlassBadge>
                    </div>
                    <GlassButton
                      variant="ghost"
                      size="sm"
                      onClick={() => removeItem(item.id)}
                      className="text-rose-400 hover:text-rose-300"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </GlassButton>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}

        {/* Reusable GlassModal Demo */}
        <GlassModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Elevated Specular Refraction Modal"
          description="Rendered with backdrop-blur-2xl, spring physics entrance, and auto-focus trap."
        >
          <div className="space-y-4 text-xs text-[var(--text-muted)]">
            <p>This dialog demonstrates the elevated layer of the Liquid Glass design system.</p>
            <div className="flex justify-end gap-2 pt-2 border-t border-[var(--border)]">
              <GlassButton variant="ghost" size="sm" onClick={() => setModalOpen(false)}>
                Cancel
              </GlassButton>
              <GlassButton variant="primary" size="sm" onClick={() => setModalOpen(false)}>
                Confirm Action
              </GlassButton>
            </div>
          </div>
        </GlassModal>
      </FadeIn>
    </AppLayout>
  );
}
