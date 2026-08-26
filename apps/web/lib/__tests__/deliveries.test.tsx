import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import DeliveriesPage from "@/app/admin/deliveries/page";
import { apiClient } from "@/lib/api-client";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
  usePathname: () => "/admin/deliveries",
}));

// Mock AppLayout
vi.mock("@/components/AppLayout", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock API Client
vi.mock("@/lib/api-client", () => ({
  getAuthToken: async () => "test_token",
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

describe("Delivery & Logistics Status Board (/admin/deliveries)", () => {
  const mockDeliveries = [
    {
      id: "del-1",
      sales_order_id: "so-101",
      so_number: "SO-2026-0101",
      buyer_name: "Alpha Supermarket",
      destination_address: "Andheri East, Mumbai",
      driver_name: "Ramesh Kumar",
      vehicle_no: "MH-02-AB-1234",
      status: "assigned",
      total_amount: 4500.0,
      dispatched_at: null,
      delivered_at: null,
      notes: "Handle carefully",
      created_at: "2026-08-19T10:00:00Z",
    },
    {
      id: "del-2",
      sales_order_id: "so-102",
      so_number: "SO-2026-0102",
      buyer_name: "Beta Provision Store",
      destination_address: "Kothrud, Pune",
      driver_name: "Suresh Patil",
      vehicle_no: "MH-12-XY-9999",
      status: "out_for_delivery",
      total_amount: 8200.0,
      dispatched_at: "2026-08-19T11:00:00Z",
      delivered_at: null,
      notes: null,
      created_at: "2026-08-19T10:30:00Z",
    },
    {
      id: "del-3",
      sales_order_id: "so-103",
      so_number: "SO-2026-0103",
      buyer_name: "Gamma Retail Mart",
      destination_address: "Connaught Place, New Delhi",
      driver_name: "Amit Singh",
      vehicle_no: "DL-01-AA-5555",
      status: "delivered",
      total_amount: 12000.0,
      dispatched_at: "2026-08-19T08:00:00Z",
      delivered_at: "2026-08-19T09:30:00Z",
      notes: "Received and signed by manager",
      created_at: "2026-08-19T07:30:00Z",
    },
    {
      id: "del-4",
      sales_order_id: "so-104",
      so_number: "SO-2026-0104",
      buyer_name: "Delta Wholesale Hub",
      destination_address: "Sector 18, Noida",
      driver_name: "Rajesh Sharma",
      vehicle_no: "UP-16-QQ-1122",
      status: "failed",
      total_amount: 6700.0,
      dispatched_at: "2026-08-19T09:00:00Z",
      delivered_at: null,
      notes: "Store closed for festival holiday",
      created_at: "2026-08-19T08:30:00Z",
    },
  ];

  const mockPackedOrders = [
    {
      id: "so-packed-99",
      so_number: "SO-2026-0099",
      buyer_name: "Epsilon Traders",
      retailer_name: "Epsilon Traders",
      total_amount: 3400.0,
      status: "packed",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.startsWith("/deliveries")) {
        return Promise.resolve(mockDeliveries as never);
      }
      if (url.startsWith("/sales-orders")) {
        return Promise.resolve(mockPackedOrders as never);
      }
      return Promise.resolve([] as never);
    });
  });

  it("should render page header, KPI summary metrics, and 4 Kanban status columns", async () => {
    render(<DeliveriesPage />);

    expect(await screen.findByText("Delivery & Logistics Board")).toBeDefined();
    expect(screen.getByText("Phase 12")).toBeDefined();

    // Check Kanban column headers
    expect(screen.getByText(/Assigned \(1\)/i)).toBeDefined();
    expect(screen.getByText(/In Transit \(1\)/i)).toBeDefined();
    expect(screen.getByText(/Delivered \(1\)/i)).toBeDefined();
    expect(screen.getByText(/Exceptions \(1\)/i)).toBeDefined();

    // Check delivery cards rendered
    expect(screen.getByText("SO-2026-0101")).toBeDefined();
    expect(screen.getByText("Alpha Supermarket")).toBeDefined();
    expect(screen.getByText("Ramesh Kumar")).toBeDefined();
    expect(screen.getByText("MH-02-AB-1234")).toBeDefined();

    expect(screen.getByText("SO-2026-0102")).toBeDefined();
    expect(screen.getByText("Beta Provision Store")).toBeDefined();
  });

  it("should filter delivery cards by search input", async () => {
    render(<DeliveriesPage />);

    expect(await screen.findByText("SO-2026-0101")).toBeDefined();
    expect(screen.getByText("SO-2026-0102")).toBeDefined();

    const searchInput = screen.getByPlaceholderText(
      /Search by SO number, buyer, driver, or vehicle/i,
    );
    fireEvent.change(searchInput, { target: { value: "Alpha" } });

    expect(screen.getByText("SO-2026-0101")).toBeDefined();
    expect(screen.queryByText("SO-2026-0102")).toBeNull();
  });

  it("should transition assigned delivery to out_for_delivery when clicking Start Delivery", async () => {
    vi.mocked(apiClient.patch).mockResolvedValue({
      id: "del-1",
      status: "out_for_delivery",
    } as never);

    render(<DeliveriesPage />);

    const startBtn = await screen.findByRole("button", { name: /Start Delivery/i });
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(apiClient.patch).toHaveBeenCalledWith("/deliveries/del-1/status", {
        status: "out_for_delivery",
      });
    });
  });

  it("should transition in-transit delivery to delivered when clicking Delivered", async () => {
    vi.mocked(apiClient.patch).mockResolvedValue({
      id: "del-2",
      status: "delivered",
    } as never);

    render(<DeliveriesPage />);

    const deliveredBtn = await screen.findByRole("button", { name: /^Delivered$/i });
    fireEvent.click(deliveredBtn);

    await waitFor(() => {
      expect(apiClient.patch).toHaveBeenCalledWith("/deliveries/del-2/status", {
        status: "delivered",
      });
    });
  });

  it("should open fail modal and require reason before submitting failure status", async () => {
    vi.mocked(apiClient.patch).mockResolvedValue({
      id: "del-2",
      status: "failed",
      notes: "Road closed due to waterlogging",
    } as never);

    render(<DeliveriesPage />);

    const failedBtn = await screen.findByRole("button", { name: /^Failed$/i });
    fireEvent.click(failedBtn);

    expect(await screen.findByText(/Record Delivery Failure: SO-2026-0102/i)).toBeDefined();

    const reasonInput = screen.getByPlaceholderText(/e\.g\. Retailer store closed/i);
    fireEvent.change(reasonInput, { target: { value: "Road closed due to waterlogging" } });

    const submitFailBtn = screen.getByRole("button", { name: /Record Failure/i });
    fireEvent.click(submitFailBtn);

    await waitFor(() => {
      expect(apiClient.patch).toHaveBeenCalledWith("/deliveries/del-2/status", {
        status: "failed",
        notes: "Road closed due to waterlogging",
      });
    });
  });

  it("should open assign modal, select packed order, and submit new delivery dispatch", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      id: "del-new-1",
      sales_order_id: "so-packed-99",
      driver_name: "Deepak Verma",
      vehicle_no: "MH-04-AB-7788",
      status: "assigned",
    } as never);

    render(<DeliveriesPage />);

    const assignBtn = await screen.findByRole("button", { name: /Assign Delivery/i });
    fireEvent.click(assignBtn);

    expect(await screen.findByText("Assign Driver & Vehicle to Sales Order")).toBeDefined();

    const orderSelect = screen.getByLabelText(/Select Packed Sales Order/i);
    fireEvent.change(orderSelect, { target: { value: "so-packed-99" } });

    const driverInput = screen.getByLabelText(/Driver Name/i);
    fireEvent.change(driverInput, { target: { value: "Deepak Verma" } });

    const vehicleInput = screen.getByLabelText(/Vehicle Registration No\./i);
    fireEvent.change(vehicleInput, { target: { value: "MH-04-AB-7788" } });

    const submitBtn = screen.getByRole("button", { name: /Confirm & Dispatch/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith("/sales-orders/so-packed-99/delivery", {
        driver_name: "Deepak Verma",
        vehicle_no: "MH-04-AB-7788",
        notes: undefined,
      });
    });
  });
});
