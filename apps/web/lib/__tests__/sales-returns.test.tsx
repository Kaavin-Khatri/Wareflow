/**
 * Frontend Unit Tests for Retailer Returns (RMA In) Admin View (Step 8.3).
 *
 * Tests:
 * 1. Renders KPI cards, condition breakdowns, and returns table
 * 2. Filters by search query and status tabs
 * 3. Creates new RMA return request with condition assessments
 * 4. Inspects return detail and approves return (restocks resellable)
 * 5. Rejects return request
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import SalesReturnsPage, { SalesReturn } from "@/app/admin/sales-returns/page";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/sales-returns",
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

const mockReturns: SalesReturn[] = [
  {
    id: "ret-1",
    sales_order_id: "so-1",
    so_number: "SO-202608-0001",
    retailer_id: "ret-apex",
    retailer_name: "Apex Kirana Stores",
    status: "requested",
    reason: "Damaged packaging in transit",
    credit_adjustment_amount: 1350.0,
    requested_at: "2026-08-18T10:00:00Z",
    items: [
      {
        id: "ri-1",
        return_id: "ret-1",
        product_id: "prod-1",
        product_name: "Royal Basmati Rice 5kg",
        product_sku: "RIC-BAS-001",
        qty: 3,
        batch_id: "batch-1",
        batch_no: "B-2026-001",
        condition: "resellable",
        unit_price: 450.0,
        refund_amount: 1350.0,
      },
    ],
  },
  {
    id: "ret-2",
    sales_order_id: "so-2",
    so_number: "SO-202608-0002",
    retailer_id: "ret-metro",
    retailer_name: "Metro Retail Mart",
    status: "approved",
    reason: "Expired stock sent",
    credit_adjustment_amount: 2000.0,
    requested_at: "2026-08-17T10:00:00Z",
    items: [
      {
        id: "ri-2",
        return_id: "ret-2",
        product_id: "prod-2",
        product_name: "Organic Whole Wheat 10kg",
        product_sku: "WHT-ORG-010",
        qty: 4,
        batch_id: "batch-2",
        batch_no: "B-2026-002",
        condition: "damaged",
        unit_price: 500.0,
        refund_amount: 2000.0,
      },
    ],
  },
];

const mockOrders = [
  {
    id: "so-1",
    so_number: "SO-202608-0001",
    retailer_id: "ret-apex",
    retailer_name: "Apex Kirana Stores",
    status: "delivered",
    items: [
      {
        id: "so-it-1",
        product_id: "prod-1",
        product_name: "Royal Basmati Rice 5kg",
        product_sku: "RIC-BAS-001",
        qty: 10,
        unit_price: 450.0,
        batch_id: "batch-1",
      },
    ],
  },
];

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

describe("SalesReturnsPage (Step 8.3)", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const { apiClient } = await import("@/lib/api-client");
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes("/sales-returns")) return Promise.resolve(mockReturns);
      if (url.includes("/sales-orders")) return Promise.resolve(mockOrders);
      return Promise.resolve([]);
    });
    vi.mocked(apiClient.post).mockImplementation((url: string, body: unknown) => {
      return Promise.resolve({
        id: "ret-new-3",
        status: "requested",
        ...(body as object),
      });
    });
    vi.mocked(apiClient.patch).mockImplementation((url: string) => {
      if (url.includes("/approve")) {
        return Promise.resolve({ ...mockReturns[0], status: "approved" });
      }
      if (url.includes("/reject")) {
        return Promise.resolve({ ...mockReturns[0], status: "rejected" });
      }
      return Promise.resolve({});
    });
  });

  it("renders KPI cards, metrics, and returns list", async () => {
    render(<SalesReturnsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Retailer Returns (RMA In)").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Metro Retail Mart").length).toBeGreaterThanOrEqual(1);
    });

    // Check KPI titles
    expect(screen.getAllByText("Total RMA Returns").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Pending Approvals").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Resellable Restocked").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Damaged Write-offs").length).toBeGreaterThanOrEqual(1);
  });

  it("filters returns by search query and status tabs", async () => {
    render(<SalesReturnsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
    });

    // Filter by search query
    const searchInput = screen.getByPlaceholderText(/Search/i);
    fireEvent.change(searchInput, { target: { value: "Apex" } });

    expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("Metro Retail Mart")).toBeNull();

    // Reset search
    fireEvent.change(searchInput, { target: { value: "" } });

    // Filter by Status Tab
    const requestedTab = screen.getByRole("button", { name: "Requested" });
    fireEvent.click(requestedTab);

    expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("Metro Retail Mart")).toBeNull();
  });

  it("opens create RMA return modal and submits new return", async () => {
    const { apiClient } = await import("@/lib/api-client");
    render(<SalesReturnsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
    });

    const createBtn = screen.getByRole("button", { name: /Request RMA Return/i });
    fireEvent.click(createBtn);

    expect(screen.getAllByText("Request Inbound Retailer Return (RMA In)").length).toBeGreaterThanOrEqual(1);

    // Select sales order
    const orderSelect = screen.getByLabelText(/Select Sales Order \*/i);
    fireEvent.change(orderSelect, { target: { value: "so-1" } });

    // Enter reason
    const reasonInput = screen.getByLabelText(/Reason for Return/i);
    fireEvent.change(reasonInput, { target: { value: "Overstock return" } });

    // Submit form
    const submitBtn = screen.getByRole("button", { name: /Create RMA Return/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/sales-returns",
        expect.objectContaining({
          sales_order_id: "so-1",
          reason: "Overstock return",
        })
      );
    });
  });

  it("opens detail modal and approves return with condition-based restocking", async () => {
    const { apiClient } = await import("@/lib/api-client");
    render(<SalesReturnsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
    });

    // Click details button on first row
    const detailButtons = screen.getAllByRole("button", { name: /Details/i });
    fireEvent.click(detailButtons[0]);

    expect(screen.getAllByText("Sales Return Inspection (RMA In)").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Returned Items Breakdown").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Total Estimated Credit Adjustment:").length).toBeGreaterThanOrEqual(1);

    // Click Approve
    const approveBtn = screen.getByRole("button", { name: /Approve \(Restock Resellable\)/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(apiClient.patch).toHaveBeenCalledWith("/sales-returns/ret-1/approve", {});
    });
  });

  it("opens detail modal and rejects return", async () => {
    const { apiClient } = await import("@/lib/api-client");
    render(<SalesReturnsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
    });

    const detailButtons = screen.getAllByRole("button", { name: /Details/i });
    fireEvent.click(detailButtons[0]);

    const rejectBtn = screen.getByRole("button", { name: /Reject Return/i });
    fireEvent.click(rejectBtn);

    await waitFor(() => {
      expect(apiClient.patch).toHaveBeenCalledWith(
        "/sales-returns/ret-1/reject",
        expect.objectContaining({
          status: "rejected",
        })
      );
    });
  });
});
