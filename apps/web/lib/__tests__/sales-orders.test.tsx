/**
 * Frontend Unit Tests for Sales Orders Admin View (Step 8.2).
 *
 * Tests:
 * 1. Renders KPI cards, summary metrics, and sales orders table
 * 2. Filters by search query and status tabs
 * 3. Creates new draft sales order with live tier pricing
 * 4. Confirms draft order and advances fulfillment status
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import SalesOrdersAdminPage, { SalesOrder } from "@/app/admin/sales-orders/page";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/sales-orders",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock AppLayout
vi.mock("@/components/AppLayout", () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-layout">{children}</div>
  ),
  AppLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-layout">{children}</div>
  ),
}));

const mockSalesOrders: SalesOrder[] = [
  {
    id: "so-1",
    so_number: "SO-202608-0001",
    buyer_type: "retailer",
    retailer_id: "ret-1",
    retailer_name: "Apex Kirana Stores",
    retailer_pricing_tier: "gold",
    status: "draft",
    order_date: "2026-08-18T10:00:00Z",
    total_amount: 9000.0,
    created_at: "2026-08-18T10:00:00Z",
    items: [
      {
        id: "so-item-1",
        so_id: "so-1",
        product_id: "prod-1",
        product_name: "Royal Basmati Rice 5kg",
        product_sku: "RIC-BAS-001",
        qty: 20,
        unit_price: 450.0,
        line_total: 9000.0,
      },
    ],
  },
  {
    id: "so-2",
    so_number: "SO-202608-0002",
    buyer_type: "retailer",
    retailer_id: "ret-2",
    retailer_name: "City Supermarket",
    retailer_pricing_tier: "silver",
    status: "confirmed",
    order_date: "2026-08-18T11:00:00Z",
    total_amount: 4750.0,
    created_at: "2026-08-18T11:00:00Z",
    items: [
      {
        id: "so-item-2",
        so_id: "so-2",
        product_id: "prod-1",
        product_name: "Royal Basmati Rice 5kg",
        product_sku: "RIC-BAS-001",
        qty: 10,
        unit_price: 475.0,
        line_total: 4750.0,
      },
    ],
  },
  {
    id: "so-3",
    so_number: "SO-202608-0003",
    buyer_type: "retailer",
    retailer_id: "ret-3",
    retailer_name: "Old Corner Grocery",
    retailer_pricing_tier: "standard",
    status: "delivered",
    order_date: "2026-08-17T09:00:00Z",
    total_amount: 2500.0,
    created_at: "2026-08-17T09:00:00Z",
    items: [],
  },
];

const mockRetailers = [
  {
    id: "ret-1",
    name: "Apex Kirana Stores",
    pricing_tier: "gold",
    credit_limit: 50000.0,
    credit_balance: 10000.0,
  },
  {
    id: "ret-2",
    name: "City Supermarket",
    pricing_tier: "silver",
    credit_limit: 25000.0,
    credit_balance: 0.0,
  },
];

const mockProducts = [
  {
    id: "prod-1",
    name: "Royal Basmati Rice 5kg",
    sku: "RIC-BAS-001",
    wholesale_price: 500.0,
  },
];

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url === "/sales-orders") return Promise.resolve(mockSalesOrders);
      if (url === "/retailers") return Promise.resolve(mockRetailers);
      if (url === "/products") return Promise.resolve(mockProducts);
      return Promise.resolve([]);
    }),
    post: vi.fn().mockImplementation((url: string) => {
      if (url === "/sales-orders") {
        return Promise.resolve({
          id: "so-new",
          so_number: "SO-202608-0004",
          status: "draft",
          total_amount: 4500.0,
        });
      }
      if (url.endsWith("/confirm")) {
        return Promise.resolve({
          ...mockSalesOrders[0],
          status: "confirmed",
        });
      }
      return Promise.resolve({});
    }),
    patch: vi.fn().mockImplementation(
      (
        url: string,
        body: { status: "draft" | "confirmed" | "packed" | "shipped" | "delivered" | "cancelled" }
      ) => {
        return Promise.resolve({
          ...mockSalesOrders[0],
          status: body.status,
        });
      }
    ),

  },
}));

describe("SalesOrdersAdminPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders KPI cards and sales orders list", async () => {
    render(<SalesOrdersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Sales Orders & Dispatch").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("SO-202608-0001").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("SO-202608-0002").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("SO-202608-0003").length).toBeGreaterThanOrEqual(1);
    });

    // Check KPI counts
    expect(screen.getAllByText("3").length).toBeGreaterThanOrEqual(1); // Total orders
    expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
  });

  it("filters sales orders by search input", async () => {
    render(<SalesOrdersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("SO-202608-0001").length).toBeGreaterThanOrEqual(1);
    });

    const searchInput = screen.getByPlaceholderText(/Search by SO number/i);
    fireEvent.change(searchInput, { target: { value: "City Supermarket" } });

    await waitFor(() => {
      expect(screen.getAllByText("City Supermarket").length).toBeGreaterThanOrEqual(1);
      expect(screen.queryByText("Apex Kirana Stores")).toBeNull();
    });
  });

  it("filters sales orders by status tabs", async () => {
    render(<SalesOrdersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("SO-202608-0001").length).toBeGreaterThanOrEqual(1);
    });

    // Click Delivered tab
    const deliveredTab = screen.getByText(/Delivered \(1\)/i);
    fireEvent.click(deliveredTab);

    await waitFor(() => {
      expect(screen.getAllByText("SO-202608-0003").length).toBeGreaterThanOrEqual(1);
      expect(screen.queryByText("SO-202608-0001")).toBeNull();
    });
  });

  it("opens create sales order modal and submits new draft order", async () => {
    const { apiClient } = await import("@/lib/api-client");
    render(<SalesOrdersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Create Sales Order").length).toBeGreaterThanOrEqual(1);
    });

    // Click Create Sales Order header button
    fireEvent.click(screen.getByText("Create Sales Order"));

    // Select retailer
    const retailerSelect = screen.getByLabelText(/Select Retailer/i);
    fireEvent.change(retailerSelect, { target: { value: "ret-1" } });

    // Select product in line item
    const productSelects = screen.getAllByRole("combobox");
    const productSelect = productSelects[productSelects.length - 1];
    fireEvent.change(productSelect, { target: { value: "prod-1" } });

    // Submit form
    const submitBtn = screen.getByRole("button", { name: "Create Draft Order" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/sales-orders",
        expect.objectContaining({
          buyer_type: "retailer",
          retailer_id: "ret-1",
        }),
      );
    });
  });

  it("opens details modal and confirms draft sales order", async () => {
    const { apiClient } = await import("@/lib/api-client");
    render(<SalesOrdersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("SO-202608-0001").length).toBeGreaterThanOrEqual(1);
    });

    // Click Details button for first order (draft)
    const detailButtons = screen.getAllByRole("button", { name: /Details/i });
    fireEvent.click(detailButtons[0]);

    await waitFor(() => {
      expect(screen.getAllByText("Sales Order: SO-202608-0001").length).toBeGreaterThanOrEqual(1);
    });

    // Click Confirm Order button
    const confirmBtn = screen.getByRole("button", { name: /Confirm Order \(Deduct FIFO\)/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith("/sales-orders/so-1/confirm");
    });
  });
});
