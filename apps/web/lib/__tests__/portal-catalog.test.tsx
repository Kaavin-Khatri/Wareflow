import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import PortalCatalogPage from "@/app/portal/catalog/page";
import { onAuthStateChanged } from "firebase/auth";

// Mock firebase auth
vi.mock("@/lib/firebase-client", () => ({
  auth: { currentUser: { uid: "uid_ret_alice", email: "alice@alphamart.com", getIdToken: async () => "mock_token" } },
}));

vi.mock("firebase/auth", () => ({
  onAuthStateChanged: vi.fn(),
}));

const mockCategories = [
  { id: "cat-grains", name: "Grains & Cereals" },
  { id: "cat-beverages", name: "Beverages" },
];

const mockProducts = [
  {
    id: "prod-1",
    sku: "RIC-BAS-001",
    name: "Royal Basmati Rice 25kg",
    description: "Premium aged basmati rice",
    content_details: "25kg Bag, Grade A",
    image_url: null,
    category_id: "cat-grains",
    category_name: "Grains & Cereals",
    unit: "Bag",
    base_price: 1000.0,
    effective_price: 950.0,
    discount_percentage: 5.0,
    pricing_tier: "silver",
    availability: "Available",
    hsn_code: "1006.30",
  },
  {
    id: "prod-2",
    sku: "TEA-ASS-001",
    name: "Assam CTC Black Tea 5kg",
    description: "Strong aromatic tea",
    content_details: "5kg Box",
    image_url: null,
    category_id: "cat-beverages",
    category_name: "Beverages",
    unit: "Box",
    base_price: 500.0,
    effective_price: 475.0,
    discount_percentage: 5.0,
    pricing_tier: "silver",
    availability: "Low",
    hsn_code: "0902.30",
  },
  {
    id: "prod-3",
    sku: "SUG-REF-001",
    name: "Refined White Sugar 50kg",
    description: "Pure cane sugar",
    content_details: "50kg Bag",
    image_url: null,
    category_id: "cat-grains",
    category_name: "Grains & Cereals",
    unit: "Bag",
    base_price: 200.0,
    effective_price: 190.0,
    discount_percentage: 5.0,
    pricing_tier: "silver",
    availability: "Out",
    hsn_code: "1701.99",
  },
];

