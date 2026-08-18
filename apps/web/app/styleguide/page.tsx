"use client";

import React, { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { useTheme } from "@/components/ThemeProvider";
import {
  GlassButton,
  GlassCard,
  GlassCardTitle,
  GlassCardDescription,
  GlassModal,
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
import { StatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import { SkeletonCard } from "@/components/SkeletonPrimitives";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import {
  FileSpreadsheet,
  Plus,
  Trash2,
  Edit3,
  Layers,
  LayoutGrid,
  Activity,
  Package,
  TrendingUp,
  AlertTriangle,
  Truck,
  TableProperties,
  Cpu,
} from "lucide-react";

interface SampleWholesaleItem {
  id: string;
  sku: string;
  name: string;
  category: string;
  stock: number;
  price: number;
  status: string;
}

export default function StyleguidePage() {
  const { theme, resolvedTheme, setTheme, isLowPower, toggleLowPower } = useTheme();
  const [activeTab, setActiveTab] = useState<
    "primitives" | "data-primitives" | "templates" | "motion"
  >("primitives");
  const [activeTemplatePreview, setActiveTemplatePreview] = useState<
    "list" | "detail" | "form" | "dashboard"
  >("list");

  // Primitive States
  const [modalOpen, setModalOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("Basmati Premium Export 25kg");

  // DataTable Sample Data
  const [tableLoading, setTableLoading] = useState(false);
  const [tableData, setTableData] = useState<SampleWholesaleItem[]>([
    {
      id: "sku-1",
      sku: "RICE-BAS-01",
      name: "Basmati Premium Export 25kg",
      category: "Grains & Rice",
      stock: 450,
      price: 2450,
      status: "in_stock",
    },
    {
      id: "sku-2",
      sku: "OIL-SUN-05",
      name: "Sunflower Pure Cooking Oil 15L",
      category: "Edible Oils",
      stock: 42,
      price: 1850,
      status: "low_stock",
    },
    {
      id: "sku-3",
      sku: "WHT-AAT-10",
      name: "Chakki Fresh Whole Wheat 50kg",
      category: "Flours & Grains",
      stock: 0,
      price: 1680,
      status: "out_of_stock",
    },
    {
      id: "sku-4",
      sku: "PUL-TUR-02",
      name: "Organic Tur Dal Polished 30kg",
      category: "Pulses",
      stock: 620,
      price: 3200,
      status: "in_stock",
    },
    {
      id: "sku-5",
      sku: "SUG-REF-01",
      name: "Refined Crystal Sugar M-30 50kg",
      category: "Sugar & Sweeteners",
      stock: 890,
      price: 1950,
      status: "overstocked",
    },
  ]);

  const tableColumns: DataTableColumn<SampleWholesaleItem>[] = [
    {
      key: "sku",
      header: "SKU / Code",
      sortable: true,
      mobilePrimary: true,
      render: (item) => (
        <div>
          <span className="font-mono font-bold text-[var(--accent)] block text-xs">{item.sku}</span>
          <span className="text-[var(--text)] font-semibold text-xs">{item.name}</span>
        </div>
      ),
    },
    {
      key: "category",
      header: "Category",
      sortable: true,
      mobileLabel: "Category",
      render: (item) => <span className="text-[var(--text-muted)] text-xs">{item.category}</span>,
    },
    {
      key: "stock",
      header: "Stock (Bags)",
      sortable: true,
      align: "right",
      mobileLabel: "Current Stock",
      render: (item) => (
        <span className="font-mono font-semibold text-xs">
          {item.stock.toLocaleString("en-IN")}
        </span>
      ),
    },
    {
      key: "price",
      header: "Wholesale Price (₹)",
      sortable: true,
      align: "right",
      mobileLabel: "Wholesale Price",
      render: (item) => (
        <span className="font-mono text-xs text-[var(--text)]">
          ₹{item.price.toLocaleString("en-IN")}
        </span>
      ),
    },
    {
      key: "status",
      header: "Stock Level",
      sortable: true,
      mobileLabel: "Inventory Status",
      render: (item) => <StatusBadge status={item.status} />,
    },
    {
      key: "actions",
      header: "Action",
      align: "right",
      render: () => (
        <GlassButton variant="ghost" size="sm">
          Inspect
        </GlassButton>
      ),
    },
  ];

  // Motion & Anime.js States
  const [animeChecked, setAnimeChecked] = useState(false);
  const [animeMorphed, setAnimeMorphed] = useState(false);
  const [autoListRef] = useAutoAnimate();
  const [interactiveList, setInteractiveList] = useState([
    { id: "1", title: "PO #894 — Basmati Rice 500 Bags", status: "in_transit", priority: "High" },
    {
      id: "2",
      title: "SO #102 — APMC Vashi Grocery Hub",
      status: "dispatched",
      priority: "Normal",
    },
    {
      id: "3",
      title: "Recall Batch #B-409 (Quarantined)",
      status: "critical",
      priority: "Immediate",
    },
  ]);

  const addItem = () => {
    const newId = String(Date.now());
    setInteractiveList((prev) => [
      {
        id: newId,
        title: `SO #${Math.floor(Math.random() * 900 + 100)} — Fast Order`,
        status: "processing",
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
              Liquid Glass Primitives • Empty/Skeleton/Status Primitives • Responsive DataTable •
              Layered Motion Stack
            </p>
          </div>

          {/* Controls Widget: Theme + Low Power Fallback */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={toggleLowPower}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all border ${
                isLowPower
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-sm"
                  : "bg-[var(--surface-hover)] text-[var(--text-muted)] border-[var(--border)] hover:text-[var(--text)]"
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Low-Power Glass: {isLowPower ? "ON (Flat)" : "OFF (Refract)"}</span>
            </button>

            <div className="flex items-center gap-1 p-1 rounded-2xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-md">
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
        </div>

        {/* Master Section Tabs */}
        <div className="flex items-center gap-2 border-b border-[var(--border)] pb-3 overflow-x-auto">
          <GlassButton
            variant={activeTab === "primitives" ? "primary" : "outline"}
            size="sm"
            onClick={() => setActiveTab("primitives")}
          >
            <Layers className="w-3.5 h-3.5" />
            Glass Primitives
          </GlassButton>
          <GlassButton
            variant={activeTab === "data-primitives" ? "primary" : "outline"}
            size="sm"
            onClick={() => setActiveTab("data-primitives")}
          >
            <TableProperties className="w-3.5 h-3.5" />
            Empty / Skeleton / Status / Table
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
                <div className="flex flex-wrap gap-4 items-center">
                  <GlassButton variant="primary" size="sm">
                    Small
                  </GlassButton>
                  <GlassButton variant="primary" size="md">
                    Medium
                  </GlassButton>
                  <GlassButton variant="primary" size="lg">
                    Large Interactive
                  </GlassButton>
                  <GlassButton variant="primary" size="md" disabled>
                    Disabled State
                  </GlassButton>
                </div>
              </div>
            </section>

            {/* 2. GlassCard & Modal */}
            <section className="space-y-4">
              <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                2. GlassCard & Modal Primitives
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <GlassCard hoverable className="p-6 space-y-3">
                  <GlassBadge variant="accent">GlassCard Hoverable</GlassBadge>
                  <GlassCardTitle>Linear-Grade Surface Card</GlassCardTitle>
                  <GlassCardDescription>
                    Specially calibrated specular top-border gradient simulating real physical glass
                    thickness.
                  </GlassCardDescription>
                </GlassCard>

                <GlassCard className="p-6 space-y-3 flex flex-col justify-between">
                  <div>
                    <GlassBadge variant="neutral">GlassModal Trigger</GlassBadge>
                    <GlassCardTitle className="mt-2">Elevated Modal Layer</GlassCardTitle>
                    <GlassCardDescription>
                      Full-screen backdrop blur and spring scale entrance.
                    </GlassCardDescription>
                  </div>
                  <GlassButton variant="primary" size="sm" onClick={() => setModalOpen(true)}>
                    Open Elevated GlassModal
                  </GlassButton>
                </GlassCard>
              </div>
            </section>
          </div>
        )}

        {/* TAB 2: DATA PRIMITIVES (Empty / Skeleton / Status / DataTable) */}
        {activeTab === "data-primitives" && (
          <div className="space-y-12">
            {/* 1. StatusBadge Full Enum Matrix */}
            <section className="space-y-4">
              <div>
                <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                  1. Universal StatusBadge — Schema Enum Matrix
                </h2>
                <p className="text-xs text-[var(--text-muted)]">
                  Every PO, SO, Invoice, Delivery, Return, Stock Level, and Auth status enum mapped
                  to standard token colors.
                </p>
              </div>

              <div className="p-6 rounded-3xl bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] space-y-6">
                <div>
                  <span className="text-[11px] font-bold text-[var(--text-subtle)] uppercase tracking-wider font-mono block mb-2.5">
                    Orders & Fulfillment Statuses
                  </span>
                  <div className="flex flex-wrap gap-2.5">
                    <StatusBadge status="draft" />
                    <StatusBadge status="submitted" />
                    <StatusBadge status="confirmed" />
                    <StatusBadge status="processing" />
                    <StatusBadge status="packed" />
                    <StatusBadge status="dispatched" />
                    <StatusBadge status="delivered" />
                    <StatusBadge status="partially_received" />
                    <StatusBadge status="received" />
                    <StatusBadge status="cancelled" />
                  </div>
                </div>

                <div>
                  <span className="text-[11px] font-bold text-[var(--text-subtle)] uppercase tracking-wider font-mono block mb-2.5">
                    Invoicing & Financial Statuses
                  </span>
                  <div className="flex flex-wrap gap-2.5">
                    <StatusBadge status="issued" />
                    <StatusBadge status="paid" />
                    <StatusBadge status="partially_paid" />
                    <StatusBadge status="overdue" />
                    <StatusBadge status="upi" />
                    <StatusBadge status="neft_rtgs" />
                    <StatusBadge status="credit" />
                  </div>
                </div>

                <div>
                  <span className="text-[11px] font-bold text-[var(--text-subtle)] uppercase tracking-wider font-mono block mb-2.5">
                    Inventory, Warehouse & Quality Control
                  </span>
                  <div className="flex flex-wrap gap-2.5">
                    <StatusBadge status="in_stock" />
                    <StatusBadge status="low_stock" />
                    <StatusBadge status="out_of_stock" />
                    <StatusBadge status="overstocked" />
                    <StatusBadge status="inward" />
                    <StatusBadge status="outward" />
                    <StatusBadge status="good" />
                    <StatusBadge status="damaged" />
                    <StatusBadge status="critical" />
                  </div>
                </div>

                <div>
                  <span className="text-[11px] font-bold text-[var(--text-subtle)] uppercase tracking-wider font-mono block mb-2.5">
                    Security, 2FA & Staff Access
                  </span>
                  <div className="flex flex-wrap gap-2.5">
                    <StatusBadge status="active" />
                    <StatusBadge status="suspended" />
                    <StatusBadge status="invited" />
                    <StatusBadge status="enrolled" />
                    <StatusBadge status="not_enrolled" />
                    <StatusBadge status="required" />
                  </div>
                </div>
              </div>
            </section>

            {/* 2. Universal DataTable with Live Sorting and Mobile Card Restructuring */}
            <section className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                    2. Universal DataTable — Auto Mobile Card-View
                  </h2>
                  <p className="text-xs text-[var(--text-muted)]">
                    Client sorting, key-value card restructuring below 768px, and built-in
                    loading/empty modes.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <GlassButton
                    variant="outline"
                    size="sm"
                    onClick={() => setTableLoading((prev) => !prev)}
                  >
                    Toggle Shimmer Loading ({tableLoading ? "Active" : "Off"})
                  </GlassButton>
                  <GlassButton
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setTableData((prev) =>
                        prev.length > 0
                          ? []
                          : [
                              {
                                id: "sku-1",
                                sku: "RICE-BAS-01",
                                name: "Basmati Premium Export 25kg",
                                category: "Grains & Rice",
                                stock: 450,
                                price: 2450,
                                status: "in_stock",
                              },
                            ],
                      )
                    }
                  >
                    Toggle Empty State
                  </GlassButton>
                </div>
              </div>

              <DataTable
                columns={tableColumns}
                data={tableData}
                keyExtractor={(item) => item.id}
                isLoading={tableLoading}
                emptyTitle="No wholesale items in catalog"
                emptyDescription="Add a new SKU batch or clear your active category filters to view records."
                emptyAction={
                  <GlassButton variant="primary" size="sm">
                    <Plus className="w-3.5 h-3.5" />
                    Add First Product
                  </GlassButton>
                }
              />
            </section>

            {/* 3. Skeleton Shimmer Loaders */}
            <section className="space-y-4">
              <div>
                <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                  3. Skeleton Shimmer Primitives
                </h2>
                <p className="text-xs text-[var(--text-muted)]">
                  Fluid gradient sweep animations replacing flat static placeholders.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <SkeletonCard variant="kpi" />
                <SkeletonCard variant="kpi" />
                <SkeletonCard variant="kpi" />
              </div>
            </section>

            {/* 4. EmptyState Showcase */}
            <section className="space-y-4">
              <div>
                <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                  4. EmptyState Component
                </h2>
                <p className="text-xs text-[var(--text-muted)]">
                  Motion-driven empty placeholder with action slots and warehouse-appropriate copy.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <EmptyState
                  title="No Inward Dispatches Scheduled"
                  description="All pending Purchase Orders have been received into inventory."
                  action={
                    <GlassButton variant="primary" size="sm">
                      <Plus className="w-3.5 h-3.5" />
                      Create Purchase Order
                    </GlassButton>
                  }
                />

                <EmptyState
                  compact
                  title="No Active Low-Stock Alerts"
                  description="All warehouse SKU balances are currently above their reorder points."
                />
              </div>
            </section>
          </div>
        )}

        {/* TAB 3: LOCKED TEMPLATES */}
        {activeTab === "templates" && (
          <div className="space-y-8">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
              <span className="text-xs text-[var(--text-muted)]">Select Template to inspect:</span>
              <div className="flex gap-2">
                <GlassButton
                  variant={activeTemplatePreview === "list" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setActiveTemplatePreview("list")}
                >
                  1. List View
                </GlassButton>
                <GlassButton
                  variant={activeTemplatePreview === "detail" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setActiveTemplatePreview("detail")}
                >
                  2. Detail View (8/4)
                </GlassButton>
                <GlassButton
                  variant={activeTemplatePreview === "form" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setActiveTemplatePreview("form")}
                >
                  3. Form (Sticky Action)
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
                  <DataTable columns={tableColumns} data={tableData} keyExtractor={(i) => i.id} />
                </ListViewTemplate>
              </div>
            )}

            {/* Template 2: DetailView Demo */}
            {activeTemplatePreview === "detail" && (
              <div className="p-6 rounded-3xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-xl">
                <DetailViewTemplate
                  title="Product: Basmati Premium Export 25kg"
                  subtitle="SKU: RICE-BAS-01 • Category: Grains & Cereals"
                  statusBadge={<StatusBadge status="in_stock" />}
                  backHref="#templates"
                  backLabel="Back to Inventory"
                  primaryAction={
                    <GlassButton variant="primary" size="sm">
                      Receive Stock (GRN)
                    </GlassButton>
                  }
                  secondaryActions={
                    <GlassButton variant="outline" size="sm">
                      <Edit3 className="w-3.5 h-3.5" />
                      Edit SKU
                    </GlassButton>
                  }
                  sidePanel={
                    <GlassCard className="p-5 space-y-4 text-xs">
                      <GlassCardTitle className="text-xs uppercase tracking-wider text-[var(--text-muted)]">
                        Wholesale Pricing & Taxes
                      </GlassCardTitle>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-[var(--text-muted)]">Wholesale Price</span>
                          <span className="font-mono font-bold">₹2,450.00 / bag</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[var(--text-muted)]">GST Rate</span>
                          <span className="font-mono font-bold text-emerald-400">5% GST</span>
                        </div>
                      </div>
                    </GlassCard>
                  }
                >
                  <div className="space-y-6">
                    <GlassCard className="p-6 space-y-4">
                      <GlassCardTitle className="text-base">Batch Breakdown (FIFO)</GlassCardTitle>
                      <div className="space-y-3">
                        <div className="p-3.5 rounded-xl bg-[var(--surface-hover)] flex items-center justify-between text-xs">
                          <div>
                            <span className="font-mono font-bold text-[var(--accent)] block">
                              Batch #B-89021 (450 Bags)
                            </span>
                            <span className="text-[var(--text-muted)]">
                              Received: 2026-08-10 • Expiry: 2028-08-10
                            </span>
                          </div>
                          <StatusBadge status="good" />
                        </div>
                      </div>
                    </GlassCard>
                  </div>
                </DetailViewTemplate>
              </div>
            )}

            {/* Template 3: FormTemplate Demo */}
            {activeTemplatePreview === "form" && (
              <div className="p-6 rounded-3xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-xl">
                <FormTemplate
                  title="Create Wholesale Purchase Order"
                  description="Issue authorized procurement order with automatic FSSAI & GST validation."
                  backHref="#templates"
                  onSubmit={(e) => {
                    e.preventDefault();
                    alert("PO Saved");
                  }}
                  submitLabel="Authorize & Issue PO"
                  isSubmitting={false}
                >
                  <FormSection
                    title="1. Supplier & Procurement Terminal"
                    description="Select verified manufacturer."
                  >
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-[var(--text)]">
                          Supplier Account
                        </label>
                        <GlassInput defaultValue="Royal Agro Food Mills Pvt Ltd" />
                      </div>
                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-[var(--text)]">
                          Destination Terminal
                        </label>
                        <GlassInput defaultValue="Bhiwandi Central Hub (Terminal #1)" />
                      </div>
                    </div>
                  </FormSection>
                </FormTemplate>
              </div>
            )}

            {/* Template 4: DashboardTemplate Demo */}
            {activeTemplatePreview === "dashboard" && (
              <div className="p-6 rounded-3xl bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-xl">
                <DashboardTemplate
                  title="Executive Wholesale Dashboard"
                  description="Real-time GMV, batch expiry risk radar, and terminal dispatch velocity."
                  badge={<StatusBadge status="in_stock" overrideLabel="Live Sync" />}
                  kpiMetrics={[
                    {
                      id: "kpi-gmv",
                      title: "Daily Wholesale GMV",
                      value: "₹8,45,200",
                      change: "+18.4% vs yesterday",
                      trend: "up",
                      icon: <TrendingUp className="w-4 h-4" />,
                    },
                    {
                      id: "kpi-dispatches",
                      title: "Active Vehicle Dispatches",
                      value: "38 Runs",
                      change: "4 trucks en-route",
                      trend: "neutral",
                      icon: <Truck className="w-4 h-4" />,
                    },
                    {
                      id: "kpi-low-stock",
                      title: "Low Stock Triggers",
                      value: "4 SKUs",
                      change: "2 POs drafted",
                      trend: "down",
                      icon: <AlertTriangle className="w-4 h-4 text-amber-500" />,
                    },
                    {
                      id: "kpi-bags",
                      title: "Warehouse Bags in Stock",
                      value: "14,820 bags",
                      change: "98.2% capacity",
                      trend: "up",
                      icon: <Package className="w-4 h-4" />,
                    },
                  ]}
                  mainContent={
                    <GlassCard className="p-6 space-y-4">
                      <GlassCardTitle className="text-base">
                        Recent Wholesale Dispatches
                      </GlassCardTitle>
                      <DataTable
                        columns={tableColumns}
                        data={tableData}
                        keyExtractor={(i) => i.id}
                      />
                    </GlassCard>
                  }
                  sideContent={
                    <GlassCard className="p-5 space-y-3">
                      <GlassCardTitle className="text-xs uppercase tracking-wider text-[var(--text-muted)]">
                        Terminal Radar
                      </GlassCardTitle>
                      <div className="space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-[var(--text-muted)]">Bhiwandi Hub</span>
                          <StatusBadge status="active" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[var(--text-muted)]">APMC Terminal</span>
                          <StatusBadge status="active" />
                        </div>
                      </div>
                    </GlassCard>
                  }
                />
              </div>
            )}
          </div>
        )}

        {/* TAB 4: MOTION & ANIME.JS */}
        {activeTab === "motion" && (
          <div className="space-y-10">
            {/* Anime.js Micro-Interactions */}
            <section className="space-y-4">
              <h2 className="text-lg font-bold text-[var(--text)] tracking-tight">
                anime.js Micro-Interactions (SVG Path Morphing & Elastic Physics)
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <GlassCard
                  hoverable
                  onClick={() => setAnimeChecked((prev) => !prev)}
                  className="p-6 flex flex-col items-center justify-center text-center space-y-3 cursor-pointer"
                >
                  <AnimeCheckIcon checked={animeChecked} />
                  <GlassCardTitle className="text-sm">SVG Checkmark Draw</GlassCardTitle>
                  <GlassCardDescription className="text-xs">
                    Stroke-dashoffset animation via anime.js.
                  </GlassCardDescription>
                </GlassCard>

                <GlassCard
                  hoverable
                  onClick={() => setAnimeMorphed((prev) => !prev)}
                  className="p-6 flex flex-col items-center justify-center text-center space-y-3 cursor-pointer"
                >
                  <AnimeMorphIcon active={animeMorphed} />
                  <GlassCardTitle className="text-sm">SVG Path Morphing</GlassCardTitle>
                  <GlassCardDescription className="text-xs">
                    Smooth coordinate interpolation.
                  </GlassCardDescription>
                </GlassCard>

                <GlassCard className="p-6 flex flex-col items-center justify-center text-center space-y-3">
                  <AnimeMicroPress className="px-4 py-2 rounded-xl bg-gradient-to-r from-[var(--accent)] to-[var(--accent-hover)] text-white text-xs font-bold shadow-md">
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
                      <StatusBadge status={item.status} />
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
