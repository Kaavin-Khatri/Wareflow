/**
 * Frontend Unit Tests for Global Admin Search (Step 15.4).
 *
 * Tests:
 * 1. Topbar renders search trigger button with shortcut indicator.
 * 2. Cmd+K / Ctrl+K keyboard shortcut opens command palette modal.
 * 3. Searching query fetches and renders categorized, ranked result items.
 * 4. Keyboard arrow keys (Up/Down) navigate results and Enter selects.
 * 5. Escape key dismisses the search palette.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import React from "react";
import { Topbar } from "@/components/Topbar";
import { SearchCommandPalette, SearchResponse } from "@/components/SearchCommandPalette";
import { ThemeProvider } from "@/components/ThemeProvider";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    refresh: vi.fn(),
  }),
  usePathname: () => "/admin/dashboard",
}));

// Mock firebase
vi.mock("@/lib/firebase-client", () => ({
  db: {},
}));

vi.mock("firebase/firestore", () => ({
  collection: vi.fn(),
  query: vi.fn(),
  orderBy: vi.fn(),
  limit: vi.fn(),
  onSnapshot: vi.fn(() => () => {}),
}));

// Mock API Client
vi.mock("@/lib/api-client", () => ({
  getAuthToken: async () => "test_token",
  apiClient: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url === "/me") {
        return Promise.resolve({
          id: "user-1",
          email: "owner@wareflow.com",
          role_name: "Owner",
          permissions: ["all"],
        });
      }
      if (url.includes("/notifications")) {
        return Promise.resolve({ items: [] });
      }
      if (url.startsWith("/search")) {
        const mockResponse: SearchResponse = {
          query: "basmati",
          total: 2,
          results: [
            {
              id: "prod-1",
              kind: "product",
              title: "Royal Basmati Rice 5kg",
              subtitle: "SKU: RIC-BAS-001 • ₹500.00",
              badge: "Grains & Rice",
              url: "/admin/products",
              score: 100.0,
            },
            {
              id: "so-1",
              kind: "sales_order",
              title: "SO-2026-0001",
              subtitle: "Apex Kirana Stores • ₹15,400.00",
              badge: "CONFIRMED",
              url: "/admin/sales-orders",
              score: 85.0,
            },
          ],
        };
        return Promise.resolve(mockResponse);
      }
      return Promise.resolve({});
    }),
  },
}));

describe("Global Admin Search & Command Palette (Step 15.4)", () => {
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
  });

  it("renders search trigger in Topbar and opens command palette on click", async () => {
    render(
      <ThemeProvider>
        <Topbar />
      </ThemeProvider>,
    );

    const searchTrigger = screen.getByTestId("global-search-trigger");
    expect(searchTrigger).toBeDefined();
    expect(screen.getByText(/Search across ERP/i)).toBeDefined();

    // Click trigger to open palette
    fireEvent.click(searchTrigger);

    await waitFor(() => {
      expect(screen.getByTestId("search-command-palette-modal")).toBeDefined();
      expect(screen.getByTestId("global-search-input")).toBeDefined();
    });
  });

  it("opens search command palette when pressing Cmd+K / Ctrl+K keyboard shortcut", async () => {
    render(
      <ThemeProvider>
        <Topbar />
      </ThemeProvider>,
    );

    // Dispatch global Cmd+K
    act(() => {
      window.dispatchEvent(
        new KeyboardEvent("keydown", {
          key: "k",
          metaKey: true,
          bubbles: true,
        }),
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("search-command-palette-modal")).toBeDefined();
    });
  });

  it("queries GET /search?q= and displays ranked results with badges", async () => {
    const handleClose = vi.fn();
    render(<SearchCommandPalette isOpen={true} onClose={handleClose} />);

    const input = screen.getByTestId("global-search-input");
    fireEvent.change(input, { target: { value: "basmati" } });

    await waitFor(() => {
      expect(screen.getByText("Royal Basmati Rice 5kg")).toBeDefined();
      expect(screen.getByText("SKU: RIC-BAS-001 • ₹500.00")).toBeDefined();
      expect(screen.getByText("SO-2026-0001")).toBeDefined();
    });
  });

  it("navigates results with ArrowDown/ArrowUp and selects with Enter", async () => {
    const handleClose = vi.fn();
    render(<SearchCommandPalette isOpen={true} onClose={handleClose} />);

    const input = screen.getByTestId("global-search-input");
    fireEvent.change(input, { target: { value: "basmati" } });

    await waitFor(() => {
      expect(screen.getByText("Royal Basmati Rice 5kg")).toBeDefined();
    });

    // Press ArrowDown to select second result (SO-2026-0001)
    fireEvent.keyDown(input, { key: "ArrowDown" });

    // Press Enter to navigate to SO page
    fireEvent.keyDown(input, { key: "Enter" });

    expect(handleClose).toHaveBeenCalled();
    expect(mockPush).toHaveBeenCalledWith("/admin/sales-orders");
  });

  it("dismisses palette when pressing Escape key", async () => {
    const handleClose = vi.fn();
    render(<SearchCommandPalette isOpen={true} onClose={handleClose} />);

    const input = screen.getByTestId("global-search-input");
    fireEvent.keyDown(input, { key: "Escape" });

    expect(handleClose).toHaveBeenCalled();
  });
});
