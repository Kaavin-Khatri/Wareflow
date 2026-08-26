import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import StockTransferPage from "@/app/admin/stock/transfer/page";
import { apiClient } from "@/lib/api-client";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/stock/transfer",
  useSearchParams: () => new URLSearchParams(),
}));

const MOCK_TRANSFERS_RESPONSE = {
  items: [
    {
      id: "trf-1",
      product_id: "prod-1",
      product_name: "Organic Whole Milk 1L",
      product_sku: "MILK-ORG-001",
      from_warehouse_id: "wh-1",
      from_warehouse_name: "Central Cold Storage",
      to_warehouse_id: "wh-2",
      to_warehouse_name: "North Logistics Hub",
      batch_no: "BATCH-2026-0801",
      quantity: 100,
      created_by: "operations@wareflow.io",
      created_at: "2026-08-10T10:00:00Z",
      notes: "Regional buffer stock redistribution",
    },
  ],
  total: 1,
  page: 1,
  page_size: 50,
  pages: 1,
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
      if (url === "/stock/warehouses") {
        return Promise.resolve([
          { id: "wh-1", name: "Central Cold Storage", is_active: true },
          { id: "wh-2", name: "North Logistics Hub", is_active: true },
        ]);
      }
      if (url.startsWith("/products/prod-1/stock?warehouse_id=wh-1")) {
        return Promise.resolve({
          batches: [
            {
              id: "batch-1",
              product_id: "prod-1",
              warehouse_id: "wh-1",
              batch_no: "BATCH-2026-0801",
              quantity: 80.0,
            },
          ],
        });
      }
      if (url.startsWith("/products/prod-1/stock?warehouse_id=wh-2")) {
        return Promise.resolve({
          batches: [
            {
              id: "batch-2",
              product_id: "prod-1",
              warehouse_id: "wh-2",
              batch_no: "BATCH-2026-0801",
              quantity: 20.0,
            },
          ],
        });
      }
      if (url.startsWith("/stock/transfers")) {
        return Promise.resolve(MOCK_TRANSFERS_RESPONSE);
      }
      return Promise.resolve([]);
    }),
    post: vi.fn().mockImplementation((url: string, body: { quantity?: number }) => {
      if (url === "/stock/transfers") {
        return Promise.resolve({
          id: "trf-new",
          product_id: "prod-1",
          from_warehouse_id: "wh-1",
          to_warehouse_id: "wh-2",
          quantity: body.quantity || 25,
          notes: "Store stock balance",
        });
      }
      return Promise.resolve({});
    }),
  },
}));

describe("Stock Transfers UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the transfer page with form fields, live preview, and transfers table", async () => {
    render(<StockTransferPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Inter-Warehouse Stock Transfers").length).toBeGreaterThanOrEqual(
        1,
      );
      expect(screen.getByLabelText(/Product to Relocate \*/i)).toBeDefined();
      expect(screen.getByLabelText(/Source Warehouse \(Dispatch\) \*/i)).toBeDefined();
      expect(screen.getByLabelText(/Destination Warehouse \(Receive\) \*/i)).toBeDefined();
      expect(screen.getAllByText("Recent Inter-Warehouse Transfers").length).toBeGreaterThanOrEqual(
        1,
      );
      expect(screen.getAllByText("Organic Whole Milk 1L").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("selects product and batch, updates live dual-warehouse preview, and submits transfer", async () => {
    render(<StockTransferPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Product to Relocate \*/i)).toBeDefined();
    });

    // Select Product
    fireEvent.change(screen.getByLabelText(/Product to Relocate \*/i), {
      target: { value: "prod-1" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText(/Source Stock Batch \*/i)).toBeDefined();
    });

    // Enter transfer quantity
    const qtyInput = screen.getByLabelText(/Quantity to Transfer \*/i);
    fireEvent.change(qtyInput, { target: { value: "25" } });

    // Enter notes
    const notesInput = screen.getByLabelText(/Reference \/ Reason Notes/i);
    fireEvent.change(notesInput, { target: { value: "Store stock balance" } });

    // Submit transfer
    const submitBtn = screen.getByRole("button", { name: /Execute Inter-Warehouse Transfer/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/stock/transfers",
        expect.objectContaining({
          product_id: "prod-1",
          batch_id: "batch-1",
          from_warehouse_id: "wh-1",
          to_warehouse_id: "wh-2",
          quantity: 25,
          notes: "Store stock balance",
        }),
      );
      expect(
        screen.getAllByText(/Successfully transferred 25.00 units/i).length,
      ).toBeGreaterThanOrEqual(1);
    });
  });
});
