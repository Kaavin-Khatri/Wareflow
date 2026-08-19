"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "@/lib/firebase-client";

export interface CatalogProduct {
  id: string;
  sku: string;
  name: string;
  description: string | null;
  content_details: string | null;
  image_url: string | null;
  category_id: string | null;
  category_name: string | null;
  unit: string;
  base_price: number;
  effective_price: number;
  discount_percentage: number;
  pricing_tier: string;
  availability: "Available" | "Low" | "Out";
  hsn_code: string | null;
}

export interface CategoryOption {
  id: string;
  name: string;
}

export default function PortalCatalogPage() {
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [categories, setCategories] = useState<CategoryOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Sorting state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [stockFilter, setStockFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("name-asc");

  // Interaction modals
  const [inquiryProduct, setInquiryProduct] = useState<CatalogProduct | null>(null);
  const [orderProduct, setOrderProduct] = useState<CatalogProduct | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        setLoading(false);
        return;
      }
      try {
        const idToken = await user.getIdToken();
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

        // Fetch catalog & categories in parallel
        const [catRes, prodRes] = await Promise.all([
          fetch(`${apiUrl}/portal/categories`, { headers: { Authorization: `Bearer ${idToken}` } }),
          fetch(`${apiUrl}/portal/catalog`, { headers: { Authorization: `Bearer ${idToken}` } }),
        ]);

        if (catRes.ok) {
          const catData = await catRes.json();
          setCategories(catData);
        }
        if (prodRes.ok) {
          const prodData = await prodRes.json();
          setProducts(prodData);
        } else {
          setError("Failed to load catalog products.");
        }
      } catch (err) {
        console.error("Error loading portal catalog:", err);
        setError("Network error while loading catalog.");
      } finally {
        setLoading(false);
      }
    });

    return () => unsubscribe();
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const filteredProducts = useMemo(() => {
    return products
      .filter((p) => {
        // Search filter
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchName = p.name.toLowerCase().includes(q);
          const matchSku = p.sku.toLowerCase().includes(q);
          const matchDesc = p.description?.toLowerCase().includes(q);
          const matchCat = p.category_name?.toLowerCase().includes(q);
          if (!matchName && !matchSku && !matchDesc && !matchCat) return false;
        }
        // Category filter
        if (selectedCategory !== "all" && p.category_id !== selectedCategory) {
          return false;
        }
        // Stock filter
        if (stockFilter !== "all" && p.availability.toLowerCase() !== stockFilter) {
          return false;
        }
        return true;
      })
      .sort((a, b) => {
        if (sortBy === "name-asc") return a.name.localeCompare(b.name);
        if (sortBy === "name-desc") return b.name.localeCompare(a.name);
        if (sortBy === "price-asc") return a.effective_price - b.effective_price;
        if (sortBy === "price-desc") return b.effective_price - a.effective_price;
        if (sortBy === "discount-desc") return b.discount_percentage - a.discount_percentage;
        return 0;
      });
  }, [products, searchQuery, selectedCategory, stockFilter, sortBy]);

  const activeTier = products.length > 0 ? products[0].pricing_tier : "standard";

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-3 rounded-2xl bg-emerald-950/90 border border-emerald-500/30 text-emerald-200 text-sm font-medium shadow-2xl backdrop-blur-xl animate-fade-in flex items-center gap-2">
          <span>✓</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Banner */}
      <CatalogHeader activeTier={activeTier} productCount={products.length} />

      {/* Controls: Search, Categories, Filters, Sorting */}
      <CatalogControls
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        selectedCategory={selectedCategory}
        setSelectedCategory={setSelectedCategory}
        categories={categories}
        stockFilter={stockFilter}
        setStockFilter={setStockFilter}
        sortBy={sortBy}
        setSortBy={setSortBy}
      />

      {/* Product Grid / Loading / Empty State */}
      {loading ? (
        <CatalogLoadingSkeleton />
      ) : error ? (
        <div className="p-8 rounded-3xl bg-rose-500/10 border border-rose-500/20 text-center text-rose-300">
          <p className="font-medium">{error}</p>
        </div>
      ) : filteredProducts.length === 0 ? (
        <CatalogEmptyState onReset={() => { setSearchQuery(""); setSelectedCategory("all"); setStockFilter("all"); }} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {filteredProducts.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              onAskQuestion={() => setInquiryProduct(product)}
              onAddToOrder={() => setOrderProduct(product)}
            />
          ))}
        </div>
      )}

      {/* Inquiry Dialog */}
      {inquiryProduct && (
        <InquiryModal
          product={inquiryProduct}
          onClose={() => setInquiryProduct(null)}
          onSuccess={() => {
            setInquiryProduct(null);
            showToast(`Inquiry for ${inquiryProduct.name} submitted successfully!`);
          }}
        />
      )}

      {/* Quick Order Dialog */}
      {orderProduct && (
        <QuickOrderModal
          product={orderProduct}
          onClose={() => setOrderProduct(null)}
          onConfirm={(qty) => {
            setOrderProduct(null);
            showToast(`Added ${qty} ${orderProduct.unit}(s) of ${orderProduct.name} to order!`);
          }}
        />
      )}
    </div>
  );
}

