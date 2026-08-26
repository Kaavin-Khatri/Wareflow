import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import PurchaseReturnsPage, { PurchaseReturn } from "@/app/admin/purchase-returns/page";
import { ThemeProvider } from "@/components/ThemeProvider";
import { apiClient } from "@/lib/api-client";

// Mock Next Navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/purchase-returns",
  useSearchParams: () => new URLSearchParams(),
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

// Mock apiClient
vi.mock("@/lib/api-client", () => ({
  getAuthToken: async () => "test_token",
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockReturns: PurchaseReturn[] = [
  {
    id: "ret-001-abcdef123456",
    purchase_order_id: "po-1",
    po_number: "PO-202608-0001",
    supplier_id: "sup-1",
    supplier_name: "Tata Consumer Products",
    status: "requested",
    reason: "Packaging damaged during delivery",
    credit_note_ref: null,
    requested_at: "2026-08-18T10:00:00Z",
    items_count: 1,
    total_qty: 15,
    items: [
      {
        id: "ri-1",
        return_id: "ret-001-abcdef123456",
        product_id: "prod-1",
        product_name: "Tata Tea Gold 500g",
        product_sku: "TEA-GOLD-500",
        qty: 15,
        batch_id: "batch-1",
        batch_no: "BATCH-2026-T1",
        reason: "Crushed cartons",
      },
    ],
  },
  {
    id: "ret-002-9876543210ab",
    purchase_order_id: "po-2",
    po_number: "PO-202608-0002",
    supplier_id: "sup-2",
    supplier_name: "Fortune Agri Corp",
    status: "credited",
    reason: "Moisture contamination",
    credit_note_ref: "CRN-FORTUNE-881",
    requested_at: "2026-08-17T14:30:00Z",
    items_count: 1,
    total_qty: 25,
    items: [
      {
        id: "ri-2",
        return_id: "ret-002-9876543210ab",
        product_id: "prod-2",
        product_name: "Fortune Sunflower Oil 1L",
        product_sku: "OIL-FORT-1L",
        qty: 25,
        batch_id: "batch-2",
        batch_no: "BATCH-2026-F2",
        reason: "Leaking pouches",
      },
    ],
  },
];

const mockPurchaseOrders = [
  {
    id: "po-1",
    po_number: "PO-202608-0001",
    supplier_id: "sup-1",
    supplier_name: "Tata Consumer Products",
    status: "received",
    items: [
      {
        id: "poi-1",
        product_id: "prod-1",
        product_name: "Tata Tea Gold 500g",
        product_sku: "TEA-GOLD-500",
        qty_ordered: 100,
        qty_received: 100,
      },
    ],
  },
];

const mockBatches = [
  {
    id: "batch-1",
    product_id: "prod-1",
    product_name: "Tata Tea Gold 500g",
    batch_no: "BATCH-2026-T1",
    quantity: 85,
    warehouse_id: "wh-1",
  },
];

const mockSuppliers = [
  { id: "sup-1", name: "Tata Consumer Products", is_active: true },
  { id: "sup-2", name: "Fortune Agri Corp", is_active: true },
];

describe("PurchaseReturnsPage Frontend Component (Step 7.3)", () => {
  beforeEach(() => {
    vi.clearAllMocks();

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

    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path.startsWith("/purchase-returns")) return Promise.resolve(mockReturns);
      if (path.startsWith("/purchase-orders")) return Promise.resolve(mockPurchaseOrders);
      if (path.startsWith("/stock/batches")) return Promise.resolve(mockBatches);
      if (path.startsWith("/suppliers")) return Promise.resolve(mockSuppliers);
      return Promise.resolve([]);
    });
  });

  const renderComponent = () => {
    return render(
      <ThemeProvider>
        <PurchaseReturnsPage />
      </ThemeProvider>,
    );
  };

  it("should render page header, KPI metric cards, and returns table", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText("Supplier Returns (RMA Out)").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Total Returns").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Units Returned").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Vendor Credited").length).toBeGreaterThanOrEqual(1);
      // Check table rows
      expect(screen.getAllByText("PO-202608-0001").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Tata Consumer Products").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("15 units").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("CRN-FORTUNE-881").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("should filter table when search query is entered", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText("PO-202608-0001").length).toBeGreaterThanOrEqual(1);
    });

    const searchInput = screen.getByPlaceholderText("Search RMA, PO, supplier, batch...");
    fireEvent.change(searchInput, { target: { value: "Fortune" } });

    // Fortune row should match, Tata row should not
    expect(screen.getAllByText("PO-202608-0002").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("PO-202608-0001")).toBeNull();
  });

  it("should filter returns by status pills", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText("PO-202608-0001").length).toBeGreaterThanOrEqual(1);
    });

    // Click "credited" pill
    const creditedPill = screen.getByRole("button", { name: /^credited$/i });
    fireEvent.click(creditedPill);

    // Only credited return should remain visible
    expect(screen.getAllByText("PO-202608-0002").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("PO-202608-0001")).toBeNull();
  });

  it("should open Create Return modal and allow submitting a return request", async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      id: "ret-new",
      status: "requested",
      total_qty: 5,
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText("Request Return (RMA)").length).toBeGreaterThanOrEqual(1);
    });

    const createBtn = screen.getAllByText("Request Return (RMA)")[0];
    fireEvent.click(createBtn);

    // Modal title should appear
    expect(screen.getByText("Create Supplier Return Request (RMA Out)")).toBeDefined();

    // Select PO
    const poSelect = screen.getByDisplayValue("Select a Purchase Order...");
    fireEvent.change(poSelect, { target: { value: "po-1" } });

    // Submit form (batch is auto-populated for product line)
    const submitBtn = screen.getByText("Confirm & Deduct Stock");
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/purchase-returns",
        expect.objectContaining({
          purchase_order_id: "po-1",
        }),
      );
    });
  });

  it("should open Status Update modal and transition requested -> shipped", async () => {
    vi.mocked(apiClient.patch).mockResolvedValueOnce({
      id: "ret-001-abcdef123456",
      status: "shipped",
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText("Ship RMA").length).toBeGreaterThanOrEqual(1);
    });

    const shipBtn = screen.getAllByText("Ship RMA")[0];
    fireEvent.click(shipBtn);

    expect(screen.getByText(/Update RMA Status/i)).toBeDefined();

    const confirmBtn = screen.getByText("Confirm SHIPPED");
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(apiClient.patch).toHaveBeenCalledWith(
        "/purchase-returns/ret-001-abcdef123456/status",
        expect.objectContaining({
          status: "shipped",
        }),
      );
    });
  });

  it("should display 2FA challenge banner when 2FA error occurs and auto-reload on 2FA verified event", async () => {
    vi.mocked(apiClient.get).mockImplementationOnce((path: string) => {
      if (path.startsWith("/purchase-returns")) {
        return Promise.reject(new Error("Two-factor authentication required for sensitive operations."));
      }
      return Promise.resolve([]);
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/Two-factor authentication required/i)).toBeDefined();
      expect(screen.getByText("Verify 2FA Now")).toBeDefined();
    });

    // Reset mock to return valid data upon re-fetch
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path.startsWith("/purchase-returns")) return Promise.resolve(mockReturns);
      if (path.startsWith("/purchase-orders")) return Promise.resolve(mockPurchaseOrders);
      if (path.startsWith("/stock/batches")) return Promise.resolve(mockBatches);
      if (path.startsWith("/suppliers")) return Promise.resolve(mockSuppliers);
      return Promise.resolve([]);
    });

    // Dispatch 2fa verified event
    window.dispatchEvent(new CustomEvent("wareflow:2fa-verified"));

    await waitFor(() => {
      expect(screen.queryByText(/Two-factor authentication required/i)).toBeNull();
      expect(screen.getAllByText("PO-202608-0001").length).toBeGreaterThanOrEqual(1);
    });
  });
});

