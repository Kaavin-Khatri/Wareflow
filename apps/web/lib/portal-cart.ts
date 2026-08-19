/**
 * Client-side Cart State Manager for Retailer Self-Service Portal.
 * Handles localStorage persistence, quantity mutations, and reactive storage events.
 */

export interface PortalCartItem {
  productId: string;
  sku: string;
  name: string;
  unitPrice: number;
  quantity: number;
  unit?: string;
  imageUrl?: string | null;
  categoryName?: string | null;
}

const CART_STORAGE_KEY = "wareflow_portal_cart";
const CART_CHANGE_EVENT = "wareflow_cart_updated";

export function getCartItems(): PortalCartItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    console.warn("Failed to parse cart storage:", err);
    return [];
  }
}

export function saveCartItems(items: PortalCartItem[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
    window.dispatchEvent(new Event(CART_CHANGE_EVENT));
  } catch (err) {
    console.warn("Failed to write cart storage:", err);
  }
}

export function addToCart(item: Omit<PortalCartItem, "quantity">, qty: number = 1): void {
  const current = getCartItems();
  const existingIdx = current.findIndex((i) => i.productId === item.productId);

  if (existingIdx >= 0) {
    current[existingIdx].quantity += qty;
  } else {
    current.push({ ...item, quantity: qty });
  }

  saveCartItems(current);
}

export function updateCartQuantity(productId: string, quantity: number): void {
  const current = getCartItems();
  if (quantity <= 0) {
    removeFromCart(productId);
    return;
  }

  const item = current.find((i) => i.productId === productId);
  if (item) {
    item.quantity = quantity;
    saveCartItems(current);
  }
}

export function removeFromCart(productId: string): void {
  const current = getCartItems();
  const filtered = current.filter((i) => i.productId !== productId);
  saveCartItems(filtered);
}

export function clearCart(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(CART_STORAGE_KEY);
  window.dispatchEvent(new Event(CART_CHANGE_EVENT));
}

export function getCartTotal(): { itemCount: number; subtotal: number } {
  const items = getCartItems();
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = items.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0);
  return { itemCount, subtotal: Math.round(subtotal * 100) / 100 };
}
