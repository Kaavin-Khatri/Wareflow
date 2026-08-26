import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import RetailerLedgerPage from "@/app/admin/retailers/[id]/ledger/page";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "ret-101" }),
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/retailers/ret-101/ledger",
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

const MOCK_LEDGER_RESPONSE = {
  retailer_id: "ret-101",
  retailer_name: "Apex Superstore",
  gstin: "07AAAAA1234A1Z5",
  credit_limit: 500000.0,
  current_credit_balance: 17500.0,
  available_credit: 482500.0,
  total_invoiced: 40000.0,
  total_paid: 22500.0,
  entries: [
    {
      id: "inv-1",
      date: "2026-08-10T10:00:00Z",
      entry_type: "invoice",
      reference_no: "INV/2026-27/0031",
      description: "Tax Invoice (SO-0031)",
      debit_amount: 15000.0,
      credit_amount: 0.0,
      running_balance: 15000.0,
      status: "paid",
    },
    {
      id: "pay-1",
      date: "2026-08-12T14:30:00Z",
      entry_type: "payment",
      reference_no: "PAY-P1A2B3C4",
      description: "Payment received via BANK TRANSFER — Partial on Inv 31",
      debit_amount: 0.0,
      credit_amount: 10000.0,
      running_balance: 5000.0,
      status: "settled",
    },
    {
      id: "inv-2",
      date: "2026-08-15T09:15:00Z",
      entry_type: "invoice",
      reference_no: "INV/2026-27/0032",
      description: "Tax Invoice (SO-0032)",
      debit_amount: 25000.0,
      credit_amount: 0.0,
      running_balance: 30000.0,
      status: "partially_paid",
    },
    {
      id: "pay-2",
      date: "2026-08-17T16:00:00Z",
      entry_type: "payment",
      reference_no: "PAY-P2A2B3C4",
      description: "Payment received via UPI — 50% on Inv 32",
      debit_amount: 0.0,
      credit_amount: 12500.0,
      running_balance: 17500.0,
      status: "settled",
    },
  ],
};

const MOCK_RETAILER_INVOICES = {
  items: [
    {
      id: "inv-2",
      invoice_no: "INV/2026-27/0032",
      invoice_date: "2026-08-15T09:15:00Z",
      total_amount: 25000.0,
      paid_amount: 12500.0,
      outstanding_balance: 12500.0,
      status: "partially_paid",
    },
  ],
};

vi.mock("@/lib/api-client", () => ({
  getAuthToken: async () => "test_token",
  apiClient: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url.includes("/ledger")) {
        return Promise.resolve(MOCK_LEDGER_RESPONSE);
      }
      if (url.includes("/invoices")) {
        return Promise.resolve(MOCK_RETAILER_INVOICES);
      }
      return Promise.resolve({});
    }),
    post: vi.fn().mockImplementation(() => Promise.resolve({ success: true })),
  },
}));

describe("Retailer Accounts-Receivable Ledger UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the retailer statement with KPI cards, credit utilization, and paired ledger entries", async () => {
    render(<RetailerLedgerPage />);

    await waitFor(() => {
      expect(screen.getByText(/Apex Superstore Statement/i)).toBeDefined();
      expect(screen.getByText(/GSTIN: 07AAAAA1234A1Z5/i)).toBeDefined();
      expect(screen.getByText("Current Balance Owed")).toBeDefined();
      expect(screen.getByText("Credit Line & Limit")).toBeDefined();
      expect(screen.getByText("Total Invoiced (Debit)")).toBeDefined();
      expect(screen.getByText("Total Settled (Credit)")).toBeDefined();
      expect(screen.getAllByText("INV/2026-27/0031").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("INV/2026-27/0032").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("PAY-P1A2B3C4").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("PAY-P2A2B3C4").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("filters ledger transactions by type (invoices vs payments)", async () => {
    render(<RetailerLedgerPage />);

    await waitFor(() => {
      expect(screen.getAllByText("INV/2026-27/0031").length).toBeGreaterThanOrEqual(1);
    });

    // Click Invoices filter
    fireEvent.click(screen.getByRole("button", { name: /Invoices \(/i }));

    await waitFor(() => {
      expect(screen.getAllByText("INV/2026-27/0031").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("INV/2026-27/0032").length).toBeGreaterThanOrEqual(1);
      expect(screen.queryByText("PAY-P1A2B3C4")).toBeNull();
    });

    // Click Payments filter
    fireEvent.click(screen.getByRole("button", { name: /Payments \(/i }));

    await waitFor(() => {
      expect(screen.getAllByText("PAY-P1A2B3C4").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("PAY-P2A2B3C4").length).toBeGreaterThanOrEqual(1);
      expect(screen.queryByText("INV/2026-27/0031")).toBeNull();
    });
  });

  it("opens the Record Payment modal and allows recording a payment against an outstanding invoice", async () => {
    render(<RetailerLedgerPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Record Payment/i })).toBeDefined();
    });

    fireEvent.click(screen.getByRole("button", { name: /Record Payment/i }));

    await waitFor(() => {
      expect(screen.getByText(/Record Payment for Apex Superstore/i)).toBeDefined();
      expect(screen.getByText(/Apply to Invoice/i)).toBeDefined();
      expect(screen.getByText(/Payment Amount/i)).toBeDefined();
    });

    // Submit form
    fireEvent.click(screen.getByRole("button", { name: /Record & Post Payment/i }));

    await waitFor(() => {
      expect(screen.queryByText(/Record Payment for Apex Superstore/i)).toBeNull();
    });
  });
});