describe("Retailer Portal — Tier-Priced Wholesale Catalog View", () => {
  beforeEach(() => {
    vi.mocked(onAuthStateChanged).mockImplementation((_auth, callback) => {
      if (typeof callback === "function") {
        (callback as (user: unknown) => void)({
          uid: "uid_ret_alice",
          email: "alice@alphamart.com",
          getIdToken: async () => "mock_token",
        });
      }
      return () => {};
    });

    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/portal/categories")) {
        return Promise.resolve({
          ok: true,
          json: async () => mockCategories,
        });
      }
      if (url.includes("/portal/catalog")) {
        return Promise.resolve({
          ok: true,
          json: async () => mockProducts,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      });
    });
  });

  it("renders catalog header, tier badge, search bar, and product cards", async () => {
    render(<PortalCatalogPage />);

    expect(await screen.findByText("Wholesale Catalog")).toBeDefined();
    expect(screen.getByText(/Silver Tier Pricing/i)).toBeDefined();
    expect(screen.getByPlaceholderText(/Search products by SKU, name, or description/i)).toBeDefined();
    expect(screen.getByText("Royal Basmati Rice 25kg")).toBeDefined();
    expect(screen.getByText("Assam CTC Black Tea 5kg")).toBeDefined();
    expect(screen.getByText("Refined White Sugar 50kg")).toBeDefined();
  });

  it("displays tier-discounted pricing with strike-through base wholesale rate", async () => {
    render(<PortalCatalogPage />);

    expect(await screen.findByText("Royal Basmati Rice 25kg")).toBeDefined();

    // Effective tier price: ₹950.00
    expect(screen.getByText("₹950.00")).toBeDefined();
    // Strike-through base price: ₹1000.00
    expect(screen.getByText("₹1000.00")).toBeDefined();
    // Discount badge: 5% OFF
    const discountBadges = screen.getAllByText("5% OFF");
    expect(discountBadges.length).toBeGreaterThanOrEqual(1);
  });

  it("displays privacy-safe stock availability status (Available / Low Stock / Out)", async () => {
    render(<PortalCatalogPage />);

    expect(await screen.findByText("Royal Basmati Rice 25kg")).toBeDefined();

    expect(screen.getAllByText("Available").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Low Stock").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Out").length).toBeGreaterThanOrEqual(1);

    // Out of stock product card button is disabled
    const outBtns = screen.getAllByRole("button", { name: "Out of Stock" });
    expect(outBtns.length).toBeGreaterThanOrEqual(1);
    expect(outBtns.some((btn) => btn.hasAttribute("disabled"))).toBe(true);
  });

  it("filters product cards instantaneously on search input change", async () => {
    render(<PortalCatalogPage />);

    expect(await screen.findByText("Royal Basmati Rice 25kg")).toBeDefined();

    const searchInput = screen.getByPlaceholderText(/Search products by SKU, name, or description/i);
    fireEvent.change(searchInput, { target: { value: "tea" } });

    expect(screen.getByText("Assam CTC Black Tea 5kg")).toBeDefined();
    expect(screen.queryByText("Royal Basmati Rice 25kg")).toBeNull();
    expect(screen.queryByText("Refined White Sugar 50kg")).toBeNull();
  });

  it("filters product cards on category pill selection", async () => {
    render(<PortalCatalogPage />);

    const bevButton = await screen.findByRole("button", { name: "Beverages" });
    fireEvent.click(bevButton);

    await waitFor(() => {
      expect(screen.getByText("Assam CTC Black Tea 5kg")).toBeDefined();
      expect(screen.queryByText("Royal Basmati Rice 25kg")).toBeNull();
    });
  });

  it("opens Ask a Question modal and allows submitting an inquiry", async () => {
    render(<PortalCatalogPage />);

    const askButtons = await screen.findAllByRole("button", { name: "Ask Question" });
    // First alphabetically sorted item is Assam CTC Black Tea 5kg
    fireEvent.click(askButtons[0]);

    const textarea = await screen.findByPlaceholderText(/Ask about bulk volumes/i);
    fireEvent.change(textarea, { target: { value: "Can we order 100 boxes next week?" } });

    await waitFor(() => {
      const submitBtn = screen.getByRole("button", { name: "Send Inquiry" });
      expect(submitBtn.hasAttribute("disabled")).toBe(false);
    });

    const submitBtn = screen.getByRole("button", { name: "Send Inquiry" });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Inquiry for Assam CTC Black Tea 5kg submitted successfully!/i)).toBeDefined();
  });

  it("opens Quick Order modal and calculates quantity total", async () => {
    render(<PortalCatalogPage />);

    const addButtons = await screen.findAllByRole("button", { name: "Add to Order" });
    // First alphabetically sorted item is Assam CTC Black Tea 5kg (effective unit price: 475.00)
    fireEvent.click(addButtons[0]);

    const heading = await screen.findByRole("heading", { name: "Add to Order" });
    expect(heading).toBeDefined();

    const plusBtn = screen.getByRole("button", { name: "+" });
    fireEvent.click(plusBtn);

    // After clicking +, total is 2 * 475.00 = 950.00
    const modalContainer = heading.closest(".max-w-md");
    expect(modalContainer).toBeDefined();
    if (modalContainer) {
      expect(within(modalContainer as HTMLElement).getByText("₹950.00")).toBeDefined();
    }

    const confirmBtn = screen.getByRole("button", { name: "Confirm & Add" });
    fireEvent.click(confirmBtn);

    expect(await screen.findByText(/Added 2 Box\(s\) of Assam CTC Black Tea 5kg to (order|cart)!/i)).toBeDefined();
  });
});
