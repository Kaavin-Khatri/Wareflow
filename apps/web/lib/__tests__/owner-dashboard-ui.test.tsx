import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import DashboardPage from "@/app/dashboard/page";
import { apiClient } from "@/lib/api-client";

// Mock Next Navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
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

// Mock AutoAnimate
vi.mock("@formkit/auto-animate/react", () => ({
  useAutoAnimate: () => [{ current: null }],
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

// Mock matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

const mockDashboardResponse = {
  kpi_metrics: {
    monthly_sales_revenue: 540000,
    monthly_inventory_value: 1350000,
    monthly_inventory_units: 1100,
    total_stock_value: 1350000,
    open_pos_count: 3,
    open_sos_count: 7,
    low_stock_count: 2,
    critical_stock_count: 1,
    total_outstanding_receivables: 340000,
    overdue_invoices_count: 2,
  },
  top_fastest_moving: [
    {
      product_id: "prod-1",
      product_name: "Basmati Premium Rice 25kg",
      sku: "RIC-BAS-025",
      units_moved: 300,
      revenue: 540000,
      category_name: "Grains & Cereals",
    },
  ],
  top_dead_stock: [
    {
      product_id: "prod-dead-1",
      product_name: "Legacy Jaggery Block 10kg",
      sku: "JAG-LEG-010",
      units_on_hand: 50,
      tied_up_capital: 85000,
      days_inactive: 75,
    },
  ],
  movement_trend_30d: [
    { date: "2026-08-01", inbound_qty: 150, outbound_qty: 80 },
    { date: "2026-08-02", inbound_qty: 200, outbound_qty: 120 },
  ],
  low_stock_quick_list: [
    {
      product_id: "prod-sugar",
      product_name: "Organic Sugar 50kg",
      sku: "SUG-ORG-050",
      current_stock: 0,
      reorder_point: 20,
      urgency: "critical",
      primary_supplier_name: "Agro Prime Commodities Ltd",
      deficit: 20,
    },
    {
      product_id: "prod-oil",
      product_name: "Sunflower Refined Oil 15L",
      sku: "OIL-SUN-015",
      current_stock: 5,
      reorder_point: 20,
      urgency: "high",
      primary_supplier_name: "Agro Prime Commodities Ltd",
      deficit: 15,
    },
  ],
  overdue_invoices_quick_list: [
    {
      invoice_id: "inv-1",
      invoice_number: "INV/2026-27/0001",
      retailer_name: "Vashi APMC Wholesale Traders",
      due_date: "2026-08-10",
      overdue_days: 11,
      balance_due: 340000,
      status: "unpaid",
    },
  ],
  is_empty_state: false,
};

const mockEmptyDashboardResponse = {
  kpi_metrics: {
    monthly_sales_revenue: 0,
    monthly_inventory_value: 0,
    monthly_inventory_units: 0,
    total_stock_value: 0,
    open_pos_count: 0,
    open_sos_count: 0,
    low_stock_count: 0,
    critical_stock_count: 0,
    total_outstanding_receivables: 0,
    overdue_invoices_count: 0,
  },
  top_fastest_moving: [],
  top_dead_stock: [],
  movement_trend_30d: [],
  low_stock_quick_list: [],
  overdue_invoices_quick_list: [],
  is_empty_state: true,
};

const mockWeeklyInsight = {
  headline: "Revenue Momentum +18.4% with Grains Leading Volume",
  narrative: "Wholesale dispatches showed steady acceleration across Bhiwandi Hub terminals.",
  metrics_summary: {
    weekly_revenue: 845200,
    weekly_orders_count: 42,
    confirmed_orders_count: 38,
    top_mover_product_name: "Basmati Premium Rice 25kg",
    top_mover_units_sold: 450,
    reorder_needed_count: 3,
    dead_stock_count: 2,
    dead_stock_capital: 120000,
  },
  generated_at: "2026-08-19T06:00:00Z",
  expires_at: "2026-08-26T06:00:00Z",
  is_ai_generated: true,
  is_cached: true,
};

describe("Owner Analytics Dashboard UI (Step 15.1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render owner dashboard KPI metrics, 30d movement chart, and quick lists", async () => {
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes("/analytics/dashboard")) {
        return Promise.resolve(mockDashboardResponse);
      }
      if (url.includes("/analytics/weekly-insight")) {
        return Promise.resolve(mockWeeklyInsight);
      }
      return Promise.reject(new Error("Not found"));
    });

    render(<DashboardPage />);

    // Verify Title
    expect(screen.getByText("Owner Wholesale Command Center")).toBeDefined();

    // Verify KPI metric cards
    await waitFor(() => {
      expect(screen.getByText(/Total Inventory Valuation/i)).toBeDefined();
      expect(screen.getByText(/Stock Alert Status/i)).toBeDefined();
      expect(screen.getByText(/Outstanding Receivables/i)).toBeDefined();
    });

    // Verify 30-Day Movement Chart container
    expect(screen.getByText(/30-Day Inventory Movement Velocity/i)).toBeDefined();

    // Verify Top Velocity Movers
    expect(screen.getByText("Top Velocity Products (30 Days)")).toBeDefined();
    expect(screen.getByText("Basmati Premium Rice 25kg")).toBeDefined();
    expect(screen.getByText("RIC-BAS-025 • Grains & Cereals")).toBeDefined();

    // Verify Dead Stock Risks
    expect(screen.getByText("Dead Stock Capital Risk (60+ Days)")).toBeDefined();
    expect(screen.getByText("Legacy Jaggery Block 10kg")).toBeDefined();

    // Verify Low Stock Quick List widget
    expect(screen.getByText("Low Stock Quick Action")).toBeDefined();
    expect(screen.getByText("Organic Sugar 50kg")).toBeDefined();
    expect(screen.getByText("Sunflower Refined Oil 15L")).toBeDefined();
    expect(
      screen.getAllByText(/Supplier: Agro Prime Commodities Ltd/i).length,
    ).toBeGreaterThanOrEqual(1);

    // Verify Overdue Receivables Queue widget
    expect(screen.getByText("Overdue Receivables Queue")).toBeDefined();
    expect(screen.getAllByText("Vashi APMC Wholesale Traders").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/11d Overdue/i)).toBeDefined();

    // Verify AI Executive Intelligence Briefing
    expect(screen.getByText("AI Executive Intelligence Briefing")).toBeDefined();
    expect(screen.getByText(/Revenue Momentum \+18.4%/i)).toBeDefined();
  });

  it("should render guided EmptyState on fresh deployment with zero data", async () => {
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes("/analytics/dashboard")) {
        return Promise.resolve(mockEmptyDashboardResponse);
      }
      if (url.includes("/analytics/weekly-insight")) {
        return Promise.resolve(null);
      }
      return Promise.reject(new Error("Not found"));
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Fresh Deployment Initialized")).toBeDefined();
      expect(screen.getByText(/Your wholesale warehouse environment is ready/i)).toBeDefined();
      expect(screen.getByText("Add Catalog Products")).toBeDefined();
    });
  });
});
