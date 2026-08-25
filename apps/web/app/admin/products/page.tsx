"use client";

import { useEffect, useState, useRef } from "react";
import AppLayout from "@/components/AppLayout";
import { ListViewTemplate } from "@/components/templates/ListViewTemplate";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassInput } from "@/components/glass/GlassInput";
import { GlassModal } from "@/components/glass/GlassModal";
import { StatusBadge } from "@/components/StatusBadge";
import { apiClient } from "@/lib/api-client";
import {
  Plus,
  Edit2,
  Image as ImageIcon,
  PowerOff,
  Package,
  Upload,
  CheckCircle2,
  AlertCircle,
  Scale,
  Calculator,
  Trash2,
  ArrowRight,
  Bell,
  MessageSquare,
  Mail,
  Users,
  Barcode,
  ScanLine,
  Camera,
  FileSpreadsheet,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { BarcodeScannerModal, ScannedProduct } from "@/components/barcode/BarcodeScannerModal";
import { ProductLabelSheetModal } from "@/components/barcode/ProductLabelSheetModal";

export interface StockSubscriberItem {
  id: string;
  retailer_id: string;
  product_id: string;
  product_name?: string | null;
  retailer_name?: string | null;
  channel_preference: string;
  is_active: boolean;
  created_at: string;
  notified_at?: string | null;
}

export interface RetailerOptionItem {
  id: string;
  name: string;
  phone?: string | null;
  email?: string | null;
}

export interface CategorySummary {
  id: string;
  name: string;
}

export interface UOMItem {
  id: string;
  name: string;
  abbreviation: string;
}

export interface ProductConversionItem {
  id: string;
  product_id: string;
  from_uom_id: string;
  to_uom_id: string;
  factor: number;
  from_uom?: UOMItem | null;
  to_uom?: UOMItem | null;
}

export interface ProductItem {
  id: string;
  sku: string;
  name: string;
  description?: string | null;
  content_details?: string | null;
  image_url?: string | null;
  hsn_code?: string | null;
  category_id?: string | null;
  base_uom_id?: string | null;
  unit?: string | null;
  cost_price: number;
  wholesale_price: number;
  reorder_point: number;
  reorder_qty: number;
  barcode?: string | null;
  is_active: boolean;
  category?: CategorySummary | null;
  base_uom?: UOMItem | null;
}

export default function ProductsAdminPage() {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [uoms, setUoms] = useState<UOMItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Product Create/Edit Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<ProductItem | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form Fields
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [contentDetails, setContentDetails] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [baseUomId, setBaseUomId] = useState("");
  const [unit, setUnit] = useState("Bag");
  const [costPrice, setCostPrice] = useState<number | string>("");
  const [wholesalePrice, setWholesalePrice] = useState<number | string>("");
  const [reorderPoint, setReorderPoint] = useState<number | string>(10);
  const [reorderQty, setReorderQty] = useState<number | string>(50);
  const [barcode, setBarcode] = useState("");
  const [hsnCode, setHsnCode] = useState("");

  // Image Upload Modal State
  const [imageModalOpen, setImageModalOpen] = useState(false);
  const [selectedProductForImage, setSelectedProductForImage] = useState<ProductItem | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // UoM Conversions Modal State
  const [uomModalOpen, setUomModalOpen] = useState(false);
  const [selectedProductForUom, setSelectedProductForUom] = useState<ProductItem | null>(null);
  const [conversions, setConversions] = useState<ProductConversionItem[]>([]);
  const [loadingConversions, setLoadingConversions] = useState(false);
  const [convFromUomId, setConvFromUomId] = useState("");
  const [convToUomId, setConvToUomId] = useState("");
  const [convFactor, setConvFactor] = useState<number | string>("");
  const [convSubmitting, setConvSubmitting] = useState(false);
  const [convError, setConvError] = useState<string | null>(null);

  // Live Conversion Calculator State
  const [calcQty, setCalcQty] = useState<number | string>(1);
  const [calcFromUom, setCalcFromUom] = useState("");
  const [calcToUom, setCalcToUom] = useState("");
  const [calcResult, setCalcResult] = useState<number | null>(null);
  const [calcLoading, setCalcLoading] = useState(false);

  // Restock Notification Quick-Action Modal State (Step 13.4)
  const [notifyModalOpen, setNotifyModalOpen] = useState(false);
  const [selectedProductForNotify, setSelectedProductForNotify] = useState<ProductItem | null>(null);
  const [retailersList, setRetailersList] = useState<RetailerOptionItem[]>([]);
  const [subscribersList, setSubscribersList] = useState<StockSubscriberItem[]>([]);
  const [selectedRetailerId, setSelectedRetailerId] = useState("");
  const [selectedChannelPref, setSelectedChannelPref] = useState<"both" | "whatsapp" | "email">("both");
  const [notifySubmitting, setNotifySubmitting] = useState(false);
  const [loadingSubscribers, setLoadingSubscribers] = useState(false);
  const [notifyError, setNotifyError] = useState<string | null>(null);
  const [notifySuccess, setNotifySuccess] = useState<string | null>(null);

  // Barcode & Scanning States (Step 18.1)
  const [scannerOpen, setScannerOpen] = useState(false);
  const [barcodeModalProduct, setBarcodeModalProduct] = useState<ProductItem | null>(null);
  const [fieldScannerOpen, setFieldScannerOpen] = useState(false);

  const fetchCatalogData = async () => {
    try {
      const [productsData, categoriesData, uomsData] = await Promise.all([
        apiClient.get<ProductItem[]>("/products"),
        apiClient.get<CategorySummary[]>("/categories"),
        apiClient.get<UOMItem[]>("/uom").catch(() => []),
      ]);
      setProducts(productsData);
      setCategories(categoriesData);
      setUoms(uomsData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load product catalog.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      try {
        const [productsData, categoriesData, uomsData] = await Promise.all([
          apiClient.get<ProductItem[]>("/products"),
          apiClient.get<CategorySummary[]>("/categories"),
          apiClient.get<UOMItem[]>("/uom").catch(() => []),
        ]);
        if (!ignore) {
          setProducts(productsData);
          setCategories(categoriesData);
          setUoms(uomsData);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load product catalog.");
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
  }, []);

  const handleOpenCreate = () => {
    setEditingProduct(null);
    setSku("");
    setName("");
    setDescription("");
    setContentDetails("");
    setCategoryId(categories.length > 0 ? categories[0].id : "");
    setBaseUomId(uoms.length > 0 ? uoms[0].id : "");
    setUnit("Bag");
    setCostPrice("");
    setWholesalePrice("");
    setReorderPoint(10);
    setReorderQty(50);
    setBarcode("");
    setHsnCode("");
    setModalOpen(true);
  };

  const handleOpenEdit = (prod: ProductItem) => {
    setEditingProduct(prod);
    setSku(prod.sku);
    setName(prod.name);
    setDescription(prod.description || "");
    setContentDetails(prod.content_details || "");
    setCategoryId(prod.category_id || "");
    setBaseUomId(prod.base_uom_id || (uoms.length > 0 ? uoms[0].id : ""));
    setUnit(prod.unit || "Bag");
    setCostPrice(prod.cost_price);
    setWholesalePrice(prod.wholesale_price);
    setReorderPoint(prod.reorder_point);
    setReorderQty(prod.reorder_qty);
    setBarcode(prod.barcode || "");
    setHsnCode(prod.hsn_code || "");
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    const payload = {
      sku: sku.trim().toUpperCase(),
      name: name.trim(),
      description: description.trim() || null,
      content_details: contentDetails.trim() || null,
      category_id: categoryId || null,
      base_uom_id: baseUomId || null,
      unit: unit.trim() || null,
      cost_price: Number(costPrice) || 0,
      wholesale_price: Number(wholesalePrice) || 0,
      reorder_point: Number(reorderPoint) || 0,
      reorder_qty: Number(reorderQty) || 1,
      barcode: barcode.trim() || null,
      hsn_code: hsnCode.trim() || null,
    };

    try {
      if (editingProduct) {
        await apiClient.patch(`/products/${editingProduct.id}`, payload);
        setSuccess(`Product "${name}" updated successfully.`);
      } else {
        await apiClient.post("/products", payload);
        setSuccess(`Product "${name}" (${sku}) created successfully.`);
      }
      setModalOpen(false);
      await fetchCatalogData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save product.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenImageUpload = (prod: ProductItem) => {
    setSelectedProductForImage(prod);
    setImageFile(null);
    setImagePreview(prod.image_url || null);
    setImageError(null);
    setImageModalOpen(true);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setImageError("Invalid file type. Allowed formats: JPEG, PNG, WebP.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setImageError("File size exceeds 5MB limit.");
      return;
    }

    setImageError(null);
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const handleUploadImage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductForImage || !imageFile) return;

    setUploadingImage(true);
    setImageError(null);

    const formData = new FormData();
    formData.append("file", imageFile);

    try {
      await apiClient.upload<{ product_id: string; image_url: string }>(
        `/products/${selectedProductForImage.id}/image`,
        formData,
      );
      setSuccess(`Image updated for "${selectedProductForImage.name}".`);
      setImageModalOpen(false);
      await fetchCatalogData();
    } catch (err: unknown) {
      setImageError(err instanceof Error ? err.message : "Failed to upload image.");
    } finally {
      setUploadingImage(false);
    }
  };

  const handleDeactivate = async (prod: ProductItem) => {
    if (!confirm(`Are you sure you want to deactivate "${prod.name}"?`)) return;

    try {
      await apiClient.post(`/products/${prod.id}/deactivate`);
      setSuccess(`Product "${prod.name}" deactivated.`);
      await fetchCatalogData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to deactivate product.");
    }
  };

  // UoM Conversion Operations
  const fetchConversions = async (productId: string) => {
    setLoadingConversions(true);
    setConvError(null);
    try {
      const data = await apiClient.get<ProductConversionItem[]>(
        `/products/${productId}/conversions`,
      );
      setConversions(data);
    } catch (err: unknown) {
      setConvError(err instanceof Error ? err.message : "Failed to load conversion rules.");
    } finally {
      setLoadingConversions(false);
    }
  };

  const handleOpenUomModal = async (prod: ProductItem) => {
    setSelectedProductForUom(prod);
    setConvError(null);
    setCalcResult(null);
    setUomModalOpen(true);

    if (uoms.length >= 2) {
      setConvFromUomId(uoms[1].id);
      setConvToUomId(prod.base_uom_id || uoms[0].id);
      setCalcFromUom(uoms[1].id);
      setCalcToUom(prod.base_uom_id || uoms[0].id);
    }
    setConvFactor(24);
    await fetchConversions(prod.id);
  };

  const handleAddConversion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductForUom) return;

    setConvSubmitting(true);
    setConvError(null);

    try {
      await apiClient.post(`/products/${selectedProductForUom.id}/conversions`, {
        from_uom_id: convFromUomId,
        to_uom_id: convToUomId,
        factor: Number(convFactor),
      });
      await fetchConversions(selectedProductForUom.id);
      setSuccess("UoM conversion ratio saved.");
    } catch (err: unknown) {
      setConvError(err instanceof Error ? err.message : "Failed to save conversion.");
    } finally {
      setConvSubmitting(false);
    }
  };

  const handleDeleteConversion = async (conversionId: string) => {
    if (!selectedProductForUom) return;
    try {
      await apiClient.delete(`/products/${selectedProductForUom.id}/conversions/${conversionId}`);
      await fetchConversions(selectedProductForUom.id);
    } catch (err: unknown) {
      setConvError(err instanceof Error ? err.message : "Failed to delete conversion.");
    }
  };

  const handleCalculateConversion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductForUom || !calcFromUom || !calcToUom) return;

    setCalcLoading(true);
    setConvError(null);

    try {
      const res = await apiClient.post<{ converted_qty: number }>(
        `/products/${selectedProductForUom.id}/convert`,
        {
          qty: Number(calcQty) || 0,
          from_uom_id: calcFromUom,
          to_uom_id: calcToUom,
        },
      );
      setCalcResult(res.converted_qty);
    } catch (err: unknown) {
      setConvError(err instanceof Error ? err.message : "Conversion calculation failed.");
      setCalcResult(null);
    } finally {
      setCalcLoading(false);
    }
  };

  const handleOpenNotifyModal = async (prod: ProductItem) => {
    setSelectedProductForNotify(prod);
    setNotifyError(null);
    setNotifySuccess(null);
    setNotifyModalOpen(true);
    setLoadingSubscribers(true);

    try {
      const [subsData, retsData] = await Promise.all([
        apiClient.get<StockSubscriberItem[]>(`/products/${prod.id}/subscribers`),
        retailersList.length === 0
          ? apiClient.get<RetailerOptionItem[]>("/retailers")
          : Promise.resolve(retailersList),
      ]);
      setSubscribersList(subsData);
      if (retailersList.length === 0) {
        setRetailersList(retsData);
        if (retsData.length > 0) {
          setSelectedRetailerId(retsData[0].id);
        }
      } else if (!selectedRetailerId && retailersList.length > 0) {
        setSelectedRetailerId(retailersList[0].id);
      }
    } catch (err: unknown) {
      setNotifyError(err instanceof Error ? err.message : "Failed to load subscribers.");
    } finally {
      setLoadingSubscribers(false);
    }
  };

  const handleSubscribeRetailer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductForNotify || !selectedRetailerId) return;

    setNotifySubmitting(true);
    setNotifyError(null);
    setNotifySuccess(null);

    try {
      await apiClient.post<StockSubscriberItem>(
        `/products/${selectedProductForNotify.id}/subscribe`,
        {
          retailer_id: selectedRetailerId,
          channel_preference: selectedChannelPref,
        }
      );
      setNotifySuccess(`Subscribed retailer for restock alerts via ${selectedChannelPref}.`);
      const subs = await apiClient.get<StockSubscriberItem[]>(
        `/products/${selectedProductForNotify.id}/subscribers`
      );
      setSubscribersList(subs);
    } catch (err: unknown) {
      setNotifyError(err instanceof Error ? err.message : "Failed to subscribe retailer.");
    } finally {
      setNotifySubmitting(false);
    }
  };

  const handleUnsubscribeRetailer = async (retailerId: string) => {
    if (!selectedProductForNotify) return;
    try {
      await apiClient.delete(
        `/products/${selectedProductForNotify.id}/subscribe?retailer_id=${retailerId}`
      );
      setSubscribersList((prev) => prev.filter((s) => s.retailer_id !== retailerId));
      setNotifySuccess("Unsubscribed retailer from restock notifications.");
    } catch (err: unknown) {
      setNotifyError(err instanceof Error ? err.message : "Failed to unsubscribe.");
    }
  };

  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      searchQuery === "" ||
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.barcode && p.barcode.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesCat = selectedCategory === "" || p.category_id === selectedCategory;
    return matchesSearch && matchesCat;
  });

  const columns: DataTableColumn<ProductItem>[] = [
    {
      key: "name",
      header: "Product / SKU",
      render: (p) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center overflow-hidden shrink-0">
            {p.image_url ? (
              <Image
                src={p.image_url}
                alt={p.name}
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
            <div className="font-semibold text-white text-sm">{p.name}</div>
            <div className="text-xs text-purple-400 font-mono tracking-wider">{p.sku}</div>
          </div>
        </div>
      ),
    },
    {
      key: "category",
      header: "Category",
      render: (p) => (
        <span className="text-xs px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-white/80">
          {p.category?.name || "Uncategorized"}
        </span>
      ),
    },
    {
      key: "wholesale_price",
      header: "Wholesale Price",
      sortable: true,
      render: (p) => (
        <div>
          <span className="font-mono font-medium text-white">
            ₹{Number(p.wholesale_price).toFixed(2)}
          </span>
          <span className="text-[11px] text-white/50 block">
            Cost: ₹{Number(p.cost_price).toFixed(2)}
          </span>
        </div>
      ),
    },
    {
      key: "base_uom",
      header: "Base Unit",
      render: (p) => (
        <span className="text-xs font-mono text-purple-300">
          {p.base_uom?.name || p.unit || "Piece"}
        </span>
      ),
    },
    {
      key: "hsn_code",
      header: "HSN / GST",
      render: (p) =>
        p.hsn_code && p.hsn_code.trim() !== "" && p.hsn_code !== "N/A" ? (
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            {p.hsn_code}
          </span>
        ) : (
          <span
            className="text-[11px] font-medium text-amber-300 bg-amber-500/15 px-2 py-0.5 rounded border border-amber-500/30 flex items-center gap-1 inline-flex"
            title="Required for GST tax invoicing"
          >
            <AlertCircle className="w-3 h-3 text-amber-400" />
            HSN Missing
          </span>
        ),
    },
    {
      key: "is_active",
      header: "Status",
      render: (p) => <StatusBadge status={p.is_active ? "active" : "suspended"} size="sm" />,
    },

    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (p) => (
        <div className="flex items-center justify-end gap-1.5">
          <GlassButton
            onClick={() => setBarcodeModalProduct(p)}
            variant="secondary"
            size="sm"
            className="px-2 py-1 text-xs text-purple-300 hover:text-purple-200"
            title="Barcode & Printable Label Sheets"
          >
            <Barcode className="w-3.5 h-3.5 mr-1" /> Label
          </GlassButton>
          <GlassButton
            onClick={() => handleOpenNotifyModal(p)}
            variant="secondary"
            size="sm"
            className="px-2 py-1 text-xs text-amber-300 hover:text-amber-200"
            title="Notify Retailer When Available"
          >
            <Bell className="w-3.5 h-3.5 mr-1" /> Alert
          </GlassButton>
          <GlassButton
            onClick={() => handleOpenUomModal(p)}
            variant="secondary"
            size="sm"
            className="px-2 py-1 text-xs"
            title="Packaging & UoM Conversions"
          >
            <Scale className="w-3.5 h-3.5 mr-1" /> UoM
          </GlassButton>
          <GlassButton
            onClick={() => handleOpenImageUpload(p)}
            variant="secondary"
            size="sm"
            className="px-2 py-1 text-xs"
            title="Upload Product Image"
          >
            <ImageIcon className="w-3.5 h-3.5" />
          </GlassButton>
          <GlassButton
            onClick={() => handleOpenEdit(p)}
            variant="secondary"
            size="sm"
            className="px-2 py-1 text-xs"
            title="Edit Details"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </GlassButton>
          {p.is_active && (
            <GlassButton
              onClick={() => handleDeactivate(p)}
              variant="destructive"
              size="sm"
              className="px-2 py-1 text-xs"
              title="Deactivate Product"
            >
              <PowerOff className="w-3.5 h-3.5" />
            </GlassButton>
          )}
        </div>
      ),
    },
  ];

  return (
    <AppLayout>
      <ListViewTemplate
        title="Product Catalog"
        description="Manage master SKU specifications, packaging ratios, and wholesale pricing."
        primaryAction={
          <div className="flex items-center gap-2 flex-wrap">
            <Link href="/admin/products/import">
              <GlassButton
                variant="secondary"
                className="flex items-center gap-1.5 text-xs font-semibold"
                title="Bulk CSV Import / Export"
              >
                <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                <span>Import / Export CSV</span>
              </GlassButton>
            </Link>
            <GlassButton
              onClick={() => setScannerOpen(true)}
              variant="secondary"
              className="flex items-center gap-1.5"
            >
              <ScanLine className="w-4 h-4 text-[var(--accent)]" />
              <span>Scan Barcode</span>
            </GlassButton>
            <GlassButton onClick={handleOpenCreate} variant="primary">
              <Plus className="w-4 h-4 mr-1.5" /> Add Product
            </GlassButton>
          </div>
        }
        searchPlaceholder="Search by name, SKU, or barcode..."
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        filters={
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
        }
      >
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        <DataTable
          columns={columns}
          data={filteredProducts}
          keyExtractor={(item) => item.id}
          isLoading={loading}
          emptyTitle="No products found"
          emptyDescription="Add wholesale inventory products to build your active stock catalog."
          emptyIcon={<Package className="w-12 h-12 text-purple-400/50" />}
          emptyAction={
            <GlassButton onClick={handleOpenCreate} variant="primary">
              <Plus className="w-4 h-4 mr-1.5 inline" /> Create Product
            </GlassButton>
          }
        />
      </ListViewTemplate>

      {/* Product Create/Edit Modal */}
      <GlassModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingProduct ? "Edit Product" : "Create New Product"}
        description="Specify SKU, wholesale pricing, category, and inventory parameters."
        maxWidth="xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                SKU Code
              </label>
              <GlassInput
                placeholder="e.g. RICE-ROYAL-25KG"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                Product Name
              </label>
              <GlassInput
                placeholder="e.g. Royal Basmati Rice 25kg"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                Category
              </label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-purple-500/50"
              >
                <option value="">Select Category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                Base Unit of Measure
              </label>
              <select
                value={baseUomId}
                onChange={(e) => setBaseUomId(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-purple-500/50"
              >
                <option value="">Select Base UoM</option>
                {uoms.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name} ({u.abbreviation})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                Unit Label
              </label>
              <GlassInput
                placeholder="e.g. Bag, Box, Kg"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                Wholesale Price (₹)
              </label>
              <GlassInput
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={wholesalePrice}
                onChange={(e) => setWholesalePrice(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                Cost / Procurement Price (₹)
              </label>
              <GlassInput
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={costPrice}
                onChange={(e) => setCostPrice(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                Reorder Threshold Point
              </label>
              <GlassInput
                type="number"
                min="0"
                value={reorderPoint}
                onChange={(e) => setReorderPoint(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                Default Reorder Batch Quantity
              </label>
              <GlassInput
                type="number"
                min="1"
                value={reorderQty}
                onChange={(e) => setReorderQty(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                HSN Code (GST)
              </label>
              <GlassInput
                placeholder="e.g. 10063020"
                value={hsnCode}
                onChange={(e) => setHsnCode(e.target.value)}
              />
              {(!hsnCode || hsnCode.trim() === "") && (
                <p className="text-[11px] text-amber-400 mt-1 flex items-center gap-1 font-mono">
                  <AlertCircle className="w-3 h-3 shrink-0" />
                  Mandatory for generating GST tax invoices.
                </p>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-white/70 uppercase tracking-wider">
                  Barcode / EAN-13
                </label>
                <button
                  type="button"
                  onClick={() => setFieldScannerOpen(true)}
                  className="text-[11px] text-[var(--accent)] hover:underline flex items-center gap-1 font-medium"
                >
                  <Camera className="w-3 h-3" />
                  <span>Scan via Camera</span>
                </button>
              </div>
              <GlassInput
                placeholder="e.g. 8901234567890"
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
              />
              <p className="text-[11px] text-[var(--text-muted)] mt-1 font-mono">
                Leave empty to auto-generate an EAN-13 warehouse barcode.
              </p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
              Description
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Wholesale packaging specs, brand details, storage conditions..."
              className="w-full px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-purple-500/50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
              Content & Nutritional Details
            </label>
            <textarea
              rows={2}
              value={contentDetails}
              onChange={(e) => setContentDetails(e.target.value)}
              placeholder="Ingredients, allergen notices, grain length, nutritional facts..."
              className="w-full px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-purple-500/50"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <GlassButton type="button" variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </GlassButton>
            <GlassButton type="submit" variant="primary" disabled={submitting}>
              {submitting ? "Saving..." : editingProduct ? "Update Product" : "Create Product"}
            </GlassButton>
          </div>
        </form>
      </GlassModal>

      {/* Packaging & UoM Conversions Modal */}
      <GlassModal
        isOpen={uomModalOpen}
        onClose={() => setUomModalOpen(false)}
        title={`UoM Conversions — ${selectedProductForUom?.name || "Product"}`}
        description="Configure packaging conversions (e.g. 1 Case = 24 Pieces). Stock ledger balances are strictly tracked in Base UoM."
        maxWidth="2xl"
      >
        <div className="space-y-6">
          {convError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{convError}</span>
            </div>
          )}

          {/* Current Base UoM Indicator */}
          <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-between text-xs">
            <div>
              <span className="text-purple-300 font-semibold uppercase tracking-wider block">
                Single Point of Truth (Base Unit)
              </span>
              <span className="text-white/80">
                All warehouse batches and stock ledger movements are stored in this base unit.
              </span>
            </div>
            <span className="px-3 py-1.5 rounded-lg bg-purple-500/20 text-purple-200 font-mono font-bold text-sm">
              {selectedProductForUom?.base_uom?.name || selectedProductForUom?.unit || "Piece"}
            </span>
          </div>

          {/* Existing Conversions List */}
          <div>
            <h4 className="text-xs font-semibold text-white/70 mb-2 uppercase tracking-wider">
              Active Packaging Ratios
            </h4>
            {loadingConversions ? (
              <div className="py-4 text-center text-xs text-white/40">Loading conversions...</div>
            ) : conversions.length === 0 ? (
              <div className="py-4 text-center text-xs text-white/40 bg-white/5 rounded-xl border border-white/5">
                No custom packaging conversions defined. Product trades 1:1 in base unit.
              </div>
            ) : (
              <div className="space-y-2">
                {conversions.map((c) => (
                  <div
                    key={c.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10 text-xs"
                  >
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-white font-bold">1 {c.from_uom?.name || "Unit"}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-purple-400" />
                      <span className="text-purple-300 font-bold">
                        {c.factor} {c.to_uom?.name || "Base Units"}
                      </span>
                    </div>
                    <GlassButton
                      onClick={() => handleDeleteConversion(c.id)}
                      variant="destructive"
                      size="sm"
                      className="px-2 py-1 text-xs"
                    >
                      <Trash2 className="w-3 h-3" />
                    </GlassButton>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add New Conversion Form */}
          <form
            onSubmit={handleAddConversion}
            className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3"
          >
            <h4 className="text-xs font-semibold text-white/80 uppercase tracking-wider">
              Add Packaging Conversion
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] text-white/60 mb-1">
                  Source Unit (1 unit of)
                </label>
                <select
                  value={convFromUomId}
                  onChange={(e) => setConvFromUomId(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-xs focus:outline-none focus:border-purple-500/50"
                  required
                >
                  <option value="">Select From UoM</option>
                  {uoms.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name} ({u.abbreviation})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] text-white/60 mb-1">Target Unit</label>
                <select
                  value={convToUomId}
                  onChange={(e) => setConvToUomId(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-xs focus:outline-none focus:border-purple-500/50"
                  required
                >
                  <option value="">Select To UoM</option>
                  {uoms.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name} ({u.abbreviation})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] text-white/60 mb-1">Conversion Factor</label>
                <GlassInput
                  type="number"
                  min="0.0001"
                  step="any"
                  placeholder="e.g. 24"
                  value={convFactor}
                  onChange={(e) => setConvFactor(e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <GlassButton type="submit" variant="primary" size="sm" disabled={convSubmitting}>
                {convSubmitting ? "Saving..." : "Save Ratio"}
              </GlassButton>
            </div>
          </form>

          {/* Interactive Live Conversion Calculator */}
          <form
            onSubmit={handleCalculateConversion}
            className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/20 space-y-3"
          >
            <div className="flex items-center gap-2">
              <Calculator className="w-4 h-4 text-purple-400" />
              <h4 className="text-xs font-semibold text-purple-200 uppercase tracking-wider">
                Live Conversion Calculator Preview
              </h4>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] text-white/60 mb-1">Quantity</label>
                <GlassInput
                  type="number"
                  step="any"
                  value={calcQty}
                  onChange={(e) => setCalcQty(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-[11px] text-white/60 mb-1">From</label>
                <select
                  value={calcFromUom}
                  onChange={(e) => setCalcFromUom(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-xs focus:outline-none focus:border-purple-500/50"
                  required
                >
                  <option value="">Select From UoM</option>
                  {uoms.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name} ({u.abbreviation})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] text-white/60 mb-1">To</label>
                <select
                  value={calcToUom}
                  onChange={(e) => setCalcToUom(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-xs focus:outline-none focus:border-purple-500/50"
                  required
                >
                  <option value="">Select To UoM</option>
                  {uoms.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name} ({u.abbreviation})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex items-center justify-between pt-2">
              <div className="text-xs font-mono">
                {calcResult !== null && (
                  <span className="text-emerald-400 font-bold">
                    Result: {calcQty} {uoms.find((u) => u.id === calcFromUom)?.name} = {calcResult}{" "}
                    {uoms.find((u) => u.id === calcToUom)?.name}
                  </span>
                )}
              </div>
              <GlassButton type="submit" variant="secondary" size="sm" disabled={calcLoading}>
                {calcLoading ? "Calculating..." : "Calculate"}
              </GlassButton>
            </div>
          </form>
        </div>
      </GlassModal>

      {/* Image Upload Modal */}
      <GlassModal
        isOpen={imageModalOpen}
        onClose={() => setImageModalOpen(false)}
        title={`Upload Image — ${selectedProductForImage?.name || "Product"}`}
        description="Upload a high-resolution product catalog photo (JPEG, PNG, WebP up to 5MB)."
      >
        <form onSubmit={handleUploadImage} className="space-y-4">
          {imageError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{imageError}</span>
            </div>
          )}

          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-white/20 hover:border-purple-500/50 transition-colors rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer bg-white/5 group"
          >
            {imagePreview ? (
              <div className="relative w-48 h-48 rounded-xl overflow-hidden mb-3 border border-white/10">
                <Image
                  src={imagePreview}
                  alt="Preview"
                  width={192}
                  height={192}
                  className="w-full h-full object-cover"
                  unoptimized
                />
              </div>
            ) : (
              <div className="w-16 h-16 rounded-full bg-purple-500/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Upload className="w-8 h-8 text-purple-400" />
              </div>
            )}
            <p className="text-xs text-white font-medium mb-1">
              {imageFile ? imageFile.name : "Click to browse or drop an image here"}
            </p>
            <p className="text-[11px] text-white/40">JPEG, PNG, or WebP (max. 5MB)</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <GlassButton type="button" variant="secondary" onClick={() => setImageModalOpen(false)}>
              Cancel
            </GlassButton>
            <GlassButton type="submit" variant="primary" disabled={!imageFile || uploadingImage}>
              {uploadingImage ? "Uploading..." : "Save Image"}
            </GlassButton>
          </div>
        </form>
      </GlassModal>

      {/* Restock Notification Quick-Action Modal (Step 13.4) */}
      <GlassModal
        isOpen={notifyModalOpen}
        onClose={() => setNotifyModalOpen(false)}
        title={`Restock Alert — ${selectedProductForNotify?.name || "Product"}`}
        description="Notify wholesale retailers immediately via WhatsApp/Email when this product is replenished."
      >
        <div className="space-y-5">
          {notifySuccess && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{notifySuccess}</span>
            </div>
          )}

          {notifyError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{notifyError}</span>
            </div>
          )}

          {/* Product Snapshot Card */}
          {selectedProductForNotify && (
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                  <Package className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-medium text-white">{selectedProductForNotify.name}</div>
                  <div className="text-xs text-purple-400 font-mono">{selectedProductForNotify.sku}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-white/60">Wholesale Price</div>
                <div className="text-sm font-mono font-semibold text-white">
                  ₹{Number(selectedProductForNotify.wholesale_price).toFixed(2)}
                </div>
              </div>
            </div>
          )}

          {/* Phone Call Quick Subscription Form */}
          <form onSubmit={handleSubscribeRetailer} className="p-4 rounded-xl bg-white/[0.03] border border-white/10 space-y-4">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-purple-300">
              <Plus className="w-3.5 h-3.5" />
              <span>Add Standing Restock Alert</span>
            </div>

            <div>
              <label className="block text-xs font-medium text-white/70 mb-1.5">Select Wholesale Retailer</label>
              <select
                value={selectedRetailerId}
                onChange={(e) => setSelectedRetailerId(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500/50"
                required
              >
                <option value="" disabled className="bg-slate-900 text-white">
                  Select a registered retailer...
                </option>
                {retailersList.map((r) => (
                  <option key={r.id} value={r.id} className="bg-slate-900 text-white">
                    {r.name} {r.phone ? `(${r.phone})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-white/70 mb-1.5">Notification Channel</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedChannelPref("whatsapp")}
                  className={`px-3 py-2 rounded-xl text-xs font-medium border flex items-center justify-center gap-1.5 transition-all ${
                    selectedChannelPref === "whatsapp"
                      ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300 shadow-sm"
                      : "bg-white/5 border-white/10 text-white/60 hover:text-white"
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" /> WhatsApp
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedChannelPref("email")}
                  className={`px-3 py-2 rounded-xl text-xs font-medium border flex items-center justify-center gap-1.5 transition-all ${
                    selectedChannelPref === "email"
                      ? "bg-blue-500/20 border-blue-500/40 text-blue-300 shadow-sm"
                      : "bg-white/5 border-white/10 text-white/60 hover:text-white"
                  }`}
                >
                  <Mail className="w-3.5 h-3.5" /> Email
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedChannelPref("both")}
                  className={`px-3 py-2 rounded-xl text-xs font-medium border flex items-center justify-center gap-1.5 transition-all ${
                    selectedChannelPref === "both"
                      ? "bg-purple-500/20 border-purple-500/40 text-purple-300 shadow-sm"
                      : "bg-white/5 border-white/10 text-white/60 hover:text-white"
                  }`}
                >
                  <Bell className="w-3.5 h-3.5" /> Both
                </button>
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <GlassButton
                type="submit"
                variant="primary"
                size="sm"
                disabled={!selectedRetailerId || notifySubmitting}
                className="w-full sm:w-auto"
              >
                {notifySubmitting ? "Subscribing..." : "Add Restock Alert"}
              </GlassButton>
            </div>
          </form>

          {/* Current Active Subscribers List */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between text-xs font-semibold text-white/80">
              <span className="flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-purple-400" />
                Active Standing Subscriptions ({subscribersList.length})
              </span>
            </div>

            {loadingSubscribers ? (
              <div className="text-center py-6 text-xs text-white/40">Loading subscribers...</div>
            ) : subscribersList.length === 0 ? (
              <div className="text-center py-6 text-xs text-white/40 rounded-xl bg-white/[0.02] border border-white/5">
                No active restock subscriptions for this product.
              </div>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {subscribersList.map((sub) => (
                  <div
                    key={sub.id}
                    className="p-2.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-medium text-white">{sub.retailer_name || "Wholesale Retailer"}</div>
                      <div className="text-[11px] text-white/40 flex items-center gap-2 mt-0.5">
                        <span className="capitalize text-purple-300 font-mono">{sub.channel_preference}</span>
                        <span>•</span>
                        <span>{new Date(sub.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <GlassButton
                      onClick={() => handleUnsubscribeRetailer(sub.retailer_id)}
                      variant="destructive"
                      size="sm"
                      className="px-2 py-1 text-xs"
                      title="Unsubscribe Retailer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </GlassButton>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </GlassModal>

      {/* General Catalog Barcode Scanner Modal */}
      {scannerOpen && (
        <BarcodeScannerModal
          isOpen={scannerOpen}
          onClose={() => setScannerOpen(false)}
          title="Catalog Scanner"
          description="Scan a product barcode or QR code to find and filter the product."
          onScanSuccess={(code, prod) => {
            setSearchQuery(code);
            if (prod) {
              setSuccess(`Found product "${prod.name}" (${prod.sku})`);
            }
          }}
        />
      )}

      {/* Field Input Camera Scanner Modal */}
      {fieldScannerOpen && (
        <BarcodeScannerModal
          isOpen={fieldScannerOpen}
          onClose={() => setFieldScannerOpen(false)}
          title="Scan Barcode into Form"
          description="Point camera at product barcode sticker to fill this field."
          autoLookupProduct={false}
          onScanSuccess={(code) => {
            setBarcode(code);
            setSuccess(`Scanned barcode: ${code}`);
          }}
        />
      )}

      {/* Product Label Sheet Printing Modal */}
      {barcodeModalProduct && (
        <ProductLabelSheetModal
          isOpen={Boolean(barcodeModalProduct)}
          onClose={() => setBarcodeModalProduct(null)}
          product={barcodeModalProduct}
        />
      )}
    </AppLayout>
  );
}
