import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import InvoicesPage from "@/app/admin/invoices/page";


// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/invoices",
  useSearchParams: () => new URLSearchParams(),
}));

const MOCK_INVOICES_RESPONSE = {
  items: [
    {
      id: "inv-101",
      sales_order_id: "so-101",
      sales_order_number: "SO-2026-001",
      invoice_no: "INV/2026-27/0001",
      invoice_date: "2026-08-18T10:00:00Z",
      buyer_type: "retailer",
      buyer_name: "Apex Wholesale Mart",
      subtotal: 11000.0,
      tax_amount: 1980.0,
      total_amount: 12980.0,
      status: "unpaid",
      items_count: 2,
      created_at: "2026-08-18T10:00:00Z",
    },
    {
      id: "inv-102",
      sales_order_id: "so-102",
      sales_order_number: "SO-2026-002",
      invoice_no: "INV/2026-27/0002",
      invoice_date: "2026-08-17T10:00:00Z",
      buyer_type: "retailer",
      buyer_name: "Fresh Mart Retail",
      subtotal: 20000.0,
      tax_amount: 3600.0,
      total_amount: 23600.0,
      status: "paid",
      items_count: 3,
      created_at: "2026-08-17T10:00:00Z",
    },
  ],
  total: 2,
  page: 1,
  page_size: 100,
  pages: 1,
};

const MOCK_INVOICE_DETAIL = {
  id: "inv-101",
  sales_order_id: "so-101",
  sales_order_number: "SO-2026-001",
  buyer_type: "retailer",
  buyer_name: "Apex Wholesale Mart",
  buyer_gstin: "06AAAAA0000A1Z5",
  buyer_phone: "+919876543210",
  buyer_email: "accounts@apex.com",
  buyer_address: "Sector 18, Gurugram, Haryana",
  invoice_no: "INV/2026-27/0001",
  invoice_date: "2026-08-18T10:00:00Z",
  gst_rate: 18.0,
  subtotal: 11000.0,
  tax_amount: 1980.0,
  total_amount: 12980.0,
  status: "unpaid",
  created_at: "2026-08-18T10:00:00Z",
  items: [
    {
      id: "item-1",
      invoice_id: "inv-101",
      product_id: "prod-milk",
      product_name: "Organic Cow Milk 1L",
      hsn_code: "0401",
      qty: 100.0,
      unit_price: 60.0,
      tax_rate: 18.0,
      tax_amount: 1080.0,
      total: 7080.0,
    },
    {
      id: "item-2",
      invoice_id: "inv-101",
      product_id: "prod-butter",
      product_name: "Salted Butter 500g",
      hsn_code: "0405",
      qty: 20.0,
      unit_price: 250.0,
      tax_rate: 18.0,
      tax_amount: 900.0,
      total: 5900.0,
    },
  ],
};

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url.startsWith("/invoices/inv-101")) {
        return Promise.resolve(MOCK_INVOICE_DETAIL);
      }
      if (url.startsWith("/invoices")) {
        return Promise.resolve(MOCK_INVOICES_RESPONSE);
      }
      return Promise.resolve([]);
    }),
    post: vi.fn().mockImplementation((url: string) => {
      if (url.includes("/invoice")) {
        return Promise.resolve(MOCK_INVOICE_DETAIL);
      }
      return Promise.resolve({});
    }),
  },
}));

describe("GST Invoices & Billing UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the tax invoice dashboard with KPIs and list items", async () => {
    render(<InvoicesPage />);

    await waitFor(() => {
      expect(screen.getAllByText("GST Tax Invoices & Billing").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Total Invoiced Value")).toBeDefined();
      expect(screen.getByText("Outstanding Unpaid")).toBeDefined();
      expect(screen.getByText("Collected Revenue")).toBeDefined();
      expect(screen.getByText("Active Invoices")).toBeDefined();
      expect(screen.getAllByText("INV/2026-27/0001").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Apex Wholesale Mart").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("filters invoices by status tabs", async () => {
    render(<InvoicesPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Apex Wholesale Mart").length).toBeGreaterThanOrEqual(1);
    });

    // Click paid filter button
    fireEvent.click(screen.getByTestId("filter-paid"));

    await waitFor(() => {
      expect(screen.getAllByText("Fresh Mart Retail").length).toBeGreaterThanOrEqual(1);
      expect(screen.queryByText("Apex Wholesale Mart")).toBeNull();
    });
  });




  it("opens invoice detail preview modal with GST breakdown and print action", async () => {
    render(<InvoicesPage />);

    await waitFor(() => {
      expect(screen.getAllByText("View & Print").length).toBeGreaterThanOrEqual(1);
    });

    fireEvent.click(screen.getAllByText("View & Print")[0]);

    await waitFor(() => {
      expect(screen.getAllByText(/Tax Invoice: INV\/2026-27\/0001/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("WareFlow Wholesale Distribution")).toBeDefined();
      expect(screen.getByText("06AAAAA0000A1Z5")).toBeDefined();
      expect(screen.getByText("Organic Cow Milk 1L")).toBeDefined();
      expect(screen.getByText("Salted Butter 500g")).toBeDefined();
      expect(screen.getByText("CGST (9%):")).toBeDefined();
      expect(screen.getByText("SGST (9%):")).toBeDefined();
      expect(screen.getByText(/Print \/ Export PDF/i)).toBeDefined();
    });
  });
});
