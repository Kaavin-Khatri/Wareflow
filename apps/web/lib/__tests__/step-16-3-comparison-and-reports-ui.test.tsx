/**
 * Frontend Vitest tests for Step 16.3:
 * - ComparisonBadge component (pure delta rendering, polarity inversion, zero handling)
 * - AnalyticsLandingPage (8 specialized report hubs, live scorecard with badges, executive summary, PDF download, and send-now)
 */

import React from "react";
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { ComparisonBadge } from "@/components/analytics/ComparisonBadge";
import AnalyticsLandingPage from "@/app/admin/analytics/page";
import { apiClient } from "@/lib/api-client";

beforeAll(() => {
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
});

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/analytics",
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
    post: vi.fn(),
    downloadBlob: vi.fn(),
  },
}));

const mockComparisonsResponse = {
  period: "30d",
  as_of: "2026-08-24T12:00:00Z",
  metrics: {
    revenue: {
      metric_key: "revenue",
      metric_label: "Wholesale Revenue",
      current_value: 500000.0,
      prior_value: 400000.0,
      delta_value: 100000.0,
      delta_pct: 25.0,
      trend: "up",
      is_positive: true,
      higher_is_better: true,
      period_label: "vs prior 30d",
      formatted_current: "₹5,00,000",
      formatted_prior: "₹4,00,000",
    },
    gross_margin: {
      metric_key: "gross_margin",
      metric_label: "Gross Profit Margin",
      current_value: 28.5,
      prior_value: 25.0,
      delta_value: 3.5,
      delta_pct: 14.0,
      trend: "up",
      is_positive: true,
      higher_is_better: true,
      period_label: "vs prior 30d",
      formatted_current: "28.5%",
      formatted_prior: "25.0%",
    },
    stock_valuation: {
      metric_key: "stock_valuation",
      metric_label: "Inventory Valuation",
      current_value: 1250000.0,
      prior_value: 1200000.0,
      delta_value: 500000.0,
      delta_pct: 4.17,
      trend: "up",
      is_positive: true,
      higher_is_better: true,
      period_label: "vs prior 30d",
      formatted_current: "₹12,50,000",
      formatted_prior: "₹12,00,000",
    },
    turnover_rate: {
      metric_key: "turnover_rate",
      metric_label: "Turnover Velocity",
      current_value: 4.2,
      prior_value: 3.8,
      delta_value: 0.4,
      delta_pct: 10.53,
      trend: "up",
      is_positive: true,
      higher_is_better: true,
      period_label: "vs prior 30d",
      formatted_current: "4.20x",
      formatted_prior: "3.80x",
    },
    units_sold: {
      metric_key: "units_sold",
      metric_label: "Units Sold",
      current_value: 1500.0,
      prior_value: 1200.0,
      delta_value: 300.0,
      delta_pct: 25.0,
      trend: "up",
      is_positive: true,
      higher_is_better: true,
      period_label: "vs prior 30d",
      formatted_current: "1,500",
      formatted_prior: "1,200",
    },
    shrinkage_value: {
      metric_key: "shrinkage_value",
      metric_label: "Shrinkage & Damage",
      current_value: 8500.0,
      prior_value: 12000.0,
      delta_value: -3500.0,
      delta_pct: -29.17,
      trend: "down",
      is_positive: true,
      higher_is_better: false,
      period_label: "vs prior 30d",
      formatted_current: "₹8,500",
      formatted_prior: "₹12,000",
    },
  },
};

