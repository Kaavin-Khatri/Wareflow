import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { PageHeader } from "@/components/PageHeader";
import { AnimatedNumber } from "@/components/motion/AnimatedNumber";
import { Topbar } from "@/components/Topbar";
import { Sidebar } from "@/components/Sidebar";
import { AppLayout } from "@/components/AppLayout";
import { ThemeProvider } from "@/components/ThemeProvider";

// Mock Next Navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
  }),
}));

// Mock API client
vi.mock("@/lib/api-client", () => ({
  getAuthToken: async () => "test_token",
  apiClient: {
    get: vi.fn().mockResolvedValue({
      id: "u-1",
      email: "owner@wareflow.internal",
      display_name: "Master Admin",
      role_name: "Owner",
      permissions: ["*"],
    }),
  },
}));

describe("Dashboard Shell & Layout Suite", () => {
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
  });

  describe("PageHeader", () => {
    it("should render title, description, and action button", () => {
      render(
        <PageHeader
          title="Inventory Ledger"
          description="Real-time FIFO stock balance."
          primaryAction={<button type="button">New Batch</button>}
        />,
      );

      expect(screen.getByText("Inventory Ledger")).toBeDefined();
      expect(screen.getByText("Real-time FIFO stock balance.")).toBeDefined();
      expect(screen.getByText("New Batch")).toBeDefined();
    });

    it("should render back link when backHref is provided", () => {
      render(<PageHeader title="PO Details" backHref="/purchasing" backLabel="Back to PO List" />);

      expect(screen.getByText("Back to PO List")).toBeDefined();
    });
  });

  describe("AnimatedNumber", () => {
    it("should render formatted currency and suffix", () => {
      render(<AnimatedNumber value={845200} prefix="₹" suffix=" Total" />);
      expect(screen.getByText(/₹/)).toBeDefined();
    });

    it("should render immediate number under reduced-motion preference", () => {
      window.matchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === "(prefers-reduced-motion: reduce)",
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      render(<AnimatedNumber value={500} prefix="SKU-" />);
      expect(screen.getByText("SKU-500")).toBeDefined();
    });
  });

  describe("Topbar", () => {
    it("should render brand, settlement badge, and notification toggle", async () => {
      await act(async () => {
        render(
          <ThemeProvider>
            <Topbar onMenuClick={vi.fn()} />
          </ThemeProvider>,
        );
      });

      expect(screen.getByText("WareFlow")).toBeDefined();
      expect(screen.getByText("0.02s Settlement")).toBeDefined();

      const notifBtn = screen.getByLabelText("Notifications");
      await act(async () => {
        fireEvent.click(notifBtn);
      });
      expect(screen.getByText("Live Notifications")).toBeDefined();
    });
  });

  describe("Sidebar", () => {
    it("should render brand header and desktop navigation container", async () => {
      await act(async () => {
        render(<Sidebar />);
      });
      expect(screen.getByText("WareFlow")).toBeDefined();
    });

    it("should render mobile drawer container when mobileOpen is true", async () => {
      const handleClose = vi.fn();
      await act(async () => {
        render(<Sidebar mobileOpen={true} onMobileClose={handleClose} />);
      });
      const closeButtons = screen.getAllByLabelText("Close Sidebar");
      expect(closeButtons.length).toBeGreaterThan(0);
    });
  });

  describe("AppLayout", () => {
    it("should render children within the responsive dashboard frame", async () => {
      await act(async () => {
        render(
          <ThemeProvider>
            <AppLayout>
              <div data-testid="dashboard-content">Hello Dashboard</div>
            </AppLayout>
          </ThemeProvider>,
        );
      });

      expect(screen.getByTestId("dashboard-content")).toBeDefined();
      expect(screen.getByText("Hello Dashboard")).toBeDefined();
    });
  });
});
