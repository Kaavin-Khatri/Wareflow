import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import PurchaseOrdersPage, { PurchaseOrderItemType } from "@/app/admin/purchase-orders/page";
import { ThemeProvider } from "@/components/ThemeProvider";
import { apiClient } from "@/lib/api-client";

// Mock Next Navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/purchase-orders",
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

const mockPurchaseOrders: PurchaseOrderItemType[] = [
  {
    id: "po-1",
    po_number: "PO-202608-0001",
    supplier_id: "sup-1",
    supplier_name: "Tata Consumer Products",
    status: "ordered",
    order_date: "2026-08-18T10:00:00Z",
    expected_date: "2026-08-25",
    total_amount: 15000.0,
    items_count: 2,
    items: [
      {
        id: "item-1",
        po_id: "po-1",
        product_id: "prod-1",
        product_name: "Tata Tea Gold 500g",
        product_sku: "TEA-GOLD-500",
        qty_ordered: 100,
        qty_received: 40,
        unit_cost: 100,
        uom_id: "uom-1",
        uom_name: "Pouch",
        base_uom_name: "Pouch",
        line_total: 10000,
      },
      {
        id: "item-2",
        po_id: "po-1",
        product_id: "prod-2",
        product_name: "Tata Salt 1kg",
        product_sku: "SALT-TATA-1KG",
        qty_ordered: 200,
        qty_received: 0,
        unit_cost: 25,
        uom_id: "uom-1",
        uom_name: "Pouch",
        base_uom_name: "Pouch",
        line_total: 5000,
      },
    ],
    created_at: "2026-08-18T10:00:00Z",
  },
  {
    id: "po-2",
    po_number: "PO-202608-0002",
    supplier_id: "sup-2",
    supplier_name: "Fortune Oil Mills",
    status: "draft",
    order_date: "2026-08-18T11:00:00Z",
    expected_date: null,
    total_amount: 28000.0,
    items_count: 1,
    items: [
      {
        id: "item-3",
        po_id: "po-2",
        product_id: "prod-3",
        product_name: "Fortune Sunflower Oil 1L",
        product_sku: "OIL-FORT-1L",
        qty_ordered: 200,
        qty_received: 0,
        unit_cost: 140,
        uom_id: "uom-2",
        uom_name: "Bottle",
        base_uom_name: "Bottle",
        line_total: 28000,
      },
    ],
    created_at: "2026-08-18T11:00:00Z",
  },
];

const mockSuppliers = [
  { id: "sup-1", name: "Tata Consumer Products", is_active: true },
  { id: "sup-2", name: "Fortune Oil Mills", is_active: true },
];

const mockWarehouses = [
  { id: "wh-1", name: "Main Central Hub", location: "Sector 4", is_active: true },
];

describe("PurchaseOrdersPage", () => {
  beforeEach(() => {
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

    vi.clearAllMocks();
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path.includes("/purchase-orders")) {
        return Promise.resolve(mockPurchaseOrders);
      }
      if (path.includes("/suppliers")) {
        return Promise.resolve(mockSuppliers);
      }
      if (path.includes("/stock/warehouses")) {
        return Promise.resolve(mockWarehouses);
      }
      if (path.includes("/products")) {
        return Promise.resolve({
          items: [
            {
              id: "prod-1",
              name: "Tata Tea Gold 500g",
              sku: "TEA-GOLD-500",
              cost_price: 100,
              base_uom_id: "uom-1",
              is_active: true,
            },
          ],
        });
      }
      if (path.includes("/uom")) {
        return Promise.resolve([{ id: "uom-1", name: "Pouch", abbreviation: "pc" }]);
      }
      return Promise.resolve([]);
    });
  });

  it("renders purchase orders, KPIs, and data table columns", async () => {
    render(
      <ThemeProvider>
        <PurchaseOrdersPage />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByText("PO-202608-0001").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("PO-202608-0002").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Tata Consumer Products").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Fortune Oil Mills").length).toBeGreaterThanOrEqual(1);
    });

    // Check KPI summary totals
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Ordered").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Draft").length).toBeGreaterThanOrEqual(1);
  });

  it("filters purchase orders by status tabs", async () => {
    render(
      <ThemeProvider>
        <PurchaseOrdersPage />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByText("PO-202608-0001").length).toBeGreaterThanOrEqual(1);
    });

    const draftTab = screen.getByRole("button", { name: "Draft" });
    fireEvent.click(draftTab);

    expect(screen.getAllByText("PO-202608-0002").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("PO-202608-0001")).toBeNull();
  });

  it("opens the goods receiving modal for ordered purchase orders", async () => {
    render(
      <ThemeProvider>
        <PurchaseOrdersPage />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByText("PO-202608-0001").length).toBeGreaterThanOrEqual(1);
    });

    const receiveBtn = screen.getAllByRole("button", { name: /Receive Goods/i })[0];
    fireEvent.click(receiveBtn);

    await waitFor(() => {
      expect(screen.getAllByText(/Receive Inbound Goods/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Tata Tea Gold 500g").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Tata Salt 1kg").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("submits goods receipt and sends POST /purchase-orders/{id}/receive payload", async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      id: "po-1",
      status: "received",
    });

    render(
      <ThemeProvider>
        <PurchaseOrdersPage />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByText("PO-202608-0001").length).toBeGreaterThanOrEqual(1);
    });

    const receiveBtn = screen.getAllByRole("button", { name: /Receive Goods/i })[0];
    fireEvent.click(receiveBtn);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Confirm Goods Receipt/i })).toBeDefined();
    });

    const submitReceiptBtn = screen.getByRole("button", { name: /Confirm Goods Receipt/i });
    fireEvent.click(submitReceiptBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/purchase-orders/po-1/receive",
        expect.objectContaining({
          items: expect.any(Array),
        }),
      );
    });
  });
});
