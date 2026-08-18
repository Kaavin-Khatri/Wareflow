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
} from "lucide-react";
import Image from "next/image";

export interface CategorySummary {
  id: string;
  name: string;
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
  unit?: string | null;
  cost_price: number;
  wholesale_price: number;
  reorder_point: number;
  reorder_qty: number;
  barcode?: string | null;
  is_active: boolean;
  category?: CategorySummary | null;
}

export default function ProductsAdminPage() {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [categories, setCategories] = useState<CategorySummary[]>([]);
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

  const fetchCatalogData = async () => {
    try {
      const [productsData, categoriesData] = await Promise.all([
        apiClient.get<ProductItem[]>("/products"),
        apiClient.get<CategorySummary[]>("/categories"),
      ]);
      setProducts(productsData);
      setCategories(categoriesData);
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
        const [productsData, categoriesData] = await Promise.all([
          apiClient.get<ProductItem[]>("/products"),
          apiClient.get<CategorySummary[]>("/categories"),
        ]);
        if (!ignore) {
          setProducts(productsData);
          setCategories(categoriesData);
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

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setImageError(null);
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate type
    const validTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!validTypes.includes(file.type.toLowerCase())) {
      setImageError("Invalid file type. Only JPEG, PNG, and WebP images are supported.");
      return;
    }

    // Validate size (<= 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setImageError("File size exceeds 5MB limit.");
      return;
    }

    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const handleUploadImageSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductForImage || !imageFile) return;

    setUploadingImage(true);
    setImageError(null);

    const formData = new FormData();
    formData.append("file", imageFile);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/products/${selectedProductForImage.id}/image`,
        {
          method: "POST",
          body: formData,
        },
      );

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Image upload failed.");
      }

      setSuccess(`Image updated for product ${selectedProductForImage.sku}.`);
      setImageModalOpen(false);
      await fetchCatalogData();
    } catch (err: unknown) {
      setImageError(err instanceof Error ? err.message : "Failed to upload image.");
    } finally {
      setUploadingImage(false);
    }
  };

  const handleDeactivate = async (prod: ProductItem) => {
    if (!confirm(`Are you sure you want to deactivate SKU "${prod.sku}" (${prod.name})?`)) return;

    setError(null);
    setSuccess(null);
    try {
      await apiClient.post(`/products/${prod.id}/deactivate`);
      setSuccess(`Product "${prod.sku}" has been deactivated.`);
      await fetchCatalogData();
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to deactivate product. Check if open orders exist.",
      );
    }
  };

  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      searchQuery === "" ||
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.barcode && p.barcode.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesCategory = selectedCategory === "" || p.category_id === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  const columns: DataTableColumn<ProductItem>[] = [
    {
      key: "product",
      header: "Product / SKU",
      mobilePrimary: true,
      sortable: true,
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center overflow-hidden shrink-0">
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
              <Package className="w-5 h-5 text-purple-400/60" />
            )}
          </div>
          <div>
            <div className="font-semibold text-white text-sm">{item.name}</div>
            <div className="text-xs font-mono text-purple-300">{item.sku}</div>
          </div>
        </div>
      ),
    },
    {
      key: "category",
      header: "Category",
      sortable: true,
      render: (item) => {
        const cat = categories.find((c) => c.id === item.category_id);
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-purple-500/10 border border-purple-500/20 text-purple-300">
            {cat?.name || "Uncategorized"}
          </span>
        );
      },
    },
    {
      key: "pricing",
      header: "Wholesale / Cost",
      sortable: true,
      render: (item) => (
        <div className="text-sm">
          <div className="font-semibold text-emerald-400">
            ₹{item.wholesale_price.toLocaleString("en-IN")}
          </div>
          <div className="text-xs text-white/50">
            Cost: ₹{item.cost_price.toLocaleString("en-IN")}
          </div>
        </div>
      ),
    },
    {
      key: "reorder",
      header: "Reorder Metrics",
      render: (item) => (
        <div className="text-xs text-white/70">
          <div>
            Min: <span className="font-mono text-white">{item.reorder_point}</span>{" "}
            {item.unit || "units"}
          </div>
          <div>
            Qty: <span className="font-mono text-white">{item.reorder_qty}</span>{" "}
            {item.unit || "units"}
          </div>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      render: (item) => <StatusBadge status={item.is_active ? "active" : "inactive"} />,
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (item) => (
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={() => handleOpenImageUpload(item)}
            className="p-1.5 rounded-lg text-white/60 hover:text-purple-300 hover:bg-purple-500/10 transition-colors"
            title="Upload Product Image"
            aria-label={`Upload image for ${item.name}`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => handleOpenEdit(item)}
            className="p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
            title="Edit Product Details"
            aria-label={`Edit ${item.name}`}
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          {item.is_active && (
            <button
              onClick={() => handleDeactivate(item)}
              className="p-1.5 rounded-lg text-amber-400/70 hover:text-amber-300 hover:bg-amber-500/10 transition-colors"
              title="Deactivate Product"
              aria-label={`Deactivate ${item.name}`}
            >
              <PowerOff className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <AppLayout>
      <ListViewTemplate
        title="Product Catalog"
        description="Manage wholesale items, SKU codes, pricing, specs, and storage assets."
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search by name, SKU, or barcode..."
        filters={
          <div className="flex items-center gap-3">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-xs focus:outline-none focus:border-purple-500/50"
            >
              <option value="">All Categories ({categories.length})</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        }
        primaryAction={
          <GlassButton onClick={handleOpenCreate} variant="primary">
            <Plus className="w-4 h-4 mr-1.5 inline" /> Add Product
          </GlassButton>
        }
      >
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center gap-2">
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

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                Unit / Packaging
              </label>
              <GlassInput
                placeholder="e.g. Bag, Box, Carton, Kg"
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
            </div>
            <div>
              <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
                Barcode / EAN
              </label>
              <GlassInput
                placeholder="e.g. 8901234567890"
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Detailed wholesale product description..."
              className="w-full px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-purple-500/50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-white/70 mb-1.5 uppercase tracking-wider">
              Content & Ingredients Details
            </label>
            <textarea
              value={contentDetails}
              onChange={(e) => setContentDetails(e.target.value)}
              rows={2}
              placeholder="100% Traditional aged long-grain basmati rice..."
              className="w-full px-3 py-2 bg-neutral-900/80 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-purple-500/50"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
            <GlassButton type="button" variant="ghost" onClick={() => setModalOpen(false)}>
              Cancel
            </GlassButton>
            <GlassButton type="submit" variant="primary" disabled={submitting}>
              {submitting ? "Saving..." : editingProduct ? "Update Product" : "Save Product"}
            </GlassButton>
          </div>
        </form>
      </GlassModal>

      {/* Image Upload Modal */}
      <GlassModal
        isOpen={imageModalOpen}
        onClose={() => setImageModalOpen(false)}
        title="Upload Product Image"
        description={`Upload photo for ${selectedProductForImage?.sku} (${selectedProductForImage?.name})`}
        maxWidth="md"
      >
        <form onSubmit={handleUploadImageSubmit} className="space-y-4">
          {imageError && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs">
              {imageError}
            </div>
          )}

          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-white/20 hover:border-purple-500/50 rounded-2xl p-6 text-center cursor-pointer transition-colors flex flex-col items-center justify-center gap-3 bg-white/[0.02]"
          >
            {imagePreview ? (
              <div className="w-32 h-32 rounded-xl overflow-hidden border border-white/20 relative">
                <Image
                  src={imagePreview}
                  alt="Preview"
                  width={128}
                  height={128}
                  className="w-full h-full object-cover"
                  unoptimized
                />
              </div>
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-purple-500/10 flex items-center justify-center text-purple-400">
                <Upload className="w-8 h-8" />
              </div>
            )}
            <div>
              <p className="text-sm font-semibold text-white">
                {imageFile ? imageFile.name : "Click to select or drag image"}
              </p>
              <p className="text-xs text-white/40 mt-1">JPEG, PNG, or WebP (max 5MB)</p>
            </div>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
            <GlassButton type="button" variant="ghost" onClick={() => setImageModalOpen(false)}>
              Cancel
            </GlassButton>
            <GlassButton type="submit" variant="primary" disabled={uploadingImage || !imageFile}>
              {uploadingImage ? "Uploading..." : "Upload Image"}
            </GlassButton>
          </div>
        </form>
      </GlassModal>
    </AppLayout>
  );
}
