import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import BatchRecallsPage from "@/app/admin/stock/recalls/page";
import { apiClient } from "@/lib/api-client";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/stock/recalls",
  useSearchParams: () => new URLSearchParams(),
}));

const MOCK_RECALLS_RESPONSE = {
  items: [
    {
      id: "rec-1",
      batch_id: "batch-101",
      batch_no: "BATCH-2026-0801",
      product_id: "prod-1",
      product_name: "Organic Whole Milk 1L",
      product_sku: "MILK-ORG-001",
      warehouse_name: "Central Cold Storage",
      remaining_quantity: 45.0,
      reason: "Packaging seal integrity issue",
      severity: "critical",
      status: "initiated",
      initiated_at: "2026-08-10T10:00:00Z",
      resolved_at: null,
      affected_orders_count: 2,
      notified_count: 0,
    },
  ],
  total: 1,
  page: 1,
  page_size: 100,
  pages: 1,
};

const MOCK_RECALL_DETAIL = {
  id: "rec-1",
  batch_id: "batch-101",
  batch_no: "BATCH-2026-0801",
  product_id: "prod-1",
  product_name: "Organic Whole Milk 1L",
  product_sku: "MILK-ORG-001",
  warehouse_id: "wh-1",
  warehouse_name: "Central Cold Storage",
  remaining_quantity: 45.0,
  reason: "Packaging seal integrity issue",
  severity: "critical",
  status: "initiated",
  initiated_at: "2026-08-10T10:00:00Z",
  resolved_at: null,
  affected_orders_count: 2,
  notified_count: 0,
  affected_orders: [
    {
      id: "aff-1",
      sales_order_id: "so-101",
      sales_order_number: "SO-101",
      buyer_type: "retailer",
      buyer_name: "Fresh Mart Retail",
      buyer_phone: "+919876543210",
      buyer_email: "freshmart@example.com",
      order_date: "2026-08-08T12:00:00Z",
      quantity_supplied: 25.0,
      notified_at: null,
    },
  ],
};

// Mock apiClient
vi.mock("@/lib/api-client", () => ({
  getAuthToken: async () => "test_token",
  apiClient: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url === "/products") {
        return Promise.resolve([
          { id: "prod-1", name: "Organic Whole Milk 1L", sku: "MILK-ORG-001" },
        ]);
      }
      if (url.startsWith("/products/prod-1/stock")) {
        return Promise.resolve({
          batches: [
            {
              id: "batch-101",
              product_id: "prod-1",
              warehouse_id: "wh-1",
              batch_no: "BATCH-2026-0801",
              quantity: 45.0,
            },
          ],
        });
      }
      if (url.startsWith("/stock/recalls/rec-1")) {
        return Promise.resolve(MOCK_RECALL_DETAIL);
      }
      if (url.startsWith("/stock/recalls")) {
        return Promise.resolve(MOCK_RECALLS_RESPONSE);
      }
      return Promise.resolve([]);
    }),
    post: vi.fn().mockImplementation((url: string, body: { reason?: string }) => {
      if (url === "/stock/recalls") {
        return Promise.resolve({
          ...MOCK_RECALL_DETAIL,
          id: "rec-new",
          reason: body.reason || "Test defect",
        });
      }
      return Promise.resolve({});
    }),
    patch: vi.fn().mockImplementation((url: string) => {
      if (url.includes("/notify")) {
        return Promise.resolve({
          status: "notifying",
          retailers_notified_count: 1,
          customers_notified_count: 0,
          notified_at: new Date().toISOString(),
        });
      }
      if (url.includes("/resolve")) {
        return Promise.resolve({
          ...MOCK_RECALL_DETAIL,
          status: "resolved",
          resolved_at: new Date().toISOString(),
        });
      }
      return Promise.resolve({});
    }),
  },
}));

describe("Batch Recalls & Traceability UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the recall dashboard with KPIs and list items", async () => {
    render(<BatchRecallsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Batch Recall & Traceability").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Total Recalls")).toBeDefined();
      expect(screen.getByText("Active Quarantines")).toBeDefined();
      expect(screen.getByText("Affected Orders Traced")).toBeDefined();
      expect(screen.getByText("Retailers Alerted")).toBeDefined();
      expect(screen.getAllByText("Organic Whole Milk 1L").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("BATCH-2026-0801").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("opens create modal and initiates a new batch recall", async () => {
    render(<BatchRecallsPage />);

    await waitFor(() => {
      expect(screen.getByText("Initiate Batch Recall")).toBeDefined();
    });

    fireEvent.click(screen.getByText("Initiate Batch Recall"));

    await waitFor(() => {
      expect(screen.getByLabelText(/Product to Recall \*/i)).toBeDefined();
    });

    // Select Product
    fireEvent.change(screen.getByLabelText(/Product to Recall \*/i), {
      target: { value: "prod-1" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText(/Defective Stock Batch \*/i)).toBeDefined();
    });

    // Enter Reason
    fireEvent.change(screen.getByLabelText(/Root Cause \/ Recall Reason \*/i), {
      target: { value: "Seal integrity failure in batch testing" },
    });

    // Submit
    const submitBtn = screen.getByRole("button", { name: /Initiate Recall & Trace Orders/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/stock/recalls",
        expect.objectContaining({
          batch_id: "batch-101",
          reason: "Seal integrity failure in batch testing",
          severity: "critical",
        }),
      );
    });
  });

  it("opens recall details and broadcasts alerts to affected retailers", async () => {
    render(<BatchRecallsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Trace & Alert").length).toBeGreaterThanOrEqual(1);
    });

    // Click Trace & Alert
    fireEvent.click(screen.getAllByText("Trace & Alert")[0]);

    await waitFor(() => {
      expect(screen.getByText(/Batch Traceability: BATCH-2026-0801/i)).toBeDefined();
      expect(screen.getByText("Fresh Mart Retail")).toBeDefined();
      expect(screen.getByText(/Broadcast Recall Alerts \(WhatsApp \+ Email\)/i)).toBeDefined();
    });

    // Broadcast Alerts
    fireEvent.click(screen.getByText(/Broadcast Recall Alerts \(WhatsApp \+ Email\)/i));

    await waitFor(() => {
      expect(apiClient.patch).toHaveBeenCalledWith("/stock/recalls/rec-1/notify", {});
    });
  });
});
