/**
 * Frontend Unit Tests for Step 14.3: Anomaly Detection Badges & AI Executive Insight Narratives.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import SalesOrdersAdminPage, { SalesOrder } from "@/app/admin/sales-orders/page";
import DashboardPage from "@/app/dashboard/page";
import { apiClient } from "@/lib/api-client";

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

// Mock AutoAnimate
vi.mock("@formkit/auto-animate/react", () => ({
  useAutoAnimate: () => [{ current: null }],
}));

// Mock apiClient
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

const mockAnomalousOrders: SalesOrder[] = [
  {
    id: "so-anom-1",
    so_number: "SO-202608-0099",
    buyer_type: "retailer",
    retailer_id: "ret-1",
    retailer_name: "Apex Kirana Stores",
    retailer_pricing_tier: "gold",
    status: "draft",
    order_date: "2026-08-19T10:00:00Z",
    total_amount: 150000.0,
    created_at: "2026-08-19T10:00:00Z",
    has_unusual_items: true,
    unusual_items_count: 1,
    anomaly_warnings: [
      "Royal Basmati Rice 5kg: Ordered qty 300 exceeds normal 3σ threshold (45.2)",
    ],
    items: [
      {
        id: "so-item-anom",
        so_id: "so-anom-1",
        product_id: "prod-1",
        product_name: "Royal Basmati Rice 5kg",
        product_sku: "RIC-BAS-001",
        qty: 300,
        unit_price: 500.0,
        line_total: 150000.0,
        is_unusual: true,
        anomaly_reason: "Ordered qty 300 exceeds normal 3σ threshold (45.2)",
        historical_mean: 20.0,
        historical_stddev: 8.4,
      },
    ],
  },
];

const mockWeeklyInsight = {
  headline: "Weekly Pulse: ₹75,000 Revenue Across 2 Orders",
  narrative:
    "Wholesale operations recorded ₹75,000 in gross revenue with 2 confirmed orders. Premium Tea was the volume driver while reorder thresholds were maintained.",
  metrics_summary: {
    weekly_revenue: 75000.0,
    weekly_orders_count: 2,
    confirmed_orders_count: 2,
    top_mover_product_name: "Premium Tea 500g",
    top_mover_units_sold: 100.0,
    reorder_needed_count: 1,
    dead_stock_count: 2,
    dead_stock_capital: 35000.0,
  },
  generated_at: "2026-08-19T10:00:00Z",
  expires_at: "2026-08-26T10:00:00Z",
  is_ai_generated: true,
  is_cached: true,
};

describe("Sales Orders Anomaly Detection UI (Step 14.3)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
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

  it("renders unusual order size warning pill in the sales orders table", async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === "/sales-orders") return Promise.resolve(mockAnomalousOrders);
      if (url === "/retailers") return Promise.resolve([]);
      if (url === "/products") return Promise.resolve([]);
      if (url === "/customers") return Promise.resolve([]);
      return Promise.resolve([]);
    });

    render(<SalesOrdersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("SO-202608-0099").length).toBeGreaterThanOrEqual(1);
    });

    // Anomaly pill should be visible in table
    expect(screen.getAllByText(/Unusual Size/i).length).toBeGreaterThanOrEqual(1);
  });

  it("displays statistical anomaly advisory banner and 3σ tag in order detail modal", async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === "/sales-orders") return Promise.resolve(mockAnomalousOrders);
      if (url.includes("/delivery")) return Promise.resolve(null);
      return Promise.resolve([]);
    });

    render(<SalesOrdersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("SO-202608-0099").length).toBeGreaterThanOrEqual(1);
    });

    // Click Details button
    const detailButtons = screen.getAllByRole("button", { name: /Details/i });
    fireEvent.click(detailButtons[0]);

    await waitFor(() => {
      expect(
        screen.getAllByText("Statistical Anomaly Advisory (3σ Threshold)").length,
      ).toBeGreaterThanOrEqual(1);
    });

    expect(screen.getAllByText(/exceeds normal 3σ threshold/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/3σ Anomaly/i).length).toBeGreaterThanOrEqual(1);
  });
});

describe("Dashboard AI Weekly Executive Briefing UI (Step 14.3)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
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

  it("renders AI Weekly Executive Briefing card with grounded narrative and metrics chips", async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes("/analytics/weekly-insight")) {
        return Promise.resolve(mockWeeklyInsight);
      }
      return Promise.resolve([]);
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(
        screen.getAllByText("AI Executive Intelligence Briefing").length,
      ).toBeGreaterThanOrEqual(1);
    });

    expect(
      screen.getAllByText("Weekly Pulse: ₹75,000 Revenue Across 2 Orders").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText(/Wholesale operations recorded ₹75,000/i).length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Groq LLM Powered").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("7d Cached").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("7D Sales Revenue").length).toBeGreaterThanOrEqual(1);
  });
});
