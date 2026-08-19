import React from "react";
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import PortalCartPage from "@/app/portal/cart/page";
import PortalOrdersPage from "@/app/portal/orders/page";
import {
  addToCart,
  clearCart,
  getCartItems,
  getCartTotal,
  removeFromCart,
  updateCartQuantity,
} from "@/lib/portal-cart";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => "/portal/cart",
}));

// Mock Firebase Auth
vi.mock("firebase/auth", () => ({
  onAuthStateChanged: vi.fn((auth, cb) => {
    cb({
      uid: "user-alpha-uid",
      email: "alpha@mart.com",
      getIdToken: vi.fn().mockResolvedValue("test-retailer-token"),
    });
    return vi.fn();
  }),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("@/lib/firebase-client", () => ({
  auth: {
    currentUser: {
      uid: "user-alpha-uid",
      email: "alpha@mart.com",
      getIdToken: vi.fn().mockResolvedValue("test-retailer-token"),
    },
  },
}));

describe("Portal Cart State Manager (lib/portal-cart.ts)", () => {
  beforeEach(() => {
    localStorage.clear();
    clearCart();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("should add products to cart and retrieve correctly", () => {
    expect(getCartItems()).toEqual([]);

    addToCart(
      {
        productId: "prod-tea-1",
        sku: "BEV-TEA-001",
        name: "Assam Gold Premium Tea 500g",
        unitPrice: 190.0,
        unit: "Piece",
      },
      2
    );

    const items = getCartItems();
    expect(items.length).toBe(1);
    expect(items[0].productId).toBe("prod-tea-1");
    expect(items[0].quantity).toBe(2);

    // Adding same product increments quantity
    addToCart(
      {
        productId: "prod-tea-1",
        sku: "BEV-TEA-001",
        name: "Assam Gold Premium Tea 500g",
        unitPrice: 190.0,
        unit: "Piece",
      },
      3
    );

    const updated = getCartItems();
    expect(updated.length).toBe(1);
    expect(updated[0].quantity).toBe(5);
  });

  it("should update quantity and compute totals accurately", () => {
    addToCart(
      {
        productId: "prod-tea-1",
        sku: "BEV-TEA-001",
        name: "Assam Gold Premium Tea",
        unitPrice: 200.0,
      },
      2
    );
    addToCart(
      {
        productId: "prod-bis-1",
        sku: "SNK-BIS-001",
        name: "Butter Crunch Cookies",
        unitPrice: 100.0,
      },
      4
    );

    let total = getCartTotal();
    expect(total.itemCount).toBe(6);
    expect(total.subtotal).toBe(800.0); // (2*200) + (4*100)

    updateCartQuantity("prod-tea-1", 5);
    total = getCartTotal();
    expect(total.itemCount).toBe(9);
    expect(total.subtotal).toBe(1400.0); // (5*200) + (4*100)

    removeFromCart("prod-bis-1");
    total = getCartTotal();
    expect(total.itemCount).toBe(5);
    expect(total.subtotal).toBe(1000.0);
  });
});

describe("Portal Cart Page (app/portal/cart/page.tsx)", () => {
  beforeEach(() => {
    localStorage.clear();
    clearCart();
    vi.restoreAllMocks();
  });

  it("should render empty cart view when no items are present", () => {
    render(<PortalCartPage />);
    expect(screen.getByText("Your Cart is Empty")).toBeDefined();
    expect(screen.getByText("Browse Wholesale Catalog")).toBeDefined();
  });

  it("should render cart items, calculate line totals, and place auto-confirmed order", async () => {
    addToCart(
      {
        productId: "prod-tea-1",
        sku: "BEV-TEA-001",
        name: "Assam Gold Premium Tea 500g",
        unitPrice: 200.0,
        unit: "Piece",
      },
      10
    );

    // Mock successful POST /portal/orders
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "so-test-101",
        so_number: "SO-2026-0099",
        status: "confirmed",
        total_amount: 2000.0,
        auto_confirmed: true,
        message: "Order placed and confirmed successfully with reserved inventory.",
        items_count: 1,
        created_at: new Date().toISOString(),
      }),
    });
    global.fetch = mockFetch;

    render(<PortalCartPage />);

    expect(screen.getByText("Assam Gold Premium Tea 500g")).toBeDefined();
    expect(screen.getByText("BEV-TEA-001")).toBeDefined();
    expect(screen.getByText("₹2,000.00")).toBeDefined();

    const submitBtn = screen.getByText("Place Wholesale Order");
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/portal/orders"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            items: [{ product_id: "prod-tea-1", qty: 10 }],
          }),
        })
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Order Placed & Confirmed!")).toBeDefined();
      expect(screen.getByText("SO-2026-0099")).toBeDefined();
    });
  });

  it("should show pending review alert when order is created in draft", async () => {
    addToCart(
      {
        productId: "prod-tea-1",
        sku: "BEV-TEA-001",
        name: "Assam Gold Premium Tea 500g",
        unitPrice: 200.0,
        unit: "Piece",
      },
      500
    );

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "so-test-draft-1",
        so_number: "SO-2026-0100",
        status: "draft",
        total_amount: 100000.0,
        auto_confirmed: false,
        message: "Order received in draft status and queued for staff review.",
        reason: "Credit limit exceeded: Required 100000.0, available 50000.0",
        items_count: 1,
        created_at: new Date().toISOString(),
      }),
    });
    global.fetch = mockFetch;

    render(<PortalCartPage />);

    const submitBtn = screen.getByText("Place Wholesale Order");
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Order Submitted (Pending Review)")).toBeDefined();
      expect(screen.getByText("SO-2026-0100")).toBeDefined();
      expect(
        screen.getByText("Credit limit exceeded: Required 100000.0, available 50000.0")
      ).toBeDefined();
    });
  });
});

describe("Portal Orders Page (app/portal/orders/page.tsx)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("should render list of orders and allow filtering", async () => {
    const mockOrders = [
      {
        id: "so-1",
        so_number: "SO-2026-0001",
        status: "confirmed",
        order_date: "2026-08-19T10:00:00Z",
        total_amount: 2500.0,
        items_count: 2,
        created_at: "2026-08-19T10:00:00Z",
      },
      {
        id: "so-2",
        so_number: "SO-2026-0002",
        status: "draft",
        order_date: "2026-08-19T11:00:00Z",
        total_amount: 8000.0,
        items_count: 3,
        created_at: "2026-08-19T11:00:00Z",
      },
    ];

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockOrders,
    });
    global.fetch = mockFetch;

    render(<PortalOrdersPage />);

    await waitFor(() => {
      expect(screen.getByText("SO-2026-0001")).toBeDefined();
      expect(screen.getByText("SO-2026-0002")).toBeDefined();
    });

    // Test Search filter
    const searchInput = screen.getByPlaceholderText("Search by SO number...");
    fireEvent.change(searchInput, { target: { value: "0001" } });

    expect(screen.getByText("SO-2026-0001")).toBeDefined();
    expect(screen.queryByText("SO-2026-0002")).toBeNull();
  });
});
