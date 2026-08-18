import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import StockAnalyticsPage from "@/app/admin/analytics/stock/page";
import { ThemeProvider } from "@/components/ThemeProvider";
import { apiClient } from "@/lib/api-client";

// Mock Next Navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/analytics/stock",
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
  }),
}));

// Mock apiClient
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

// Mock ResizeObserver for Recharts ResponsiveContainer
global.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

const mockValueSummary = {
  total_stock_value: 1250000,
  total_units: 4500,
  total_products: 25,
  by_category: [
    {
      category_id: "cat-1",
      category_name: "Grains & Pulses",
      total_value: 750000,
      total_units: 3000,
      product_count: 15,
      percentage: 60.0,
    },
    {
      category_id: "cat-2",
      category_name: "Edible Oils",
      total_value: 500000,
      total_units: 1500,
      product_count: 10,
      percentage: 40.0,
    },
  ],
  by_warehouse: [
    {
      warehouse_id: "wh-1",
      warehouse_name: "North Central Hub",
      total_value: 800000,
      total_units: 3000,
      batch_count: 12,
      percentage: 64.0,
    },
  ],
};

const mockHealthDist = {
  healthy_count: 18,
  low_count: 4,
  critical_count: 2,
  out_of_stock_count: 1,
  total_products: 25,
  bands: [
    {
      status: "healthy",
      label: "Healthy Stock",
      count: 18,
      percentage: 72.0,
      description: "Above reorder threshold",
    },
    {
      status: "low",
      label: "Low Stock",
      count: 4,
      percentage: 16.0,
      description: "At or below reorder threshold",
    },
    {
      status: "critical",
      label: "Critical",
      count: 2,
      percentage: 8.0,
      description: "25% or below reorder point",
    },
    {
      status: "out_of_stock",
      label: "Out of Stock",
      count: 1,
      percentage: 4.0,
      description: "0 units available",
    },
  ],
};

const mockTopProducts = {
  by_value: [
    {
      product_id: "p1",
      sku: "BASMATI-PREM-5K",
      name: "Royal Basmati Rice 5kg",
      category_name: "Grains & Pulses",
      total_on_hand: 500,
      cost_price: 350,
      total_value: 175000,
      base_uom_name: "pcs",
    },
  ],
  by_quantity: [
    {
      product_id: "p1",
      sku: "BASMATI-PREM-5K",
      name: "Royal Basmati Rice 5kg",
      category_name: "Grains & Pulses",
      total_on_hand: 500,
      cost_price: 350,
      total_value: 175000,
      base_uom_name: "pcs",
    },
  ],
};

const mockExpiryTimeline = {
  windows: [
    {
      window_key: "this_week",
      label: "Expiring ≤ 7 Days",
      batch_count: 2,
      total_quantity: 40,
      total_value: 14000,
    },
    {
      window_key: "next_3_months",
      label: "Expiring 31-90 Days",
      batch_count: 8,
      total_quantity: 200,
      total_value: 70000,
    },
  ],
  total_expiring_soon_count: 2,
  total_expiring_soon_value: 14000,
};

describe("Stock Analytics Dashboard View", () => {
  beforeEach(() => {
    window.matchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes("/analytics/stock/value-summary")) {
        return Promise.resolve(mockValueSummary);
      }
      if (url.includes("/analytics/stock/health-distribution")) {
        return Promise.resolve(mockHealthDist);
      }
      if (url.includes("/analytics/stock/top-value-products")) {
        return Promise.resolve(mockTopProducts);
      }
      if (url.includes("/analytics/stock/expiry-timeline")) {
        return Promise.resolve(mockExpiryTimeline);
      }
      if (url === "/me" || url === "/profiles/me") {
        return Promise.resolve({
          id: "u-1",
          email: "owner@wareflow.io",
          display_name: "Manager",
          role_name: "Manager",
          permissions: ["inventory:view"],
        });
      }
      return Promise.resolve({});
    });
  });

  it("should render stock analytics KPIs, category concentration, and health bands", async () => {
    render(
      <ThemeProvider>
        <StockAnalyticsPage />
      </ThemeProvider>,
    );

    // Assert header
    expect(screen.getByText("Stock Valuation & Composition Analytics")).toBeDefined();

    // Wait for data load
    await waitFor(() => {
      expect(screen.getAllByText("Grains & Pulses").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Edible Oils").length).toBeGreaterThan(0);
      expect(screen.getAllByText("North Central Hub").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Royal Basmati Rice 5kg").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Expiring ≤ 7 Days").length).toBeGreaterThan(0);
    });

    // Check health band items
    expect(screen.getAllByText("Above reorder threshold").length).toBeGreaterThan(0);
    expect(screen.getAllByText("0 units available").length).toBeGreaterThan(0);
  });
});
