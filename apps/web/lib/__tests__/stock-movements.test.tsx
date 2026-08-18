import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import StockMovementLedgerPage from "@/app/admin/stock/ledger/page";
import StockAdjustPage from "@/app/admin/stock/adjust/page";
import { apiClient } from "@/lib/api-client";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/stock/ledger",
  useSearchParams: () => new URLSearchParams(),
}));

const MOCK_MOVEMENTS_RESPONSE = {
  items: [
    {
      id: "mov-1",
      product_id: "prod-1",
      product_name: "Organic Whole Milk 1L",
      product_sku: "MILK-ORG-001",
      warehouse_id: "wh-1",
      warehouse_name: "Central Cold Storage",
      batch_id: "batch-1",
      batch_no: "BATCH-2026-0801",
      type: "in",
      quantity: 500,
      reference_type: "purchase_order",
      reference_id: "PO-202608-0001",
      human_label: "PO #PO-202608-0001 (Goods Receipt)",
      created_by: "procurement@wareflow.io",
      created_at: "2026-08-01T10:00:00Z",
    },
    {
      id: "mov-2",
      product_id: "prod-2",
      product_name: "Royal Basmati Rice 5kg",
      product_sku: "RIC-BAS-005",
      warehouse_id: "wh-1",
      warehouse_name: "Central Distribution Center",
      batch_id: "batch-2",
      batch_no: "BATCH-2026-0810",
      type: "adjustment",
      quantity: -5,
      reference_type: "manual_adjustment",
      reference_id: "damage:Forklift puncture in pallet",
      human_label: "Adjustment: Damage (Forklift puncture in pallet)",
      created_by: "warehouse.staff@wareflow.io",
      created_at: "2026-08-05T12:00:00Z",
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
  pages: 1,
};

// Mock apiClient
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url.startsWith("/stock/movements")) {
        return Promise.resolve(MOCK_MOVEMENTS_RESPONSE);
      }
      if (url === "/products") {
        return Promise.resolve([
          { id: "prod-1", name: "Organic Whole Milk 1L", sku: "MILK-ORG-001" },
        ]);
      }
      if (url === "/stock/warehouses") {
        return Promise.resolve([{ id: "wh-1", name: "Central Cold Storage" }]);
      }
      if (url.startsWith("/products/prod-1/stock")) {
        return Promise.resolve({
          batches: [
            {
              id: "batch-1",
              product_id: "prod-1",
              warehouse_id: "wh-1",
              batch_no: "BATCH-2026-0801",
              quantity: 50.0,
            },
          ],
        });
      }
      if (url === "/me") {
        return Promise.resolve({
          id: "u1",
          email: "owner@wareflow.io",
          role: "Owner",
          permissions: ["inventory:manage", "stock:recount"],
        });
      }
      return Promise.resolve([]);
    }),
    post: vi.fn().mockImplementation((url: string, body: { delta?: number }) => {
      if (url === "/stock/adjustments") {
        return Promise.resolve({
          movement_id: "mov-new",
          product_id: "prod-1",
          warehouse_id: "wh-1",
          batch_id: "batch-1",
          previous_quantity: 50.0,
          new_quantity: 50.0 + (body.delta || 0),
          delta: body.delta || 0,
          reason: "damage",
        });
      }
      return Promise.resolve({});
    }),
  },
}));

describe("Stock Movements Ledger & Adjustments", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders stock movement ledger with KPI cards and table entries", async () => {
    render(<StockMovementLedgerPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Stock Movement Ledger").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("PO #PO-202608-0001 (Goods Receipt)").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Adjustment: Damage (Forklift puncture in pallet)").length).toBeGreaterThanOrEqual(1);
    });

    expect(screen.getAllByText("Movement Records").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Total Inbound Stock").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Total Dispatched Stock").length).toBeGreaterThanOrEqual(1);
  });

  it("filters ledger records by search query", async () => {
    render(<StockMovementLedgerPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Organic Whole Milk 1L").length).toBeGreaterThanOrEqual(1);
    });

    const searchInput = screen.getByPlaceholderText(/Search ledger by product/i);
    fireEvent.change(searchInput, { target: { value: "Rice" } });

    expect(screen.getAllByText("Royal Basmati Rice 5kg").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("Organic Whole Milk 1L")).toBeNull();
  });

  it("renders adjustment form, selects batch, and submits manual stock adjustment", async () => {
    render(<StockAdjustPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Record Stock Adjustment").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByLabelText(/Product \*/i)).toBeDefined();
    });

    // Select Product
    fireEvent.change(screen.getByLabelText(/Product \*/i), {
      target: { value: "prod-1" },
    });

    await waitFor(() => {
      expect(screen.getByLabelText(/Stock Batch \*/i)).toBeDefined();
    });

    // Fill Delta
    const deltaInput = screen.getByLabelText(/Quantity Delta \(\+ \/ -\) \*/i);
    fireEvent.change(deltaInput, { target: { value: "-5" } });

    // Fill Notes
    const notesInput = screen.getByLabelText(/Context Notes/i);
    fireEvent.change(notesInput, { target: { value: "Broken seals during audit" } });

    // Submit
    const commitBtn = screen.getByRole("button", { name: /Commit Stock Adjustment/i });
    fireEvent.click(commitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/stock/adjustments",
        expect.objectContaining({
          product_id: "prod-1",
          warehouse_id: "wh-1",
          batch_id: "batch-1",
          delta: -5,
          reason: "damage",
          notes: "Broken seals during audit",
        })
      );
      expect(screen.getAllByText("Stock Adjustment Recorded").length).toBeGreaterThanOrEqual(1);
    });
  });
});
