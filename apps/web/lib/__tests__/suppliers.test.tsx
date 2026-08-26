import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import SuppliersAdminPage from "@/app/admin/suppliers/page";
import { ThemeProvider } from "@/components/ThemeProvider";
import { apiClient } from "@/lib/api-client";

// Mock Next Navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/suppliers",
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

const mockSuppliers = [
  {
    id: "sup-1",
    name: "Hindustan Unilever Ltd",
    contact_person: "Rajesh Sharma",
    phone: "+919876543210",
    email: "rajesh@hul.com",
    address: "Mumbai, Maharashtra",
    gstin: "27AAACH1234F1Z5",
    fssai_license_no: "10012022000123",
    fssai_expiry_date: "2028-12-31",
    is_active: true,
  },
  {
    id: "sup-2",
    name: "ITC Limited",
    contact_person: "Priya Sen",
    phone: "+919845012345",
    email: "priya@itc.in",
    address: "Kolkata, West Bengal",
    gstin: "19AAACI1681G1Z0",
    fssai_license_no: "10013011000456",
    fssai_expiry_date: "2027-06-30",
    is_active: false,
  },
];

describe("SuppliersAdminPage", () => {
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
      if (path.includes("/suppliers")) {
        return Promise.resolve(mockSuppliers);
      }
      if (path.includes("/me")) {
        return Promise.resolve({
          id: "user-1",
          email: "admin@wareflow.io",
          display_name: "Admin User",
          role_name: "Manager",
          permissions: ["inventory:view", "inventory:manage"],
        });
      }
      return Promise.resolve([]);
    });
  });

  it("renders supplier statistics and list items properly", async () => {
    render(
      <ThemeProvider>
        <SuppliersAdminPage />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByText("Hindustan Unilever Ltd").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("ITC Limited").length).toBeGreaterThanOrEqual(1);
    });

    // Check KPI counts
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(1); // Total vendors
    expect(screen.getAllByText("Active Vendor").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Inactive").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/27AAACH1234F1Z5/).length).toBeGreaterThanOrEqual(1);
  });

  it("filters suppliers by search query", async () => {
    render(
      <ThemeProvider>
        <SuppliersAdminPage />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByText("Hindustan Unilever Ltd").length).toBeGreaterThanOrEqual(1);
    });

    const searchInput = screen.getByPlaceholderText(
      "Search by name, contact person, email, or GSTIN...",
    );
    fireEvent.change(searchInput, { target: { value: "Unilever" } });

    expect(screen.getAllByText("Hindustan Unilever Ltd").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("ITC Limited")).toBeNull();
  });

  it("opens modal and submits new supplier", async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      id: "sup-3",
      name: "Nestle India Ltd",
      contact_person: "Sunil Varma",
      phone: "+919876500000",
      email: "sunil@nestle.in",
      address: "Gurugram, Haryana",
      gstin: "07AAACN1234N1Z1",
      fssai_license_no: "10014011000555",
      fssai_expiry_date: "2029-01-01",
      is_active: true,
    });

    render(
      <ThemeProvider>
        <SuppliersAdminPage />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByText("Hindustan Unilever Ltd").length).toBeGreaterThanOrEqual(1);
    });

    const addBtn = screen.getByRole("button", { name: /Add Supplier/i });
    fireEvent.click(addBtn);

    expect(screen.getByText("Register New Supplier")).toBeDefined();

    const nameInput = screen.getByPlaceholderText("e.g. Hindustan Unilever Ltd");
    fireEvent.change(nameInput, { target: { value: "Nestle India Ltd" } });

    const submitBtn = screen.getByRole("button", { name: "Create Supplier" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/suppliers",
        expect.objectContaining({
          name: "Nestle India Ltd",
          is_active: true,
        }),
      );
    });
  });
});
