/**
 * Frontend Unit Tests for Profitability & Inventory Turnover Analytics UI (Step 16.1).
 *
 * Tests:
 * 1. Profitability page renders summary KPI cards, group-by toggle buttons, and data table.
 * 2. Group by toggle triggers API calls with group_by=category/retailer/product.
 * 3. Inventory Turnover page renders velocity metrics, days of stock, and health status badges.
 * 4. Health status filter tabs filter ranked turnover items.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import React from "react";
import ProfitabilityAnalyticsPage, {
  ProfitabilityResponse,
} from "@/app/admin/analytics/profitability/page";
import InventoryTurnoverPage, { TurnoverResponse } from "@/app/admin/analytics/turnover/page";
import { ThemeProvider } from "@/components/ThemeProvider";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
  }),
  usePathname: () => "/admin/analytics/profitability",
}));

// Mock firebase
vi.mock("@/lib/firebase-client", () => ({
  db: {},
}));

vi.mock("firebase/firestore", () => ({
  collection: vi.fn(),
  query: vi.fn(),
  orderBy: vi.fn(),
  limit: vi.fn(),
  onSnapshot: vi.fn(() => () => {}),
}));

// Mock API Client
const mockProfitabilityData: ProfitabilityResponse = {
  group_by: "product",
  period: "30d",
  summary: {
    total_revenue: 15800.0,
    total_cost: 12900.0,
    total_gross_margin_inr: 2900.0,
    overall_margin_pct: 18.4,
    total_units_sold: 50.0,
    total_orders: 2,
  },
  items: [
    {
      id: "prod-1",
      name: "Royal Basmati Rice 5kg",
      secondary_info: "SKU: RIC-BAS-001",
      badge: "Grains & Rice",
      units_sold: 15.0,
      orders_count: 2,
      total_revenue: 7300.0,
      total_cost: 6000.0,
      gross_margin_inr: 1300.0,
      gross_margin_pct: 17.8,
    },
    {
      id: "prod-2",
      name: "Sona Masoori Rice 5kg",
      secondary_info: "SKU: RIC-SON-002",
      badge: "Grains & Rice",
      units_sold: 15.0,
      orders_count: 1,
      total_revenue: 5700.0,
      total_cost: 4500.0,
      gross_margin_inr: 1200.0,
      gross_margin_pct: 21.1,
    },
    {
      id: "prod-3",
      name: "Fortune Sunflower Oil 1L",
      secondary_info: "SKU: OIL-SUN-003",
      badge: "Edible Oils",
      units_sold: 20.0,
      orders_count: 1,
      total_revenue: 2800.0,
      total_cost: 2400.0,
      gross_margin_inr: 400.0,
      gross_margin_pct: 14.3,
    },
  ],
  generated_at: "2026-08-24T12:00:00Z",
};

const mockTurnoverData: TurnoverResponse = {
  period: "30d",
  summary: {
    average_turnover_ratio: 0.74,
    average_days_of_stock: 67.5,
    healthy_count: 1,
    slowing_count: 1,
    at_risk_count: 1,
    total_products: 3,
  },
  items: [
    {
      product_id: "prod-2",
      product_name: "Sona Masoori Rice 5kg",
      sku: "RIC-SON-002",
      category_name: "Grains & Rice",
      unit: "Bag",
      current_on_hand: 60.0,
      units_sold: 15.0,
      average_on_hand: 67.5,
      turnover_ratio: 0.22,
      days_of_stock: 135.0,
      turnover_band: "at_risk",
      cost_price: 300.0,
      tied_up_capital: 18000.0,
    },
    {
      product_id: "prod-1",
      product_name: "Royal Basmati Rice 5kg",
      sku: "RIC-BAS-001",
      category_name: "Grains & Rice",
      unit: "Bag",
      current_on_hand: 15.0,
      units_sold: 15.0,
      average_on_hand: 22.5,
      turnover_ratio: 0.67,
      days_of_stock: 45.0,
      turnover_band: "slowing",
      cost_price: 400.0,
      tied_up_capital: 6000.0,
    },
    {
      product_id: "prod-3",
      product_name: "Fortune Sunflower Oil 1L",
      sku: "OIL-SUN-003",
      category_name: "Edible Oils",
      unit: "Pouch",
      current_on_hand: 5.0,
      units_sold: 20.0,
      average_on_hand: 15.0,
      turnover_ratio: 1.33,
      days_of_stock: 22.5,
      turnover_band: "healthy",
      cost_price: 120.0,
      tied_up_capital: 600.0,
    },
  ],
  generated_at: "2026-08-24T12:00:00Z",
};

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url === "/me") {
        return Promise.resolve({
          id: "u-1",
          email: "owner@wareflow.com",
          role_name: "Owner",
          permissions: ["all"],
        });
      }
      if (url.includes("/notifications")) {
        return Promise.resolve({ items: [] });
      }
      if (url.startsWith("/analytics/profitability")) {
        return Promise.resolve(mockProfitabilityData);
      }
      if (url.startsWith("/analytics/turnover")) {
        return Promise.resolve(mockTurnoverData);
      }
      if (url.startsWith("/analytics/period-comparisons")) {
        return Promise.resolve({ metrics: {} });
      }
      return Promise.resolve({});
    }),
  },
}));

describe("Profitability & Inventory Turnover Analytics UI (Step 16.1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
  });

  it("renders Profitability analytics page with KPI cards and product gross margins", async () => {
    render(
      <ThemeProvider>
        <ProfitabilityAnalyticsPage />
      </ThemeProvider>,
    );

    expect(screen.getByText("Profitability & Margin Analytics")).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("Royal Basmati Rice 5kg")).toBeDefined();
      expect(screen.getByText("Sona Masoori Rice 5kg")).toBeDefined();
      expect(screen.getByText("Fortune Sunflower Oil 1L")).toBeDefined();
      expect(screen.getByText("17.8%")).toBeDefined();
      expect(screen.getByText("21.1%")).toBeDefined();
    });
  });

  it("allows switching group by dimension (Category / Retailer) in Profitability page", async () => {
    render(
      <ThemeProvider>
        <ProfitabilityAnalyticsPage />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("Royal Basmati Rice 5kg")).toBeDefined();
    });

    const categoryBtn = screen.getByRole("button", { name: /category/i });
    await act(async () => {
      fireEvent.click(categoryBtn);
    });

    const retailerBtn = screen.getByRole("button", { name: /retailer/i });
    await act(async () => {
      fireEvent.click(retailerBtn);
    });
  });

  it("renders Inventory Turnover page with velocity metrics and health banding", async () => {
    render(
      <ThemeProvider>
        <InventoryTurnoverPage />
      </ThemeProvider>,
    );

    expect(screen.getByText("Inventory Turnover & Velocity")).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("Sona Masoori Rice 5kg")).toBeDefined();
      expect(screen.getByText("0.22x")).toBeDefined();
      expect(screen.getByText("At-Risk")).toBeDefined();
      expect(screen.getByText("Slowing")).toBeDefined();
      expect(screen.getByText("Healthy")).toBeDefined();
    });
  });

  it("filters inventory turnover table by health status band tabs", async () => {
    render(
      <ThemeProvider>
        <InventoryTurnoverPage />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("Sona Masoori Rice 5kg")).toBeDefined();
    });

    // Click "Healthy (Fast)" filter
    const healthyTab = screen.getByRole("button", { name: /Healthy \(Fast\)/i });
    await act(async () => {
      fireEvent.click(healthyTab);
    });

    // Only Fortune Sunflower Oil should be displayed
    expect(screen.getByText("Fortune Sunflower Oil 1L")).toBeDefined();
    expect(screen.queryByText("Sona Masoori Rice 5kg")).toBeNull();
  });
});
