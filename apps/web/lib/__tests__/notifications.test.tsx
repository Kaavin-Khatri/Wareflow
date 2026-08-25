/**
 * Frontend Unit Tests for Topbar Real-Time Notifications (Step 13.1).
 *
 * Tests:
 * 1. Loads initial notifications & unread count from GET /notifications.
 * 2. Unread badge displays exact database unread count.
 * 3. Realtime Firestore onSnapshot listener prepends new alert and triggers floating toast.
 * 4. Dismissing notification calls PATCH /notifications/{id}/read and decrements badge.
 * 5. Clicking "Mark all read" calls PATCH /notifications/read-all and clears badge.
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { Topbar } from "@/components/Topbar";
import { ThemeProvider } from "@/components/ThemeProvider";

interface MockDocChange {
  type: string;
  doc: {
    id: string;
    data: () => Record<string, unknown>;
  };
}

interface MockSnapshot {
  docChanges: () => MockDocChange[];
}

let firestoreCallback: ((snapshot: MockSnapshot) => void) | null = null;

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock api-client
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(async (url: string) => {
      if (url === "/me") {
        return {
          id: "user-123",
          email: "manager@wareflow.io",
          display_name: "Operations Manager",
          role_name: "Manager",
          permissions: ["orders:view"],
        };
      }
      if (url.startsWith("/notifications")) {
        return {
          items: [
            {
              id: "notif-1",
              type: "low_stock",
              title: "Low Stock: Sharbati Wheat Flour",
              body: "10 bags remaining in Central Depot.",
              is_read: false,
              created_at: "2026-08-19T10:00:00Z",
            },
            {
              id: "notif-2",
              type: "delivery_success",
              title: "Delivery Completed: SO-2026-01",
              body: "Order received by Apex Kirana.",
              is_read: true,
              created_at: "2026-08-19T09:00:00Z",
            },
          ],
          total: 2,
          unread_count: 1,
        };
      }
      return null;
    }),
    patch: vi.fn(async (url: string) => {
      if (url.includes("/read-all")) {
        return { success: true, updated_count: 1 };
      }
      return { success: true };
    }),
  },
}));

// Mock firebase/firestore
vi.mock("firebase/firestore", () => ({
  getFirestore: vi.fn(() => ({})),
  collection: vi.fn(() => ({})),
  query: vi.fn(() => ({})),
  orderBy: vi.fn(() => ({})),
  limit: vi.fn(() => ({})),
  onSnapshot: vi.fn((_q, callback) => {
    firestoreCallback = callback;
    return () => {
      firestoreCallback = null;
    };
  }),
}));

describe("Real-time Topbar Notifications (Step 13.1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    firestoreCallback = null;

    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  it("renders notification bell and displays unread badge matching DB count", async () => {
    await act(async () => {
      render(
        <ThemeProvider>
          <Topbar />
        </ThemeProvider>,
      );
    });

    await waitFor(() => {
      const badge = screen.getByTestId("unread-badge");
      expect(badge).toBeDefined();
      expect(badge.textContent).toBe("1");
    });
  });

  it("opens notification dropdown showing list items and handles mark as read", async () => {
    const { apiClient } = await import("@/lib/api-client");

    await act(async () => {
      render(
        <ThemeProvider>
          <Topbar />
        </ThemeProvider>,
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("unread-badge")).toBeDefined();
    });

    const notifBtn = screen.getByLabelText("Notifications");
    await act(async () => {
      fireEvent.click(notifBtn);
    });

    expect(screen.getByText("Live Notifications")).toBeDefined();
    expect(screen.getByText("Low Stock: Sharbati Wheat Flour")).toBeDefined();
    expect(screen.getByText("Delivery Completed: SO-2026-01")).toBeDefined();

    // Dismiss first notification
    const dismissBtns = screen.getAllByLabelText("Dismiss Notification");
    await act(async () => {
      fireEvent.click(dismissBtns[0]);
    });

    expect(apiClient.patch).toHaveBeenCalledWith("/notifications/notif-1/read");
  });

  it("handles Mark all read action and clears unread badge", async () => {
    const { apiClient } = await import("@/lib/api-client");

    await act(async () => {
      render(
        <ThemeProvider>
          <Topbar />
        </ThemeProvider>,
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("unread-badge")).toBeDefined();
    });

    const notifBtn = screen.getByLabelText("Notifications");
    await act(async () => {
      fireEvent.click(notifBtn);
    });

    const markAllBtn = screen.getByRole("button", { name: /Mark all read/i });
    await act(async () => {
      fireEvent.click(markAllBtn);
    });

    expect(apiClient.patch).toHaveBeenCalledWith("/notifications/read-all");
    expect(screen.queryByTestId("unread-badge")).toBeNull();
  });

  it("receives instant realtime notification from Firestore onSnapshot listener and shows toast", async () => {
    await act(async () => {
      render(
        <ThemeProvider>
          <Topbar />
        </ThemeProvider>,
      );
    });

    await waitFor(() => {
      expect(firestoreCallback).not.toBeNull();
    });

    // Simulate incoming realtime Firestore push
    await act(async () => {
      if (firestoreCallback) {
        firestoreCallback({
          docChanges: () => [
            {
              type: "added",
              doc: {
                id: "realtime-notif-99",
                data: () => ({
                  id: "realtime-notif-99",
                  type: "fssai_expiry",
                  title: "FSSAI Expiry Alert: Supplier ABC",
                  body: "License expires in 2 days.",
                  is_read: false,
                  created_at: new Date().toISOString(),
                }),
              },
            },
          ],
        });
      }
    });

    // Toast alert should be rendered
    await waitFor(() => {
      expect(screen.getByText("FSSAI Expiry Alert: Supplier ABC")).toBeDefined();
      expect(screen.getByText("License expires in 2 days.")).toBeDefined();
    });

    // Unread badge count increments to 2
    const badge = screen.getByTestId("unread-badge");
    expect(badge.textContent).toBe("2");
  });
});