const mockWeeklyReportResponse = {
  report_id: "REP-202634-AB12CD34",
  start_date: "2026-08-17",
  end_date: "2026-08-24",
  period_label: "17 Aug – 24 Aug 2026",
  generated_at: "2026-08-24T02:30:00Z",
  revenue_inr: 500000.0,
  revenue_delta_pct: 25.0,
  gross_margin_pct: 28.5,
  gross_margin_delta_pct: 14.0,
  total_stock_valuation_inr: 1250000.0,
  turnover_ratio_30d: 4.2,
  low_stock_count: 3,
  overdue_invoices_count: 2,
  overdue_amount_inr: 45000.0,
  shrinkage_inr: 8500.0,
  top_fast_movers: [
    {
      product_id: "prod-1",
      name: "Basmati Rice Royal 5kg",
      sku: "RICE-5KG",
      revenue: 120000.0,
      units: 400.0,
    },
    {
      product_id: "prod-2",
      name: "Refined Sunflower Oil 1L",
      sku: "OIL-1L",
      revenue: 85000.0,
      units: 600.0,
    },
  ],
  top_slow_movers: [
    {
      product_id: "prod-3",
      name: "Stagnant Exotic Spice 100g",
      sku: "SPICE-100G",
      on_hand: 250.0,
      tied_up_capital: 35000.0,
    },
  ],
  highlights: [
    {
      title: "Top Revenue Driver",
      description: "Basmati Rice Royal 5kg generated ₹1,20,000 this week.",
      category: "movers",
      metric_value: "₹1,20,000",
      badge_variant: "success",
    },
    {
      title: "Replenishment Alert",
      description: "3 catalog SKU(s) breached minimum safety stock thresholds.",
      category: "low_stock",
      metric_value: "3 SKUs",
      badge_variant: "warning",
    },
    {
      title: "Accounts Receivable Notice",
      description: "2 invoice(s) overdue for a total outstanding balance of ₹45,000.",
      category: "overdue_ar",
      metric_value: "₹45,000",
      badge_variant: "error",
    },
  ],
  narrative_summary:
    "During the week of 17 Aug – 24 Aug 2026, WareFlow generated gross revenue of ₹5,00,000 with an overall gross margin of 28.5%. Total inventory holding valuation stands at ₹12,50,000. Action items: 3 SKU(s) require replenishment and ₹45,000 is overdue across 2 invoice(s).",
};

describe("Step 16.3: ComparisonBadge Component Tests", () => {
  it("renders positive growth with green indicator when higherIsBetter is true", () => {
    const { container } = render(
      <ComparisonBadge
        deltaPct={15.5}
        currentValue={1155}
        priorValue={1000}
        higherIsBetter={true}
        periodLabel="vs prior month"
      />,
    );

    expect(screen.getByText("+15.5%")).toBeDefined();
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("text-emerald-700");
  });

  it("renders negative decline with red indicator when higherIsBetter is true", () => {
    const { container } = render(
      <ComparisonBadge
        deltaPct={-8.4}
        currentValue={916}
        priorValue={1000}
        higherIsBetter={true}
      />,
    );

    expect(screen.getByText("-8.4%")).toBeDefined();
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("text-rose-700");
  });

  it("inverts polarity for metrics like shrinkage where higher is worse", () => {
    // A drop in shrinkage is favorable (should be emerald green)
    const { container: containerDecrease } = render(
      <ComparisonBadge
        deltaPct={-25.0}
        currentValue={750}
        priorValue={1000}
        higherIsBetter={false}
      />,
    );
    expect(screen.getByText("-25.0%")).toBeDefined();
    const badgeDec = containerDecrease.querySelector("span");
    expect(badgeDec?.className).toContain("text-emerald-700");

    // An increase in shrinkage is unfavorable (should be rose red)
    const { container: containerIncrease } = render(
      <ComparisonBadge
        deltaPct={30.0}
        currentValue={1300}
        priorValue={1000}
        higherIsBetter={false}
      />,
    );
    expect(screen.getByText("+30.0%")).toBeDefined();
    const badgeInc = containerIncrease.querySelector("span");
    expect(badgeInc?.className).toContain("text-rose-700");
  });

  it("renders neutral flat indicator when delta is 0 or undefined", () => {
    const { container: containerZero } = render(<ComparisonBadge deltaPct={0.0} />);
    expect(containerZero.textContent).toContain("0.0%");
    const badgeZero = containerZero.querySelector("span");
    expect(badgeZero?.className).toContain("text-zinc-500");
  });

  it("renders fallback indicator when delta is null", () => {
    const { container: containerNull } = render(<ComparisonBadge deltaPct={null} />);
    expect(containerNull.textContent).toContain("0.0%");
    const badgeNull = containerNull.querySelector("span");
    expect(badgeNull?.className).toContain("text-zinc-500");
  });

  it("displays period label and prior value when flags are enabled", () => {
    render(
      <ComparisonBadge
        deltaPct={12.0}
        currentValue={1120}
        priorValue={1000}
        showPeriodLabel={true}
        showPriorValue={true}
        periodLabel="vs last quarter"
        formatter={(v) => `₹${v.toLocaleString()}`}
      />,
    );

    expect(screen.getByText("vs last quarter")).toBeDefined();
    expect(screen.getByText("(₹1,000)")).toBeDefined();
  });
});

