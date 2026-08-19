import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import AdminInquiriesPage from "@/app/admin/inquiries/page";
import PortalCatalogPage from "@/app/portal/catalog/page";
import { onAuthStateChanged } from "firebase/auth";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/inquiries",
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

// Mock firebase client
vi.mock("@/lib/firebase-client", () => ({
  auth: {
    currentUser: {
      uid: "uid_123",
      email: "staff@wareflow.io",
      getIdToken: async () => "mock_token",
    },
  },
}));

vi.mock("firebase/auth", () => ({
  onAuthStateChanged: vi.fn(),
}));

const mockInquiries = [
  {
    id: "inq-1",
    product_id: "prod-1",
    product_name: "Royal Basmati Rice 25kg",
    product_sku: "RIC-BAS-001",
    retailer_id: "ret-1",
    retailer_name: "Alice Grocery Store",
    customer_id: null,
    message: "Do you have 200 bags available for immediate dispatch?",
    status: "open",
    response: null,
    created_at: new Date().toISOString(),
    responded_at: null,
  },
  {
    id: "inq-2",
    product_id: "prod-2",
    product_name: "Assam CTC Tea 5kg",
    product_sku: "TEA-ASS-001",
    retailer_id: "ret-2",
    retailer_name: "Bob Supermarket",
    customer_id: null,
    message: "What is the bulk price for 50 boxes?",
    status: "responded",
    response: "We can provide a 10% discount for orders over 50 units.",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    responded_at: new Date().toISOString(),
  },
];

const mockCatalogProducts = [
  {
    id: "prod-1",
    sku: "RIC-BAS-001",
    name: "Royal Basmati Rice 25kg",
    description: "Premium aged basmati rice",
    content_details: "25kg Bag",
    image_url: null,
    category_id: "cat-1",
    category_name: "Grains",
    unit: "Bag",
    base_price: 1000.0,
    effective_price: 950.0,
    discount_percentage: 5.0,
    pricing_tier: "silver",
    availability: "Available",
    hsn_code: "1006.30",
  },
];

describe("Staff Inquiries Inbox (/admin/inquiries)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn().mockImplementation(async (url: string, opts?: RequestInit) => {
      if (url.includes("/inquiries") && opts?.method === "PATCH") {
        const body = JSON.parse(opts.body as string);
        return {
          ok: true,
          status: 200,
          json: async () => ({
            ...mockInquiries[0],
            status: "responded",
            response: body.response,
            responded_at: new Date().toISOString(),
          }),
        };
      }

      if (url.includes("/inquiries")) {
        return {
          ok: true,
          status: 200,
          json: async () => mockInquiries,
        };
      }

      return {
        ok: true,
        status: 200,
        json: async () => ({}),
      };
    });
  });

  it("renders staff inquiry inbox with statistics and inquiry cards", async () => {
    render(<AdminInquiriesPage />);

    expect(screen.getByText("Loading inquiry inbox...")).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("Product Inquiries & Quotes")).toBeDefined();
      expect(screen.getByText("Royal Basmati Rice 25kg")).toBeDefined();
      expect(screen.getByText("Assam CTC Tea 5kg")).toBeDefined();
      expect(screen.getByText("Alice Grocery Store")).toBeDefined();
      expect(screen.getByText("Bob Supermarket")).toBeDefined();
    });

    // Check stats
    expect(screen.getByText("1 Open")).toBeDefined();
    expect(screen.getByText("1 Answered")).toBeDefined();
  });

  it("filters inquiries by status tab", async () => {
    render(<AdminInquiriesPage />);

    await waitFor(() => {
      expect(screen.getByText("Royal Basmati Rice 25kg")).toBeDefined();
    });

    // Click Open filter
    const openBtn = screen.getByRole("button", { name: /Open \(1\)/i });
    fireEvent.click(openBtn);

    expect(screen.getByText("Royal Basmati Rice 25kg")).toBeDefined();
    expect(screen.queryByText("Assam CTC Tea 5kg")).toBeNull();

    // Click Responded filter
    const respondedBtn = screen.getByRole("button", { name: /^Responded$/i });
    fireEvent.click(respondedBtn);

    expect(screen.queryByText("Royal Basmati Rice 25kg")).toBeNull();
    expect(screen.getByText("Assam CTC Tea 5kg")).toBeDefined();
  });

  it("allows staff to respond to an open inquiry and updates state", async () => {
    render(<AdminInquiriesPage />);

    await waitFor(() => {
      expect(screen.getByText("Royal Basmati Rice 25kg")).toBeDefined();
    });

    // Click Respond to Retailer button
    const respondBtn = screen.getByRole("button", { name: /Respond to Retailer/i });
    fireEvent.click(respondBtn);

    // Modal appears
    await waitFor(() => {
      expect(screen.getByText(/Reply to Inquiry: Royal Basmati Rice 25kg/i)).toBeDefined();
    });

    const textarea = screen.getByPlaceholderText(/Provide quotation details, dispatch timelines/i);
    fireEvent.change(textarea, {
      target: { value: "Yes, 200 bags can be dispatched by Friday." },
    });

    const submitBtn = screen.getByRole("button", { name: /Send Response/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/inquiries/inq-1/respond"),
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ response: "Yes, 200 bags can be dispatched by Friday." }),
        })
      );
    });
  });
});

describe("Retailer Portal Catalog Inquiry Flow (/portal/catalog)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(onAuthStateChanged).mockImplementation((_auth, callback) => {
      if (typeof callback === "function") {
        (callback as (user: unknown) => void)({
          uid: "uid_ret_alice",
          email: "alice@grocery.com",
          getIdToken: async () => "mock_ret_token",
        });
      }
      return () => {};
    });

    global.fetch = vi.fn().mockImplementation(async (url: string, opts?: RequestInit) => {
      if (url.includes("/portal/categories")) {
        return {
          ok: true,
          status: 200,
          json: async () => [{ id: "cat-1", name: "Grains" }],
        };
      }

      if (url.includes("/portal/catalog")) {
        return {
          ok: true,
          status: 200,
          json: async () => mockCatalogProducts,
        };
      }

      if (url.includes("/portal/inquiries") && opts?.method === "POST") {
        return {
          ok: true,
          status: 201,
          json: async () => ({
            id: "inq-new-1",
            product_id: "prod-1",
            message: "Need bulk quotation for 100 bags",
            status: "open",
          }),
        };
      }

      return {
        ok: true,
        status: 200,
        json: async () => ({}),
      };
    });
  });

  it("opens inquiry modal and submits inquiry to POST /portal/inquiries", async () => {
    render(<PortalCatalogPage />);

    await waitFor(() => {
      expect(screen.getByText("Royal Basmati Rice 25kg")).toBeDefined();
    });

    // Open inquiry modal
    const askBtn = screen.getByRole("button", { name: /Ask Question/i });
    fireEvent.click(askBtn);

    expect(screen.getByRole("heading", { name: "Ask a Question" })).toBeDefined();

    const textarea = screen.getByPlaceholderText(/Ask about bulk volumes, packaging options/i);
    fireEvent.change(textarea, {
      target: { value: "Need bulk quotation for 100 bags" },
    });

    const sendBtn = screen.getByRole("button", { name: /Send Inquiry/i });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/portal/inquiries"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            product_id: "prod-1",
            message: "Need bulk quotation for 100 bags",
          }),
        })
      );
      expect(screen.getByText(/Inquiry for Royal Basmati Rice 25kg submitted successfully!/i)).toBeDefined();
    });
  });
});
