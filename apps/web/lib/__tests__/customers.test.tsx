import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import CustomersPage from "@/app/admin/customers/page";
import { apiClient } from "@/lib/api-client";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/customers",
  useSearchParams: () => new URLSearchParams(),
}));

const MOCK_CUSTOMERS_DATA = [
  {
    id: "cust-1",
    name: "Ramesh Gupta",
    phone: "+91 98765 43210",
    email: "ramesh.gupta@gmail.com",
    address: "Shop 4, Chandni Chowk, Delhi - 110006",
    notes: "Walk-in cash buyer for bulk spices",
    created_at: "2026-08-01T10:00:00Z",
    total_orders_count: 3,
    total_spend: 14500,
  },
  {
    id: "cust-2",
    name: "Sunita Sharma",
    phone: "+91 98112 23344",
    email: "sunita.sharma@yahoo.com",
    address: "B-42, Sector 18, Noida, UP",
    notes: "Regular retail walk-in",
    created_at: "2026-08-10T12:00:00Z",
    total_orders_count: 2,
    total_spend: 8200,
  },
];

// Mock apiClient
vi.mock("@/lib/api-client", () => ({
  getAuthToken: async () => "test_token",
  apiClient: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url === "/customers") return Promise.resolve(MOCK_CUSTOMERS_DATA);
      return Promise.resolve([]);
    }),
    post: vi
      .fn()
      .mockImplementation(
        (
          url: string,
          body: { name?: string; phone?: string; email?: string; address?: string; notes?: string },
        ) => {
          if (url === "/customers") {
            return Promise.resolve({
              id: "cust-3",
              name: body.name || "Customer",
              phone: body.phone,
              email: body.email,
              address: body.address,
              notes: body.notes,
              created_at: new Date().toISOString(),
              total_orders_count: 0,
              total_spend: 0,
            });
          }
          return Promise.resolve({});
        },
      ),
    patch: vi
      .fn()
      .mockImplementation(
        (
          url: string,
          body: { name?: string; phone?: string; email?: string; address?: string; notes?: string },
        ) => {
          return Promise.resolve({
            ...MOCK_CUSTOMERS_DATA[0],
            ...body,
          });
        },
      ),
    delete: vi.fn().mockResolvedValue(true),
  },
}));

describe("Customers Admin Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders customer KPIs and table records correctly", async () => {
    render(<CustomersPage />);

    await waitFor(() => {
      expect(
        screen.getAllByText("Direct Customers & Walk-In Buyers").length,
      ).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Ramesh Gupta").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Sunita Sharma").length).toBeGreaterThanOrEqual(1);
    });

    // Check KPIs
    expect(screen.getAllByText("Direct Customers").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Active Buyers").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Direct Orders Placed").length).toBeGreaterThanOrEqual(1);
  });

  it("filters customer records by search query", async () => {
    render(<CustomersPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Ramesh Gupta").length).toBeGreaterThanOrEqual(1);
    });

    const searchInput = screen.getByPlaceholderText(/Search customers by name/i);
    fireEvent.change(searchInput, { target: { value: "Sunita" } });

    expect(screen.getAllByText("Sunita Sharma").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("Ramesh Gupta")).toBeNull();
  });

  it("opens create modal and registers a new direct customer", async () => {
    render(<CustomersPage />);

    const addBtn = screen.getByRole("button", { name: /Add Direct Customer/i });
    fireEvent.click(addBtn);

    expect(screen.getAllByText("Register Direct Walk-In Customer").length).toBeGreaterThanOrEqual(
      1,
    );

    fireEvent.change(screen.getByLabelText(/Customer Name \*/i), {
      target: { value: "Anil Verma" },
    });
    fireEvent.change(screen.getByLabelText(/Phone Number/i), {
      target: { value: "+91 99887 76655" },
    });
    fireEvent.change(screen.getByLabelText(/Email Address/i), {
      target: { value: "anil.verma@example.com" },
    });

    const submitBtn = screen.getByRole("button", { name: /Register Customer/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/customers",
        expect.objectContaining({
          name: "Anil Verma",
          phone: "+91 99887 76655",
          email: "anil.verma@example.com",
        }),
      );
    });
  });

  it("opens edit modal and updates customer details", async () => {
    render(<CustomersPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Ramesh Gupta").length).toBeGreaterThanOrEqual(1);
    });

    const editBtns = screen.getAllByTitle("Edit Customer");
    fireEvent.click(editBtns[0]);

    expect(screen.getAllByText(/Edit Customer — Ramesh Gupta/i).length).toBeGreaterThanOrEqual(1);

    const notesInput = screen.getByLabelText(/Internal Notes/i);
    fireEvent.change(notesInput, { target: { value: "Prefers morning deliveries" } });

    const updateBtn = screen.getByRole("button", { name: /Update Profile/i });
    fireEvent.click(updateBtn);

    await waitFor(() => {
      expect(apiClient.patch).toHaveBeenCalledWith(
        "/customers/cust-1",
        expect.objectContaining({
          notes: "Prefers morning deliveries",
        }),
      );
    });
  });
});
