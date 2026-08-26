import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { Sidebar } from "@/components/Sidebar";

// Mock Next Navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/inventory",
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
  }),
}));

// Mock API client
vi.mock("@/lib/api-client", () => ({
  getAuthToken: async () => "mock_token",
  apiClient: {
    get: vi.fn().mockResolvedValue({
      id: "u-101",
      email: "owner@wareflow.io",
      display_name: "Kaavin Khatri",
      role_name: "Owner",
      permissions: ["*"],
    }),
  },
}));

describe("Sidebar Navigation UI Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render brand header and domain section accordions", async () => {
    await act(async () => {
      render(<Sidebar />);
    });

    expect(screen.getByText("WareFlow")).toBeDefined();
    expect(screen.getByText("Wholesale ERP")).toBeDefined();
    expect(screen.getByText("Overview")).toBeDefined();
    expect(screen.getByText("Inventory & Catalog")).toBeDefined();
    expect(screen.getByText("Purchasing & Inward")).toBeDefined();
    expect(screen.getByText("Sales & CRM")).toBeDefined();
    expect(screen.getByText("Finance & Billing")).toBeDefined();
  });

  it("should filter navigation items dynamically when typing in search input", async () => {
    await act(async () => {
      render(<Sidebar />);
    });

    const searchInput = screen.getByPlaceholderText("Search tools & modules...");
    expect(searchInput).toBeDefined();

    await act(async () => {
      fireEvent.change(searchInput, { target: { value: "Invoices" } });
    });

    // Should find GST Invoices
    expect(screen.getByText("GST Invoices")).toBeDefined();

    // Clear search
    const clearBtn = screen.getByLabelText("Clear Search");
    await act(async () => {
      fireEvent.click(clearBtn);
    });

    expect((searchInput as HTMLInputElement).value).toBe("");
  });

  it("should allow toggling accordion sections open and closed", async () => {
    await act(async () => {
      render(<Sidebar />);
    });

    // Find the Finance & Billing section toggle button
    const financeSectionBtn = screen.getByRole("button", { name: /Finance & Billing/i });
    expect(financeSectionBtn).toBeDefined();

    // Click to collapse
    await act(async () => {
      fireEvent.click(financeSectionBtn);
    });

    // Click to expand again
    await act(async () => {
      fireEvent.click(financeSectionBtn);
    });
  });
});