describe("Step 16.3: Central Analytics Landing Hub Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes("/analytics/period-comparisons")) {
        return Promise.resolve(mockComparisonsResponse);
      }
      if (url.includes("/analytics/weekly-report/latest")) {
        return Promise.resolve(mockWeeklyReportResponse);
      }
      return Promise.resolve({});
    });
  });

  it("renders 8 specialized analytics report module cards with direct links", async () => {
    render(<AnalyticsLandingPage />);

    await waitFor(() => {
      expect(screen.getByText("Analytics & Business Intelligence")).toBeDefined();
    });

    // Check all 8 module titles
    expect(screen.getByText("Stock Valuation & Inventory Health")).toBeDefined();
    expect(screen.getByText("Profitability & Product Margins")).toBeDefined();
    expect(screen.getByText("Turnover Velocity & Stock Aging")).toBeDefined();
    expect(screen.getByText("Accounts Receivable (AR) Aging")).toBeDefined();
    expect(screen.getByText("Supplier Performance Scorecards")).toBeDefined();
    expect(screen.getByText("Retailer Performance & Churn Risk")).toBeDefined();
    expect(screen.getByText("Multi-Warehouse Breakdown")).toBeDefined();
    expect(screen.getByText("Shrinkage & Damage Write-offs")).toBeDefined();
  });

  it("renders KPI scorecard with comparison badges from live telemetry", async () => {
    render(<AnalyticsLandingPage />);

    await waitFor(() => {
      expect(screen.getByText("Total Revenue")).toBeDefined();
    });

    // KPI titles
    expect(screen.getByText("Gross Margin")).toBeDefined();
    expect(screen.getByText("Stock Valuation")).toBeDefined();
    expect(screen.getByText("Turnover Velocity")).toBeDefined();
    expect(screen.getByText("Units Sold")).toBeDefined();
    expect(screen.getByText("Shrinkage Loss")).toBeDefined();

    // Check deltas from mock data (+25.0%, +14.0%, -29.2%)
    expect(screen.getAllByText("+25.0%").length).toBeGreaterThan(0);
    expect(screen.getByText("+14.0%")).toBeDefined();
    expect(screen.getByText("-29.2%")).toBeDefined();
  });

  it("renders Weekly Executive Summary card with narrative, alerts, and fast movers", async () => {
    render(<AnalyticsLandingPage />);

    await waitFor(() => {
      expect(screen.getByText("Weekly Executive Summary (17 Aug – 24 Aug 2026)")).toBeDefined();
    });

    // Narrative text
    expect(screen.getByText(/During the week of 17 Aug – 24 Aug 2026/i)).toBeDefined();

    // Alerts
    expect(screen.getByText("Top Revenue Driver")).toBeDefined();
    expect(screen.getByText("Replenishment Alert")).toBeDefined();
    expect(screen.getByText("Accounts Receivable Notice")).toBeDefined();

    // Fast movers & Slow movers
    expect(screen.getByText("Basmati Rice Royal 5kg")).toBeDefined();
    expect(screen.getByText("Stagnant Exotic Spice 100g")).toBeDefined();
  });

  it("triggers PDF download when clicking Weekly PDF button", async () => {
    (apiClient.downloadBlob as any).mockResolvedValue(undefined);

    render(<AnalyticsLandingPage />);

    await waitFor(() => {
      expect(screen.getByText("Weekly PDF")).toBeDefined();
    });

    const downloadBtn = screen.getByRole("button", { name: /Weekly PDF/i });
    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(apiClient.downloadBlob).toHaveBeenCalledWith(
        "/analytics/weekly-report/pdf",
        "WareFlow_Weekly_Executive_Report_2026-08-17.pdf",
      );
    });
  });

  it("triggers Send Report Now dispatch when clicking action button", async () => {
    (apiClient.post as any).mockResolvedValue({
      success: true,
      message: "Dispatched",
      recipients_count: 2,
      channels_used: ["email", "whatsapp", "in_app"],
    });

    render(<AnalyticsLandingPage />);

    await waitFor(() => {
      expect(screen.getByText("Send Report Now")).toBeDefined();
    });

    const sendBtn = screen.getByRole("button", { name: /Send Report Now/i });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith("/analytics/weekly-report/send-now", {
        channels: ["email", "whatsapp", "in_app"],
      });
      expect(screen.getByText(/Report dispatched successfully to 2 recipient\(s\)/i)).toBeDefined();
    });
  });
});
