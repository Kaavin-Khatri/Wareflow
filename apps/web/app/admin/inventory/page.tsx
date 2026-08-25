"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { ListViewTemplate } from "@/components/templates/ListViewTemplate";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassModal } from "@/components/glass/GlassModal";
import { StatusBadge } from "@/components/StatusBadge";
import { apiClient } from "@/lib/api-client";
import {
  Boxes,
  Package,
  Warehouse as WarehouseIcon,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Clock,
  Calendar,
  Layers,
  FileSpreadsheet,
  ScanLine,
  Camera,
} from "lucide-react";
import Image from "next/image";
import { BarcodeScannerModal } from "@/components/barcode/BarcodeScannerModal";

export interface WarehouseSummary {
  id: string;
  name: string;
  location?: string | null;
  is_active: boolean;
}

export interface CategorySummary {
  id: string;
  name: string;
}

export interface WarehouseStockBreakdown {
  warehouse_id: string;
  warehouse_name: string;
  on_hand: number;
  batch_count: number;
}

export interface StockOverviewItem {
  product_id: string;
  sku: string;
  name: string;
  category_id?: string | null;
  category_name?: string | null;
  image_url?: string | null;
  base_uom_name: string;
  total_on_hand: number;
  preferred_uom_name?: string | null;
  preferred_uom_qty?: number | null;
  reorder_point: number;
  stock_status: "ok" | "low" | "critical";
  warehouses: WarehouseStockBreakdown[];
}

export interface StockOverviewResponse {
  items: StockOverviewItem[];
  total_products: number;
  ok_count: number;
  low_count: number;
  critical_count: number;
}

export interface StockBatchItem {
  id: string;
  product_id: string;
  warehouse_id: string;
  warehouse_name: string;
  batch_no: string;
  quantity: number;
  expiry_date?: string | null;
  received_at: string;
  days_until_expiry?: number | null;
  is_expired: boolean;
}

export interface ProductStockDetail {
  product_id: string;
  sku: string;
  name: string;
  base_uom_name: string;
  cost_price: number;
  wholesale_price: number;
  reorder_point: number;
  reorder_qty: number;
  total_on_hand: number;
  preferred_uom_name?: string | null;
  preferred_uom_qty?: number | null;
  stock_status: "ok" | "low" | "critical";
  warehouses: WarehouseStockBreakdown[];
  batches: StockBatchItem[];
}

