"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/firebase-client";
import {
  clearCart,
  getCartItems,
  getCartTotal,
  PortalCartItem,
  removeFromCart,
  updateCartQuantity,
} from "@/lib/portal-cart";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";
import {
  ShoppingCart,
  Trash2,
  Plus,
  Minus,
  CheckCircle2,
  Clock,
  ArrowRight,
  AlertTriangle,
  Package,
} from "lucide-react";

interface OrderPlacementResult {
  id: string;
  so_number: string;
  status: string;
  total_amount: number;
  auto_confirmed: boolean;
  message: string;
  reason?: string | null;
  items_count: number;
  created_at: string;
}

export default function PortalCartPage() {
  const router = useRouter();
  const [items, setItems] = useState<PortalCartItem[]>(() =>
    typeof window !== "undefined" ? getCartItems() : []
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [orderResult, setOrderResult] = useState<OrderPlacementResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const refreshCart = () => {
      setItems(getCartItems());
    };

    window.addEventListener("wareflow_cart_updated", refreshCart);
    window.addEventListener("storage", refreshCart);
    return () => {
      window.removeEventListener("wareflow_cart_updated", refreshCart);
      window.removeEventListener("storage", refreshCart);
    };
  }, []);

  const { itemCount, subtotal } = getCartTotal();

  const handleQuantityChange = (productId: string, newQty: number) => {
    if (newQty <= 0) {
      removeFromCart(productId);
    } else {
      updateCartQuantity(productId, newQty);
    }
  };

  const handleRemove = (productId: string) => {
    removeFromCart(productId);
  };

  const handleClear = () => {
    clearCart();
  };

  const handleSubmitOrder = async () => {
    if (items.length === 0 || isSubmitting) return;

    setError(null);
    setIsSubmitting(true);

    try {
      const user = auth.currentUser;
      if (!user) {
        setError("You must be logged in to place an order.");
        setIsSubmitting(false);
        return;
      }

      const idToken = await user.getIdToken();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      const payload = {
        items: items.map((it) => ({
          product_id: it.productId,
          qty: it.quantity,
        })),
      };

      const res = await fetch(`${apiUrl}/portal/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data: OrderPlacementResult = await res.json();
        setOrderResult(data);
        clearCart();
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Failed to submit wholesale order. Please try again.");
      }
    } catch (err) {
      console.error("Order submit error:", err);
      setError("Network connection error while submitting your order.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (orderResult) {
    const isAutoConfirmed = orderResult.auto_confirmed;
    return (
      <div className="max-w-3xl mx-auto py-8">
        <GlassCard className="p-8 sm:p-10 text-center space-y-6">
          <div className="flex justify-center">
            {isAutoConfirmed ? (
              <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8" />
              </div>
            ) : (
              <div className="w-16 h-16 rounded-3xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                <Clock className="w-8 h-8" />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-center gap-2">
              <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                Order Reference
              </span>
              <GlassBadge variant={isAutoConfirmed ? "success" : "warning"}>
                {orderResult.so_number}
              </GlassBadge>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              {isAutoConfirmed ? "Order Placed & Confirmed!" : "Order Submitted (Pending Review)"}
            </h2>
            <p className="text-sm text-slate-300 max-w-md mx-auto">
              {isAutoConfirmed
                ? "Your wholesale sales order has been confirmed and queued for fulfillment with allocated stock."
                : "Your order was saved in draft status. Our operations staff has been notified to review and allocate inventory."}
            </p>
          </div>

          {orderResult.reason && (
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs text-left max-w-lg mx-auto flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold mb-0.5">Review Note:</p>
                <p>{orderResult.reason}</p>
              </div>
            </div>
          )}

          <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/10 max-w-md mx-auto flex items-center justify-between text-xs">
            <span className="text-slate-400">Total Order Amount:</span>
            <span className="text-lg font-bold font-mono text-emerald-400">
              ₹{orderResult.total_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
            <GlassButton
              variant="secondary"
              onClick={() => router.push("/portal/catalog")}
              className="w-full sm:w-auto"
            >
              Continue Browsing
            </GlassButton>
            <GlassButton
              variant="primary"
              onClick={() => router.push("/portal/orders")}
              className="w-full sm:w-auto flex items-center justify-center gap-2"
            >
              <span>View in My Orders</span>
              <ArrowRight className="w-4 h-4" />
            </GlassButton>
          </div>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Wholesale Cart</h1>
            {items.length > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                {itemCount} {itemCount === 1 ? "item" : "items"}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Review your selected products, adjust packaging quantities, and submit your order.
          </p>
        </div>

        {items.length > 0 && (
          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-rose-500/10 text-slate-400 hover:text-rose-300 border border-white/10 hover:border-rose-500/20 text-xs font-medium transition-all"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Cart</span>
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {items.length === 0 ? (
        <GlassCard className="p-12 text-center space-y-4">
          <div className="w-16 h-16 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
            <ShoppingCart className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">Your Cart is Empty</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Explore your customized wholesale product catalog and add items to place an order.
            </p>
          </div>
          <div className="pt-2">
            <Link href="/portal/catalog">
              <GlassButton variant="primary" className="inline-flex items-center gap-2">
                <Package className="w-4 h-4" />
                <span>Browse Wholesale Catalog</span>
              </GlassButton>
            </Link>
          </div>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Items List */}
          <div className="lg:col-span-2 space-y-3">
            {items.map((item) => {
              const lineTotal = item.quantity * item.unitPrice;
              return (
                <GlassCard
                  key={item.productId}
                  className="p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-xl shrink-0">
                      📦
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-semibold text-white truncate">{item.name}</h4>
                        <span className="px-1.5 py-0.2 rounded bg-white/5 text-slate-400 font-mono text-[10px] border border-white/10">
                          {item.sku}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        ₹{item.unitPrice.toFixed(2)} per {item.unit || "unit"}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end gap-6 w-full sm:w-auto">
                    {/* Stepper */}
                    <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl p-1">
                      <button
                        onClick={() => handleQuantityChange(item.productId, item.quantity - 1)}
                        className="w-7 h-7 rounded-lg bg-white/5 hover:bg-white/10 text-white flex items-center justify-center transition-colors"
                      >
                        <Minus className="w-3.5 h-3.5" />
                      </button>
                      <span className="w-8 text-center text-xs font-bold text-white">
                        {item.quantity}
                      </span>
                      <button
                        onClick={() => handleQuantityChange(item.productId, item.quantity + 1)}
                        className="w-7 h-7 rounded-lg bg-white/5 hover:bg-white/10 text-white flex items-center justify-center transition-colors"
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Line Total */}
                    <div className="text-right min-w-[80px]">
                      <span className="text-xs text-slate-400 block text-[10px]">Total</span>
                      <span className="text-sm font-bold font-mono text-emerald-400">
                        ₹{lineTotal.toFixed(2)}
                      </span>
                    </div>

                    {/* Delete */}
                    <button
                      onClick={() => handleRemove(item.productId)}
                      className="p-2 rounded-xl text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                      title="Remove Item"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </GlassCard>
              );
            })}
          </div>

          {/* Order Summary Sidebar */}
          <div className="lg:col-span-1">
            <GlassCard className="p-6 space-y-5 sticky top-24">
              <h3 className="text-base font-bold text-white">Order Summary</h3>

              <div className="space-y-2.5 text-xs text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-400">Distinct Products:</span>
                  <span className="font-semibold text-white">{items.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Units:</span>
                  <span className="font-semibold text-white">{itemCount}</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-white/10">
                  <span className="text-sm font-semibold text-white">Estimated Subtotal:</span>
                  <span className="text-base font-bold font-mono text-emerald-400">
                    ₹{subtotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-[11px] text-indigo-300 space-y-1">
                <p className="font-semibold">⚡ Instant Verification</p>
                <p className="text-slate-400 leading-relaxed">
                  Orders within available stock and credit limits auto-confirm immediately.
                </p>
              </div>

              <GlassButton
                variant="primary"
                onClick={handleSubmitOrder}
                disabled={isSubmitting}
                className="w-full py-3 flex items-center justify-center gap-2 text-sm font-semibold shadow-lg shadow-indigo-600/30"
              >
                {isSubmitting ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Submitting Order...</span>
                  </>
                ) : (
                  <>
                    <span>Place Wholesale Order</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </GlassButton>
            </GlassCard>
          </div>
        </div>
      )}
    </div>
  );
}
