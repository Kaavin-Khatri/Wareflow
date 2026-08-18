"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { ListViewTemplate } from "@/components/templates/ListViewTemplate";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { apiClient } from "@/lib/api-client";
import {
  History,
  ArrowDownLeft,
  ArrowUpRight,
  SlidersHorizontal,
  RotateCcw,
  RotateCw,
  PlusCircle,
  Warehouse as WarehouseIcon,
  Layers,
} from "lucide-react";


export interface StockMovementItem {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  warehouse_id: string;
  warehouse_name: string;
  batch_id?: string | null;
  batch_no?: string | null;
  type: string;
  quantity: number;
  reference_type?: string | null;
  reference_id?: string | null;
  human_label: string;
  created_by?: string | null;
  created_at: string;
}

export interface StockMovementListResponse {
  items: StockMovementItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

const MOCK_MOVEMENTS: StockMovementItem[] = [
  {
    id: "mov-1",
    product_id: "prod-1",
    product_name: "Organic Whole Milk 1L",
    product_sku: "MILK-ORG-001",
    warehouse_id: "wh-1",
    warehouse_name: "Central Cold Storage",
    batch_id: "batch-1",
    batch_no: "BATCH-2026-0801",
    type: "in",
    quantity: 500,
    reference_type: "purchase_order",
    reference_id: "PO-202608-0001",
    human_label: "PO #PO-202608-0001 (Goods Receipt)",
    created_by: "procurement@wareflow.io",
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
  },
  {
    id: "mov-2",
    product_id: "prod-1",
    product_name: "Organic Whole Milk 1L",
    product_sku: "MILK-ORG-001",
    warehouse_id: "wh-1",
    warehouse_name: "Central Cold Storage",
    batch_id: "batch-1",
    batch_no: "BATCH-2026-0801",
    type: "out",
    quantity: -120,
    reference_type: "sales_order",
    reference_id: "SO-202608-0002",
    human_label: "SO #SO-202608-0002 (Fulfillment Dispatch)",
    created_by: "dispatch@wareflow.io",
    created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
  },
  {
    id: "mov-3",
    product_id: "prod-2",
    product_name: "Royal Basmati Rice 5kg",
    product_sku: "RIC-BAS-005",
    warehouse_id: "wh-1",
    warehouse_name: "Central Distribution Center",
    batch_id: "batch-2",
    batch_no: "BATCH-2026-0810",
    type: "adjustment",
    quantity: -5,
    reference_type: "manual_adjustment",
    reference_id: "damage:Forklift puncture in pallet",
    human_label: "Adjustment: Damage (Forklift puncture in pallet)",
    created_by: "warehouse.staff@wareflow.io",
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
  },
  {
    id: "mov-4",
    product_id: "prod-1",
    product_name: "Organic Whole Milk 1L",
    product_sku: "MILK-ORG-001",
    warehouse_id: "wh-1",
    warehouse_name: "Central Cold Storage",
    batch_id: "batch-1",
    batch_no: "BATCH-2026-0801",
    type: "return_in",
    quantity: 10,
    reference_type: "sales_return",
    reference_id: "RMA-202608-0001",
    human_label: "RMA #RMA-202608-0001 (Retailer Return)",
    created_by: "returns@wareflow.io",
    created_at: new Date(Date.now() - 86400000 * 1).toISOString(),
  },
  {
    id: "mov-5",
    product_id: "prod-2",
    product_name: "Royal Basmati Rice 5kg",
    product_sku: "RIC-BAS-005",
    warehouse_id: "wh-1",
    warehouse_name: "Central Distribution Center",
    batch_id: "batch-2",
    batch_no: "BATCH-2026-0810",
    type: "adjustment",
    quantity: 15,
    reference_type: "manual_adjustment",
    reference_id: "recount:Annual physical audit recount",
    human_label: "Adjustment: Recount (Annual physical audit recount)",
    created_by: "owner@wareflow.io",
    created_at: new Date().toISOString(),
  },
];

export default function StockMovementLedgerPage() {
  const [movements, setMovements] = useState<StockMovementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");

  useEffect(() => {
    let isMounted = true;
    const fetchMovements = async () => {
      try {
        setLoading(true);
        const res = await apiClient.get<StockMovementListResponse>("/stock/movements?page_size=200");
        if (!isMounted) return;
        if (res && res.items && Array.isArray(res.items)) {
          setMovements(res.items);
        } else {
          setMovements(MOCK_MOVEMENTS);
        }
      } catch {
        if (isMounted) setMovements(MOCK_MOVEMENTS);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchMovements();
    return () => {
      isMounted = false;
    };
  }, []);

  // Filter movements
  const filteredMovements = useMemo(() => {
    return movements.filter((m) => {
      // Type Filter
      if (typeFilter !== "ALL" && m.type.toLowerCase() !== typeFilter.toLowerCase()) {
        return false;
      }
      // Search Filter
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        m.product_name.toLowerCase().includes(q) ||
        m.product_sku.toLowerCase().includes(q) ||
        m.warehouse_name.toLowerCase().includes(q) ||
        (m.batch_no && m.batch_no.toLowerCase().includes(q)) ||
        m.human_label.toLowerCase().includes(q) ||
        (m.created_by && m.created_by.toLowerCase().includes(q))
      );
    });
  }, [movements, typeFilter, searchQuery]);

  // Aggregate Metrics
  const metrics = useMemo(() => {
    const totalMovements = movements.length;
    let totalInbound = 0;
    let totalOutbound = 0;
    let totalAdjustments = 0;

    for (const m of movements) {
      const q = Number(m.quantity) || 0;
      const t = m.type.toLowerCase();
      if (t === "in" || t === "return_in") {
        totalInbound += q;
      } else if (t === "out" || t === "return_out") {
        totalOutbound += Math.abs(q);
      } else if (t === "adjustment") {
        totalAdjustments += q;
      }
    }

    return { totalMovements, totalInbound, totalOutbound, totalAdjustments };
  }, [movements]);

  const columns: DataTableColumn<StockMovementItem>[] = [
    {
      key: "created_at",
      header: "Timestamp",
      sortable: true,
      render: (m) => (
        <div className="flex flex-col">
          <span className="font-mono text-xs text-[var(--text)] font-semibold">
            {new Date(m.created_at).toLocaleDateString("en-IN", {
              day: "2-digit",
              month: "short",
              year: "numeric",
            })}
          </span>
          <span className="text-[11px] text-[var(--text-muted)] font-mono">
            {new Date(m.created_at).toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })}
          </span>
        </div>
      ),
    },
    {
      key: "product_name",
      header: "Product & SKU",
      sortable: true,
      render: (m) => (
        <div className="flex flex-col">
          <span className="font-semibold text-xs text-[var(--text)]">{m.product_name}</span>
          <span className="font-mono text-[11px] text-[var(--text-muted)]">{m.product_sku}</span>
        </div>
      ),
    },
    {
      key: "warehouse_name",
      header: "Warehouse / Batch",
      render: (m) => (
        <div className="flex flex-col gap-0.5 text-xs text-[var(--text-muted)]">
          <span className="flex items-center gap-1 text-[var(--text)]">
            <WarehouseIcon className="w-3 h-3 text-purple-400" /> {m.warehouse_name}
          </span>
          {m.batch_no && (
            <span className="font-mono text-[11px] text-cyan-400 font-medium">
              Batch: {m.batch_no}
            </span>
          )}
        </div>
      ),
    },
    {
      key: "type",
      header: "Type",
      align: "center",
      sortable: true,
      render: (m) => {
        const t = m.type.toLowerCase();
        let badgeVariant: "success" | "warning" | "neutral" | "error" = "neutral";
        let label = m.type.toUpperCase();

        if (t === "in") {
          badgeVariant = "success";
          label = "IN (RECEIPT)";
        } else if (t === "out") {
          badgeVariant = "neutral";
          label = "OUT (DISPATCH)";
        } else if (t === "adjustment") {
          badgeVariant = "warning";
          label = "ADJUSTMENT";
        } else if (t === "return_in") {
          badgeVariant = "success";
          label = "RETURN IN";
        } else if (t === "return_out") {
          badgeVariant = "error";
          label = "RETURN OUT";
        }

        return <GlassBadge variant={badgeVariant}>{label}</GlassBadge>;
      },
    },
    {
      key: "quantity",
      header: "Quantity Delta",
      align: "right",
      sortable: true,
      render: (m) => {
        const isPositive = m.quantity > 0;
        return (
          <span
            className={`font-mono font-bold text-xs ${
              isPositive ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {isPositive ? `+${m.quantity.toFixed(2)}` : m.quantity.toFixed(2)}
          </span>
        );
      },
    },
    {
      key: "human_label",
      header: "Activity Context / Reference",
      render: (m) => (
        <div className="flex flex-col">
          <span className="font-medium text-xs text-[var(--text)]">{m.human_label}</span>
          {m.created_by && (
            <span className="text-[10px] text-[var(--text-muted)]">By: {m.created_by}</span>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--text)]">
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        {/* KPI Cards Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <History className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)] font-medium">Movement Records</p>
              <h3 className="text-2xl font-bold font-mono text-[var(--text)]">
                {metrics.totalMovements}
              </h3>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <ArrowDownLeft className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)] font-medium">Total Inbound Stock</p>
              <h3 className="text-2xl font-bold font-mono text-emerald-400">
                +{metrics.totalInbound.toLocaleString("en-IN")}
              </h3>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <ArrowUpRight className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)] font-medium">Total Dispatched Stock</p>
              <h3 className="text-2xl font-bold font-mono text-cyan-400">
                -{metrics.totalOutbound.toLocaleString("en-IN")}
              </h3>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <SlidersHorizontal className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)] font-medium">Net Adjustments Variance</p>
              <h3 className="text-2xl font-bold font-mono text-amber-400">
                {metrics.totalAdjustments >= 0
                  ? `+${metrics.totalAdjustments.toLocaleString("en-IN")}`
                  : metrics.totalAdjustments.toLocaleString("en-IN")}
              </h3>
            </div>
          </GlassCard>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap items-center gap-2">
          {[
            { id: "ALL", label: "All Movements", icon: <Layers className="w-3.5 h-3.5" /> },
            { id: "in", label: "Inbound Receipts", icon: <ArrowDownLeft className="w-3.5 h-3.5" /> },
            { id: "out", label: "Outbound Dispatches", icon: <ArrowUpRight className="w-3.5 h-3.5" /> },
            { id: "adjustment", label: "Adjustments", icon: <SlidersHorizontal className="w-3.5 h-3.5" /> },
            { id: "return_in", label: "Returns (RMA In)", icon: <RotateCcw className="w-3.5 h-3.5" /> },
            { id: "return_out", label: "Supplier Returns", icon: <RotateCw className="w-3.5 h-3.5" /> },
          ].map((tab) => {
            const isActive = typeFilter === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setTypeFilter(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? "bg-purple-600/30 text-purple-300 border border-purple-500/40 shadow-sm"
                    : "bg-[var(--surface)] text-[var(--text-muted)] hover:text-[var(--text)] border border-[var(--glass-border)]"
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Ledger ListView */}
        <ListViewTemplate
          title="Stock Movement Ledger"
          description="Complete append-only audit trail recording every inventory change, batch replenishment, sales fulfillment, return, and recount."
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          searchPlaceholder="Search ledger by product, SKU, warehouse, batch, or human activity note..."
          primaryAction={
            <Link href="/admin/stock/adjust">
              <GlassButton variant="primary" size="md">
                <PlusCircle className="w-4 h-4 mr-1.5" /> Record Stock Adjustment
              </GlassButton>
            </Link>
          }
        >
          <DataTable
            data={filteredMovements}
            columns={columns}
            keyExtractor={(m) => m.id}
            isLoading={loading}
            emptyTitle="No stock movement records found."
            emptyDescription="Inbound purchase receipts, sales dispatches, returns, and manual adjustments will appear here automatically."
          />
        </ListViewTemplate>
      </div>
    </div>
  );
}
