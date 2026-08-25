/**
 * Frontend Vitest tests for Step 16.2 Analytics:
 * - Suppliers Performance
 * - Retailers Performance
 * - Warehouse Breakdown
 * - Shrinkage & Inventory Loss
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import SupplierPerformancePage from "@/app/admin/analytics/suppliers/page";
import RetailerPerformancePage from "@/app/admin/analytics/retailers/page";
import WarehouseBreakdownPage from "@/app/admin/analytics/warehouses/page";
import ShrinkageAnalyticsPage from "@/app/admin/analytics/shrinkage/page";
import { ThemeProvider } from "@/components/ThemeProvider";
import { apiClient } from "@/lib/api-client";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/analytics/suppliers",
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
  }),
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

// Mock API Client
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

const mockSupplierData = {
  summary: {
    average_on_time_pct: 92.5,
    average_accuracy_pct: 98.0,
    average_return_rate_pct: 1.2,
    total_spend_inr: 450000.0,
    total_suppliers_analyzed: 5,
    excellent_count: 3,
    needs_improvement_count: 1,
  },
  items: [
    {
      supplier_id: "sup-1",
      supplier_name: "Apex FMCG Ltd",
      contact_person: "Rajesh Kumar",
      phone: "9876543210",
      total_pos: 12,
      completed_pos: 10,
      on_time_delivery_pct: 95.0,
      fulfillment_accuracy_pct: 99.0,
      return_rate_pct: 0.5,
      total_spend_inr: 250000.0,
      rating_band: "excellent",
    },
  ],
  generated_at: "2026-08-24T12:00:00Z",
};

const mockRetailerData = {
  summary: {
    total_retailers: 8,
    active_retailers_count: 6,
    churn_risk_count: 2,
    total_portfolio_revenue_inr: 820000.0,
    average_order_value_inr: 15000.0,
  },
  items: [
    {
      retailer_id: "ret-1",
      retailer_name: "Green Valley Mart",
      contact_person: "Amit Sharma",
      phone: "9811122233",
      pricing_tier: "GOLD",
      total_orders: 15,
      total_revenue: 350000.0,
      avg_order_value: 23333.33,
      last_order_date: "2026-08-20",
      days_since_last_order: 4,
      avg_order_gap_days: 8.5,
      frequency_trend: "increasing",
      is_churn_risk: false,
      churn_risk_reason: null,
    },
    {
      retailer_id: "ret-2",
      retailer_name: "Stagnant Supermarket",
      contact_person: "Vijay Gupta",
      phone: "9822233344",
      pricing_tier: "SILVER",
      total_orders: 3,
      total_revenue: 45000.0,
      avg_order_value: 15000.0,
      last_order_date: "2026-06-10",
      days_since_last_order: 75,
      avg_order_gap_days: 12.0,
      frequency_trend: "decreasing",
      is_churn_risk: true,
      churn_risk_reason: "No order in 75 days (exceeds 2x historical average of 12.0d)",
    },
  ],
  generated_at: "2026-08-24T12:00:00Z",
};

const mockWarehouseData = {
  summary: {
    total_warehouses: 2,
    company_total_stock_units: 1500.0,
    company_total_valuation_inr: 950000.0,
    total_30d_inbound_units: 400.0,
    total_30d_outbound_units: 350.0,
  },
  warehouses: [
    {
      warehouse_id: "wh-1",
      warehouse_name: "Central Hub Mumbai",
      location: "Bhiwandi, Maharashtra",
      is_active: true,
      total_products_stored: 45,
      total_stock_units: 1000.0,
      total_stock_value_inr: 650000.0,
      inbound_30d_units: 250.0,
      outbound_30d_units: 220.0,
      movement_count_30d: 84,
      valuation_share_pct: 68.4,
    },
  ],
  generated_at: "2026-08-24T12:00:00Z",
};

const mockShrinkageData = {
  period: "30d",
  group_by: "product",
  summary: {
    total_shrinkage_value_inr: 12500.0,
    total_units_lost: 25.0,
    shrinkage_rate_pct: 1.32,
    damage_incidents_count: 4,
  },
  items: [
    {
      id: "prod-1",
      name: "Royal Basmati Rice 25kg",
      secondary_info: "SKU: RICE-25",
      badge: "Grains & Rice",
      units_lost: 15.0,
      incidents_count: 2,
      shrinkage_value_inr: 7500.0,
      pct_of_total_shrinkage: 60.0,
    },
  ],
  generated_at: "2026-08-24T12:00:00Z",
};

describe("Step 16.2 Analytics Dashboard Pages", () => {
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

    (apiClient.get as any).mockImplementation((url: string) => {
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
      if (url.startsWith("/analytics/supplier-performance")) {
        return Promise.resolve(mockSupplierData);
      }
      if (url.startsWith("/analytics/retailer-performance")) {
        return Promise.resolve(mockRetailerData);
      }
      if (url.startsWith("/analytics/warehouse-breakdown")) {
        return Promise.resolve(mockWarehouseData);
      }
      if (url.startsWith("/analytics/shrinkage")) {
        return Promise.resolve(mockShrinkageData);
      }
      return Promise.resolve({});
    });
  });

  it("should render Supplier Performance page with reliability metrics and vendors", async () => {
    await act(async () => {
      render(
        <ThemeProvider>
          <SupplierPerformancePage />
        </ThemeProvider>,
      );
    });

    expect(screen.getByText("Supplier Reliability & Performance")).toBeDefined();
    expect(await screen.findByText("Apex FMCG Ltd")).toBeDefined();
    expect(screen.getAllByText("★ Excellent").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Fulfillment Accuracy").length).toBeGreaterThanOrEqual(1);
  });

  it("should render Retailer Performance page with churn risk alerts and revenue rankings", async () => {
    await act(async () => {
      render(
        <ThemeProvider>
          <RetailerPerformancePage />
        </ThemeProvider>,
      );
    });

    expect(screen.getByText("Retailer Performance & Churn Risk")).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("Green Valley Mart")).toBeDefined();
      expect(screen.getByText("Stagnant Supermarket")).toBeDefined();
      expect(screen.getByText("Churn Risk")).toBeDefined();
      expect(screen.getByText("Accelerating")).toBeDefined();
    });
  });

  it("should render Warehouse Breakdown page with facility valuations and flow", async () => {
    await act(async () => {
      render(
        <ThemeProvider>
          <WarehouseBreakdownPage />
        </ThemeProvider>,
      );
    });

    expect(screen.getByText("Warehouse Holdings & Throughput Breakdown")).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("Central Hub Mumbai")).toBeDefined();
      expect(screen.getByText("68.4% of total inventory")).toBeDefined();
      expect(screen.getByText("Transfer Stock")).toBeDefined();
    });
  });

  it("should render Shrinkage Analytics page with damage write-offs", async () => {
    await act(async () => {
      render(
        <ThemeProvider>
          <ShrinkageAnalyticsPage />
        </ThemeProvider>,
      );
    });

    expect(screen.getByText("Inventory Shrinkage & Loss Tracking")).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("Royal Basmati Rice 25kg")).toBeDefined();
      expect(screen.getByText("-15 units")).toBeDefined();
      expect(screen.getByText("Product Breakdown")).toBeDefined();
    });
  });
});