export default function InventoryAdminPage() {
  const [stockOverview, setStockOverview] = useState<StockOverviewResponse>({
    items: [],
    total_products: 0,
    ok_count: 0,
    low_count: 0,
    critical_count: 0,
  });
  const [warehouses, setWarehouses] = useState<WarehouseSummary[]>([]);
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedWarehouse, setSelectedWarehouse] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedStatus, setSelectedStatus] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  // Batch Detail Modal State
  const [batchModalOpen, setBatchModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<StockOverviewItem | null>(null);
  const [productDetail, setProductDetail] = useState<ProductStockDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [scannerOpen, setScannerOpen] = useState(false);

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams();
        if (selectedWarehouse) params.append("warehouse_id", selectedWarehouse);
        if (selectedCategory) params.append("category_id", selectedCategory);
        if (selectedStatus) params.append("status", selectedStatus);
        if (searchQuery) params.append("search", searchQuery);

        const [overviewData, whData, catData] = await Promise.all([
          apiClient.get<StockOverviewResponse>(`/stock/overview?${params.toString()}`),
          apiClient.get<WarehouseSummary[]>("/stock/warehouses").catch(() => []),
          apiClient.get<CategorySummary[]>("/categories").catch(() => []),
        ]);

        if (!ignore) {
          setStockOverview(overviewData);
          setWarehouses(whData);
          setCategories(catData);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load inventory stock data.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadData();
    return () => {
      ignore = true;
    };
  }, [selectedWarehouse, selectedCategory, selectedStatus, searchQuery]);

  const handleOpenBatchModal = async (item: StockOverviewItem) => {
    setSelectedProduct(item);
    setBatchModalOpen(true);
    setLoadingDetail(true);
    try {
      const data = await apiClient.get<ProductStockDetail>(`/products/${item.product_id}/stock`);
      setProductDetail(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load product batches.");
    } finally {
      setLoadingDetail(false);
    }
  };

  const columns: DataTableColumn<StockOverviewItem>[] = [
    {
      key: "name",
      header: "Product / SKU",
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center overflow-hidden shrink-0">
            {item.image_url ? (
              <Image
                src={item.image_url}
                alt={item.name}
                width={40}
                height={40}
                className="w-full h-full object-cover"
                unoptimized
              />
            ) : (
              <Package className="w-5 h-5 text-white/40" />
            )}
          </div>
          <div>
            <div className="font-semibold text-white text-sm">{item.name}</div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-purple-400 font-mono tracking-wider">{item.sku}</span>
              {item.category_name && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-white/70">
                  {item.category_name}
                </span>
              )}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: "total_on_hand",
      header: "Total On Hand",
      sortable: true,
      render: (item) => (
        <div>
          <span className="font-mono font-bold text-white text-sm">
            {item.total_on_hand.toLocaleString()} {item.base_uom_name}
          </span>
          {item.preferred_uom_name && item.preferred_uom_qty !== null && (
            <span className="text-xs text-purple-300 block font-mono">
              ≈ {item.preferred_uom_qty} {item.preferred_uom_name}s
            </span>
          )}
        </div>
      ),
    },
    {
      key: "warehouses",
      header: "Warehouse Distribution",
      render: (item) => (
        <div className="flex flex-wrap gap-1.5 max-w-xs">
          {item.warehouses.length === 0 ? (
            <span className="text-xs text-white/40 italic">No active batches</span>
          ) : (
            item.warehouses.map((wh) => (
              <span
                key={wh.warehouse_id}
                className="text-[11px] px-2 py-0.5 rounded-lg bg-neutral-900/80 border border-white/10 text-white/90 flex items-center gap-1 font-mono"
              >
                <span className="text-purple-400 font-sans font-medium">{wh.warehouse_name}:</span>
                <span>{wh.on_hand}</span>
              </span>
            ))
          )}
        </div>
      ),
    },
    {
      key: "reorder_point",
      header: "Reorder Point",
      render: (item) => (
        <div className="text-xs font-mono text-white/70">
          <span>
            {item.reorder_point} {item.base_uom_name}
          </span>
        </div>
      ),
    },
    {
      key: "stock_status",
      header: "Stock Health",
      render: (item) => <StatusBadge status={item.stock_status} size="sm" />,
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (item) => (
        <GlassButton
          onClick={() => handleOpenBatchModal(item)}
          variant="secondary"
          size="sm"
          className="px-2.5 py-1 text-xs"
          title="View Batch Breakdown"
        >
          <Boxes className="w-3.5 h-3.5 mr-1" /> Batches
        </GlassButton>
      ),
    },
  ];

  const statsBarContent = (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <GlassCard className="p-3.5 flex items-center justify-between border-white/10">
        <div>
          <span className="text-[11px] font-semibold text-white/60 uppercase tracking-wider block">
            Stocked SKUs
          </span>
          <span className="text-xl font-bold text-white font-mono">
            {stockOverview.total_products}
          </span>
        </div>
        <div className="w-9 h-9 rounded-xl bg-purple-500/10 flex items-center justify-center">
          <Layers className="w-5 h-5 text-purple-400" />
        </div>
      </GlassCard>

      <GlassCard className="p-3.5 flex items-center justify-between border-emerald-500/20 bg-emerald-500/5">
        <div>
          <span className="text-[11px] font-semibold text-emerald-300/80 uppercase tracking-wider block">
            Healthy Stock
          </span>
          <span className="text-xl font-bold text-emerald-400 font-mono">
            {stockOverview.ok_count}
          </span>
        </div>
        <div className="w-9 h-9 rounded-xl bg-emerald-500/10 flex items-center justify-center">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
        </div>
      </GlassCard>

      <GlassCard className="p-3.5 flex items-center justify-between border-amber-500/20 bg-amber-500/5">
        <div>
          <span className="text-[11px] font-semibold text-amber-300/80 uppercase tracking-wider block">
            Low Stock Alerts
          </span>
          <span className="text-xl font-bold text-amber-400 font-mono">
            {stockOverview.low_count}
          </span>
        </div>
        <div className="w-9 h-9 rounded-xl bg-amber-500/10 flex items-center justify-center">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
        </div>
      </GlassCard>

      <GlassCard className="p-3.5 flex items-center justify-between border-rose-500/20 bg-rose-500/5">
        <div>
          <span className="text-[11px] font-semibold text-rose-300/80 uppercase tracking-wider block">
            Critical / Depleted
          </span>
          <span className="text-xl font-bold text-rose-400 font-mono">
            {stockOverview.critical_count}
          </span>
        </div>
        <div className="w-9 h-9 rounded-xl bg-rose-500/10 flex items-center justify-center">
          <AlertCircle className="w-5 h-5 text-rose-400" />
        </div>
      </GlassCard>
    </div>
  );

  return (
    <AppLayout>
      <ListViewTemplate
        title="Multi-Warehouse Inventory"
        description="Real-time batch-level stock visibility across storage hubs, expiry horizons, and reorder health."
        statsBar={statsBarContent}
        searchPlaceholder="Search product by name, SKU, or barcode..."
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        primaryAction={
          <div className="flex items-center gap-2">
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => setScannerOpen(true)}
              className="text-xs h-9 gap-1.5"
            >
              <ScanLine className="w-4 h-4 text-purple-400" />
              <span>Scan Barcode</span>
            </GlassButton>
            <GlassButton
              variant="outline"
              size="sm"
              onClick={async () => {
                try {
                  await apiClient.downloadBlob("/stock/overview.xlsx", "Stock_Overview.xlsx");
                } catch (err) {
                  console.error("Stock overview export failed:", err);
                }
              }}
              className="text-xs h-9 gap-1.5 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20"
              title="Export Stock Overview as Excel (.xlsx)"
            >
              <FileSpreadsheet className="w-4 h-4" /> Export Excel
            </GlassButton>
          </div>
        }
        filters={
          <div className="flex items-center gap-2 flex-wrap">
            {/* Warehouse Filter */}
            <select
              value={selectedWarehouse}
              onChange={(e) => setSelectedWarehouse(e.target.value)}
              className="px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-xs focus:outline-none focus:border-purple-500/50"
            >
              <option value="">All Warehouses</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-xs focus:outline-none focus:border-purple-500/50"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-xs focus:outline-none focus:border-purple-500/50"
            >
              <option value="">All Statuses</option>
              <option value="ok">Healthy</option>
              <option value="low">Low Stock</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        }
      >
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <DataTable
          columns={columns}
          data={stockOverview.items}
          keyExtractor={(item) => item.product_id}
          isLoading={loading}
          emptyTitle="No inventory records found"
          emptyDescription="Products and warehouse stock batches will appear here once received."
          emptyIcon={<Boxes className="w-12 h-12 text-purple-400/50" />}
        />
      </ListViewTemplate>

      {/* Batch Detail Modal */}
      <GlassModal
        isOpen={batchModalOpen}
        onClose={() => setBatchModalOpen(false)}
        title={`Batch Breakdown — ${selectedProduct?.name || "Product"}`}
        description={`SKU: ${selectedProduct?.sku} • Total Available: ${selectedProduct?.total_on_hand} ${selectedProduct?.base_uom_name}`}
        maxWidth="2xl"
      >
        <div className="space-y-4">
          {loadingDetail ? (
            <div className="py-8 text-center text-xs text-white/40">
              Loading active stock batches...
            </div>
          ) : !productDetail || productDetail.batches.length === 0 ? (
            <div className="py-8 text-center text-xs text-white/40 bg-white/5 rounded-2xl border border-white/5">
              No active stock batches found for this product.
            </div>
          ) : (
            <div className="space-y-3">
              <div className="overflow-x-auto rounded-xl border border-white/10">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-white/5 text-white/60 uppercase font-mono tracking-wider text-[10px] border-b border-white/10">
                    <tr>
                      <th className="p-3">Batch Number</th>
                      <th className="p-3">Warehouse</th>
                      <th className="p-3">Quantity</th>
                      <th className="p-3">Expiry Date</th>
                      <th className="p-3">Horizon</th>
                      <th className="p-3">Received At</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-white">
                    {productDetail.batches.map((batch) => {
                      const days = batch.days_until_expiry;
                      let horizonBadge = <span className="text-white/40 font-mono">—</span>;
                      if (batch.is_expired) {
                        horizonBadge = (
                          <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-mono text-[10px] font-bold">
                            EXPIRED
                          </span>
                        );
                      } else if (days !== null && days !== undefined) {
                        if (days <= 30) {
                          horizonBadge = (
                            <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold">
                              {days}d left
                            </span>
                          );
                        } else {
                          horizonBadge = (
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono text-[10px]">
                              {days}d left
                            </span>
                          );
                        }
                      }

                      return (
                        <tr key={batch.id} className="hover:bg-white/5 transition-colors">
                          <td className="p-3 font-mono font-bold text-purple-300">
                            {batch.batch_no}
                          </td>
                          <td className="p-3">
                            <span className="flex items-center gap-1.5">
                              <WarehouseIcon className="w-3.5 h-3.5 text-white/50" />
                              {batch.warehouse_name}
                            </span>
                          </td>
                          <td className="p-3 font-mono font-bold">
                            {batch.quantity} {productDetail.base_uom_name}
                          </td>
                          <td className="p-3 font-mono text-white/80">
                            {batch.expiry_date ? (
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3.5 h-3.5 text-white/40" />
                                {new Date(batch.expiry_date).toLocaleDateString()}
                              </span>
                            ) : (
                              <span className="text-white/40">No Expiry</span>
                            )}
                          </td>
                          <td className="p-3">{horizonBadge}</td>
                          <td className="p-3 text-white/50 font-mono text-[11px]">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(batch.received_at).toLocaleDateString()}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-end pt-2">
                <GlassButton
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setBatchModalOpen(false)}
                >
                  Close
                </GlassButton>
              </div>
            </div>
          )}
        </div>
      </GlassModal>

      {/* Inventory Barcode Scanner Modal */}
      {scannerOpen && (
        <BarcodeScannerModal
          isOpen={scannerOpen}
          onClose={() => setScannerOpen(false)}
          title="Scan Inventory Item"
          description="Point camera at product barcode or QR to filter stock overview instantly."
          onScanSuccess={(code) => {
            setSearchQuery(code);
          }}
        />
      )}
    </AppLayout>
  );
}
