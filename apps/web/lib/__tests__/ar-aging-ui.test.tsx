/**
 * Frontend Unit Tests for Step 15.2: Accounts-Receivable (AR) Aging Report UI.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import ARAgingReportPage, { ARAgingReportResponse } from "@/app/admin/analytics/ar-aging/page";
import { apiClient } from "@/lib/api-client";

// Mock Next Navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/analytics/ar-aging",
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

// Mock ResizeObserver
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

const mockARAgingReport: ARAgingReportResponse = {
  as_of_date: "2026-08-24",
  summary: {
    total_current: 100000.0,
    total_bucket_1_30: 40000.0,
    total_bucket_31_60: 75000.0,
    total_bucket_61_90: 60000.0,
    total_bucket_90_plus: 90000.0,
    total_overdue: 265000.0,
    total_outstanding: 365000.0,
    total_retailers: 3,
    overdue_retailers_count: 2,
  },
  retailers: [
    {
      retailer_id: "ret-1",
      retailer_name: "Vashi APMC Wholesale Traders",
      contact_person: "Ramesh Patel",
      phone: "+919820011223",
      credit_limit: 500000.0,
      credit_balance: 215000.0,
      current: 100000.0,
      bucket_1_30: 40000.0,
      bucket_31_60: 75000.0,
      bucket_61_90: 0.0,
      bucket_90_plus: 0.0,
      total_overdue: 115000.0,
      total_outstanding: 215000.0,
      oldest_invoice_date: "2026-06-10",
      invoice_count: 3,
    },
    {
      retailer_id: "ret-2",
      retailer_name: "Surat Agro Mart",
      contact_person: "Kiran Shah",
      phone: "+919820044556",
      credit_limit: 300000.0,
      credit_balance: 150000.0,
      current: 0.0,
      bucket_1_30: 0.0,
      bucket_31_60: 0.0,
      bucket_61_90: 60000.0,
      bucket_90_plus: 90000.0,
      total_overdue: 150000.0,
      total_outstanding: 150000.0,
      oldest_invoice_date: "2026-03-16",
      invoice_count: 2,
    },
    {
      retailer_id: "ret-3",
      retailer_name: "Pune Zero Balance Retailers",
      contact_person: "Anil Deshmukh",
      phone: "+919820077889",
      credit_limit: 200000.0,
      credit_balance: 0.0,
      current: 0.0,
      bucket_1_30: 0.0,
      bucket_31_60: 0.0,
      bucket_61_90: 0.0,
      bucket_90_plus: 0.0,
      total_overdue: 0.0,
      total_outstanding: 0.0,
      oldest_invoice_date: null,
      invoice_count: 0,
    },
  ],
  generated_at: "2026-08-24T10:00:00Z",
};

const mockEmptyARAgingReport: ARAgingReportResponse = {
  as_of_date: "2026-08-24",
  summary: {
    total_current: 0.0,
    total_bucket_1_30: 0.0,
    total_bucket_31_60: 0.0,
    total_bucket_61_90: 0.0,
    total_bucket_90_plus: 0.0,
    total_overdue: 0.0,
    total_outstanding: 0.0,
    total_retailers: 0,
    overdue_retailers_count: 0,
  },
  retailers: [],
  generated_at: "2026-08-24T10:00:00Z",
};

describe("Accounts-Receivable Aging Report UI (Step 15.2)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render page header, top 6 aging KPI cards, distribution bar, and bucketed rows", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockARAgingReport);

    render(<ARAgingReportPage />);

    // Verify Title
    expect(screen.getByText("Accounts-Receivable Aging Report")).toBeDefined();

    // Verify KPI Summary Cards and Live Date Badge
    await waitFor(() => {
      expect(screen.getByText(/2026-08-24/i)).toBeDefined();
      expect(screen.getByText("Total Outstanding")).toBeDefined();
      expect(screen.getByText("Current (Within Terms)")).toBeDefined();
      expect(screen.getByText("1–30 Days Overdue")).toBeDefined();
      expect(screen.getByText("31–60 Days Overdue")).toBeDefined();
      expect(screen.getByText("61–90 Days Overdue")).toBeDefined();
      expect(screen.getByText("90+ Days (Critical)")).toBeDefined();
    });

    // Verify Visual Distribution Header
    expect(screen.getByText("Portfolio Debt Aging Distribution")).toBeDefined();

    // Verify Retailer Table Data
    expect(screen.getByText("Vashi APMC Wholesale Traders")).toBeDefined();
    expect(screen.getByText("Surat Agro Mart")).toBeDefined();
    expect(screen.getByText("Pune Zero Balance Retailers")).toBeDefined();

    // Verify Ledger Action Links
    const ledgerButtons = screen.getAllByRole("button", { name: /Ledger/i });
    expect(ledgerButtons.length).toBeGreaterThanOrEqual(3);

    // Verify retailer row link to ledger
    const vashiLink = screen.getByRole("link", { name: /Vashi APMC Wholesale Traders/i });
    expect(vashiLink.getAttribute("href")).toBe("/admin/retailers/ret-1/ledger");
  });

  it("should filter retailers when searching by name or contact", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockARAgingReport);

    render(<ARAgingReportPage />);

    await waitFor(() => {
      expect(screen.getByText("Vashi APMC Wholesale Traders")).toBeDefined();
    });

    // Search for "Surat"
    const searchInput = screen.getByPlaceholderText(/Search by retailer name, contact, phone.../i);
    fireEvent.change(searchInput, { target: { value: "Surat" } });

    expect(screen.getByText("Surat Agro Mart")).toBeDefined();
    expect(screen.queryByText("Vashi APMC Wholesale Traders")).toBeNull();
    expect(screen.queryByText("Pune Zero Balance Retailers")).toBeNull();
  });

  it("should filter by 90+ Days bucket and toggle Hide Zero Balance", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockARAgingReport);

    render(<ARAgingReportPage />);

    await waitFor(() => {
      expect(screen.getByText("Pune Zero Balance Retailers")).toBeDefined();
    });

    // Toggle "Hide Zero Balance"
    const hideZeroCheckbox = screen.getByRole("checkbox");
    fireEvent.click(hideZeroCheckbox);

    // Zero balance retailer is now hidden
    expect(screen.queryByText("Pune Zero Balance Retailers")).toBeNull();
    expect(screen.getByText("Vashi APMC Wholesale Traders")).toBeDefined();
    expect(screen.getByText("Surat Agro Mart")).toBeDefined();

    // Click "90+ Days" filter button
    const criticalButton = screen.getByRole("button", { name: /90\+ Days/i });
    fireEvent.click(criticalButton);

    // Only Surat Agro Mart has 90+ days overdue
    expect(screen.getByText("Surat Agro Mart")).toBeDefined();
    expect(screen.queryByText("Vashi APMC Wholesale Traders")).toBeNull();
  });

  it("should render clean EmptyState on fresh deployment with zero data", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockEmptyARAgingReport);

    render(<ARAgingReportPage />);

    await waitFor(() => {
      expect(screen.getByText("No Matching Retailer Accounts")).toBeDefined();
    });
  });
});