function CatalogHeader({ activeTier, productCount }: { activeTier: string; productCount: number }) {
  const tierCapitalized = activeTier.charAt(0).toUpperCase() + activeTier.slice(1);
  return (
    <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-slate-900/50 border border-white/10 backdrop-blur-xl relative overflow-hidden">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Wholesale Catalog</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-indigo-500/20 border border-indigo-500/30 text-indigo-300">
              {tierCapitalized} Tier Pricing
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 max-w-xl">
            Browse live wholesale inventory with your customized {tierCapitalized} pricing discount automatically applied.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/portal/orders"
            className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-200 text-xs font-medium transition-all flex items-center gap-2"
          >
            <span>My Orders</span>
            <span>&rarr;</span>
          </Link>
          <div className="px-3.5 py-2.5 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
            {productCount} Items Available
          </div>
        </div>
      </div>
    </div>
  );
}

function CatalogControls({
  searchQuery,
  setSearchQuery,
  selectedCategory,
  setSelectedCategory,
  categories,
  stockFilter,
  setStockFilter,
  sortBy,
  setSortBy,
}: {
  searchQuery: string;
  setSearchQuery: (v: string) => void;
  selectedCategory: string;
  setSelectedCategory: (v: string) => void;
  categories: CategoryOption[];
  stockFilter: string;
  setStockFilter: (v: string) => void;
  sortBy: string;
  setSortBy: (v: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex flex-col sm:flex-row items-center gap-3">
        {/* Instant Search Bar */}
        <div className="relative flex-1 w-full">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search products by SKU, name, or description..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/10 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all"
          />
          <span className="absolute left-3.5 top-2.5 text-slate-500 text-sm">🔍</span>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-2.5 text-xs text-slate-400 hover:text-white"
            >
              ✕
            </button>
          )}
        </div>

        {/* Stock Filter Pills */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-white/[0.03] border border-white/10 w-full sm:w-auto overflow-x-auto">
          {[
            { label: "All Items", value: "all" },
            { label: "Available", value: "available" },
            { label: "Low Stock", value: "low" },
            { label: "Out of Stock", value: "out" },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setStockFilter(tab.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                stockFilter === tab.value
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Sort Selector */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="w-full sm:w-44 px-3 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
        >
          <option value="name-asc">Sort: Name (A-Z)</option>
          <option value="name-desc">Sort: Name (Z-A)</option>
          <option value="price-asc">Sort: Price (Low to High)</option>
          <option value="price-desc">Sort: Price (High to Low)</option>
          <option value="discount-desc">Sort: Highest Discount</option>
        </select>
      </div>

      {/* Category Pills Bar */}
      {categories.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          <button
            onClick={() => setSelectedCategory("all")}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap border ${
              selectedCategory === "all"
                ? "bg-white/15 border-white/30 text-white shadow-sm"
                : "bg-white/[0.03] border-white/10 text-slate-400 hover:text-slate-200"
            }`}
          >
            All Categories
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap border ${
                selectedCategory === cat.id
                  ? "bg-indigo-600/30 border-indigo-500/50 text-indigo-200 shadow-sm shadow-indigo-500/20"
                  : "bg-white/[0.03] border-white/10 text-slate-400 hover:text-slate-200"
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ProductCard({
  product,
  onAskQuestion,
  onAddToOrder,
}: {
  product: CatalogProduct;
  onAskQuestion: () => void;
  onAddToOrder: () => void;
}) {
  const isDiscounted = product.discount_percentage > 0;
  const isOut = product.availability === "Out";

  return (
    <div className="rounded-2xl bg-white/[0.03] border border-white/10 hover:border-indigo-500/30 hover:bg-white/[0.05] transition-all p-4 flex flex-col justify-between group backdrop-blur-md">
      <div>
        {/* Image & Badges */}
        <div className="h-40 w-full rounded-xl bg-gradient-to-br from-slate-800/80 to-slate-900/90 border border-white/5 flex items-center justify-center relative overflow-hidden mb-3.5">
          {product.image_url ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img src={product.image_url} alt={product.name} className="h-full w-full object-cover" />
          ) : (
            <span className="text-4xl select-none group-hover:scale-110 transition-transform">📦</span>
          )}
          {/* Availability Status Badge */}
          <div className="absolute top-2.5 right-2.5">
            <AvailabilityBadge status={product.availability} />
          </div>
          {/* Category Tag */}
          {product.category_name && (
            <div className="absolute bottom-2.5 left-2.5 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-md text-[10px] text-slate-300 font-medium border border-white/10">
              {product.category_name}
            </div>
          )}
        </div>

        {/* Product Details */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <span>{product.sku}</span>
            {product.hsn_code && <span>HSN {product.hsn_code}</span>}
          </div>
          <h3 className="text-sm font-semibold text-white line-clamp-1 group-hover:text-indigo-300 transition-colors">
            {product.name}
          </h3>
          {product.content_details && (
            <p className="text-xs text-slate-400 line-clamp-1">{product.content_details}</p>
          )}
        </div>
      </div>

      {/* Pricing and Action Footer */}
      <div className="mt-4 pt-3 border-t border-white/5 space-y-3">
        <div>
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-bold text-white tracking-tight">
              ₹{product.effective_price.toFixed(2)}
            </span>
            <span className="text-xs text-slate-400">/ {product.unit}</span>
          </div>

          {isDiscounted ? (
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="text-xs text-slate-500 line-through">
                ₹{product.base_price.toFixed(2)}
              </span>
              <span className="text-[11px] font-semibold text-emerald-400">
                {product.discount_percentage}% OFF
              </span>
            </div>
          ) : (
            <div className="text-[11px] text-slate-500 mt-0.5">Standard Wholesale Rate</div>
          )}
        </div>

        {/* Actions */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onAskQuestion}
            className="px-2.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white text-xs font-medium transition-all text-center"
          >
            Ask Question
          </button>
          <button
            onClick={onAddToOrder}
            disabled={isOut}
            className={`px-2.5 py-1.5 rounded-xl text-xs font-medium transition-all text-center ${
              isOut
                ? "bg-white/5 text-slate-600 border border-white/5 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20"
            }`}
          >
            {isOut ? "Out of Stock" : "Add to Order"}
          </button>
        </div>
      </div>
    </div>
  );
}

function AvailabilityBadge({ status }: { status: "Available" | "Low" | "Out" }) {
  if (status === "Available") {
    return (
      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1 backdrop-blur-md">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        Available
      </span>
    );
  }
  if (status === "Low") {
    return (
      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1 backdrop-blur-md">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
        Low Stock
      </span>
    );
  }
  return (
    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-rose-500/20 text-rose-300 border border-rose-500/30 backdrop-blur-md">
      Out
    </span>
  );
}

function CatalogLoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
        <div key={i} className="rounded-2xl bg-white/[0.02] border border-white/5 p-4 animate-pulse space-y-3">
          <div className="h-40 rounded-xl bg-white/5 w-full" />
          <div className="h-4 bg-white/5 rounded w-3/4" />
          <div className="h-3 bg-white/5 rounded w-1/2" />
          <div className="h-8 bg-white/5 rounded w-full mt-4" />
        </div>
      ))}
    </div>
  );
}

function CatalogEmptyState({ onReset }: { onReset: () => void }) {
  return (
    <div className="p-12 rounded-3xl bg-white/[0.02] border border-white/10 text-center text-slate-400 space-y-3">
      <div className="text-4xl">🔍</div>
      <h3 className="text-base font-semibold text-slate-200">No matching products found</h3>
      <p className="text-xs text-slate-400 max-w-sm mx-auto">
        Try adjusting your search keywords, category filters, or stock status.
      </p>
      <button
        onClick={onReset}
        className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-white text-xs font-medium transition-all"
      >
        Clear All Filters
      </button>
    </div>
  );
}

function InquiryModal({
  product,
  onClose,
  onSuccess,
}: {
  product: CatalogProduct;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const currentUser = auth.currentUser;
      const idToken = currentUser ? await currentUser.getIdToken() : "";
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      const res = await fetch(`${apiUrl}/portal/inquiries`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          product_id: product.id,
          message: message.trim(),
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to submit inquiry. Please try again.");
      }

      onSuccess();
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
      <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-white/10 p-6 space-y-4 shadow-2xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Ask a Question</h3>
            <p className="text-xs text-slate-400">{product.name} ({product.sku})</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-sm" disabled={isSubmitting}>✕</button>
        </div>

        {submitError && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            {submitError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300">Your Inquiry / Question</label>
            <textarea
              rows={4}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask about bulk volumes, packaging options, or lead times..."
              disabled={isSubmitting}
              className="w-full p-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:opacity-50"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!message.trim() || isSubmitting}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium shadow-md shadow-indigo-600/30 flex items-center gap-1.5"
            >
              {isSubmitting ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Sending...</span>
                </>
              ) : (
                <span>Send Inquiry</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function QuickOrderModal({
  product,
  onClose,
  onConfirm,
}: {
  product: CatalogProduct;
  onClose: () => void;
  onConfirm: (qty: number) => void;
}) {
  const [quantity, setQuantity] = useState(1);
  const lineTotal = quantity * product.effective_price;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
      <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-white/10 p-6 space-y-4 shadow-2xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Add to Order</h3>
            <p className="text-xs text-slate-400">{product.name}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-sm">✕</button>
        </div>

        <div className="p-3.5 rounded-2xl bg-white/[0.03] border border-white/5 flex items-center justify-between text-xs">
          <span className="text-slate-400">Unit Price ({product.pricing_tier} tier):</span>
          <span className="text-white font-bold">₹{product.effective_price.toFixed(2)} / {product.unit}</span>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-medium text-slate-300">Quantity ({product.unit}s)</label>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setQuantity((q) => Math.max(1, q - 1))}
              className="w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold"
            >
              -
            </button>
            <input
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
              className="flex-1 text-center py-2 rounded-xl bg-white/5 border border-white/10 text-white font-bold text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
            />
            <button
              onClick={() => setQuantity((q) => q + 1)}
              className="w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold"
            >
              +
            </button>
          </div>
        </div>

        <div className="pt-2 border-t border-white/5 flex items-center justify-between">
          <span className="text-xs text-slate-400">Estimated Total:</span>
          <span className="text-base font-bold text-indigo-300">
            ₹{lineTotal.toFixed(2)}
          </span>
        </div>

        <div className="flex items-center justify-end gap-2 pt-2">
          <button
            onClick={onClose}
            className="px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-medium"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(quantity)}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-600/30"
          >
            Confirm & Add
          </button>
        </div>
      </div>
    </div>
  );
}
