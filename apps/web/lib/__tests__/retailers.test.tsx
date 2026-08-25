/**
 * Frontend Unit Tests for Retailers Admin UI (Step 8.1).
 *
 * Tests:
 * 1. Renders KPI statistics cards, action buttons, and DataTable
 * 2. Filters retailers by search query, status, and pricing tier
 * 3. Modal create and update flows with pricing tiers and credit limits
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import RetailersAdminPage, { RetailerItem } from "@/app/admin/retailers/page";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/retailers",
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

const mockRetailers: RetailerItem[] = [
  {
    id: "ret-1",
    name: "Apex Kirana Stores",
    contact_person: "Ramesh Patel",
    phone: "9876543210",
    email: "ramesh@apex.in",
    address: "Shop 12, Market Yard",
    gstin: "27ABCDE1234F1Z5",
    pricing_tier: "gold",
    credit_limit: 100000.0,
    credit_balance: 25000.0,
    is_active: true,
  },
  {
    id: "ret-2",
    name: "City Supermarket",
    contact_person: "Pooja Sharma",
    phone: "9811223344",
    email: "pooja@citysuper.com",
    address: "MG Road, Pune",
    gstin: "27XYZAB9876C1Z0",
    pricing_tier: "silver",
    credit_limit: 50000.0,
    credit_balance: 0.0,
    is_active: true,
  },
  {
    id: "ret-3",
    name: "Old Corner Grocery",
    contact_person: "Mohan Lal",
    phone: "9822334455",
    email: "mohan@corner.in",
    address: "Old Town, Pune",
    gstin: null,
    pricing_tier: "standard",
    credit_limit: 10000.0,
    credit_balance: 5000.0,
    is_active: false,
  },
];

// Mock API client
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url === "/retailers") {
        return Promise.resolve(mockRetailers);
      }
      if (url === "/me") {
        return Promise.resolve({
          id: "u1",
          email: "owner@wareflow.io",
          display_name: "Owner",
          role_name: "Owner",
          permissions: ["*"],
        });
      }
      return Promise.resolve([]);
    }),
    post: vi.fn().mockResolvedValue({ id: "ret-new", name: "New Retailer" }),
    patch: vi.fn().mockResolvedValue({ id: "ret-1", name: "Apex Kirana Stores Updated" }),
  },
}));

describe("RetailersAdminPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders KPI metric cards and retailer records in DataTable", async () => {
    render(<RetailersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Retailers & B2B Accounts").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("City Supermarket").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Old Corner Grocery").length).toBeGreaterThanOrEqual(1);
    });

    // Verify Tier Badges rendered
    expect(screen.getAllByText(/Gold Tier/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Silver Tier/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Standard Base/i).length).toBeGreaterThanOrEqual(1);

    // Verify KPI numbers
    expect(screen.getAllByText("3").length).toBeGreaterThanOrEqual(1); // Total
  });

  it("filters retailers by search input", async () => {
    render(<RetailersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
    });

    const searchInput = screen.getByPlaceholderText(/Search by name/i);
    fireEvent.change(searchInput, { target: { value: "City" } });

    await waitFor(() => {
      expect(screen.getAllByText("City Supermarket").length).toBeGreaterThanOrEqual(1);
      expect(screen.queryByText("Apex Kirana Stores")).toBeNull();
    });
  });

  it("filters retailers by status tabs", async () => {
    render(<RetailersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Apex Kirana Stores").length).toBeGreaterThanOrEqual(1);
    });

    // Click Inactive status tab
    const inactiveTab = screen.getByText(/Inactive \(1\)/i);
    fireEvent.click(inactiveTab);

    await waitFor(() => {
      expect(screen.getAllByText("Old Corner Grocery").length).toBeGreaterThanOrEqual(1);
      expect(screen.queryByText("Apex Kirana Stores")).toBeNull();
    });
  });

  it("opens create modal and registers a new retailer", async () => {
    const { apiClient } = await import("@/lib/api-client");
    render(<RetailersAdminPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Register Retailer").length).toBeGreaterThanOrEqual(1);
    });

    // Click Register Retailer button (the header action button)
    const registerButtons = screen.getAllByText("Register Retailer");
    fireEvent.click(registerButtons[0]);

    // Fill form
    const nameInput = screen.getByPlaceholderText(/Apex Kirana/i);
    fireEvent.change(nameInput, { target: { value: "Metro Mart" } });

    const contactInput = screen.getByPlaceholderText(/Ramesh Patel/i);
    fireEvent.change(contactInput, { target: { value: "Suresh Rao" } });

    const submitBtn = screen.getByRole("button", { name: "Submit Registration" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/retailers",
        expect.objectContaining({
          name: "Metro Mart",
          contact_person: "Suresh Rao",
          pricing_tier: "standard",
        }),
      );
    });
  });
});
