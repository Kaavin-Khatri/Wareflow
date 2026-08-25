import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { OfflineBanner } from "@/components/pwa/OfflineBanner";
import { SyncQueueModal } from "@/components/pwa/SyncQueueModal";
import { ThemeProvider } from "@/components/ThemeProvider";
import Topbar from "@/components/Topbar";
import * as offlineQueue from "@/lib/offline-queue";

// Mock Next.js router
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
  }),
}));

// Mock Firebase
vi.mock("@/lib/firebase-client", () => ({
  db: {},
}));

// Mock apiClient
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({}),
    patch: vi.fn().mockResolvedValue({}),
  },
}));

describe("PWA Offline Shell & Sync Queue UI Suite (Step 19.1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
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

  it("renders OfflineBanner when offline or when queue items are pending", async () => {
    vi.spyOn(offlineQueue, "getPendingQueueCount").mockResolvedValue(2);
    vi.spyOn(offlineQueue, "getAllQueueItems").mockResolvedValue([
      {
        id: "item-1",
        action_type: "stock_adjustment",
        title: "Adjust -5 Ratlam Sev",
        endpoint: "/stock/adjustments",
        method: "POST",
        payload: {},
        timestamp: new Date().toISOString(),
        status: "pending",
      },
    ]);

    const handleOpen = vi.fn();
    render(<OfflineBanner onOpenSyncQueue={handleOpen} />);

    await waitFor(() => {
      expect(screen.getByText("Offline Changes Pending")).toBeDefined();
      expect(screen.getByText("Sync Queue (2)")).toBeDefined();
    });

    fireEvent.click(screen.getByText("Sync Queue (2)"));
    expect(handleOpen).toHaveBeenCalledTimes(1);
  });

  it("renders SyncQueueModal with pending items and triggers Sync Now", async () => {
    const mockItems: offlineQueue.OfflineQueueItem[] = [
      {
        id: "adj-1",
        action_type: "stock_adjustment",
        title: "Stock adjustment: -10 Basmati Rice",
        endpoint: "/stock/adjustments",
        method: "POST",
        payload: { delta: -10 },
        timestamp: new Date().toISOString(),
        status: "pending",
      },
    ];

    vi.spyOn(offlineQueue, "getAllQueueItems").mockResolvedValue(mockItems);
    const flushSpy = vi.spyOn(offlineQueue, "flushOfflineQueue").mockResolvedValue({
      synced: 1,
      conflicts: 0,
      failed: 0,
    });

    render(<SyncQueueModal isOpen={true} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Offline Sync Queue")).toBeDefined();
      expect(screen.getByText("Stock adjustment: -10 Basmati Rice")).toBeDefined();
      expect(screen.getByText("Queued")).toBeDefined();
    });

    const syncBtn = screen.getByText("Sync Now");
    fireEvent.click(syncBtn);

    await waitFor(() => {
      expect(flushSpy).toHaveBeenCalled();
    });
  });

  it("renders conflict card with server discrepancy details and resolution actions", async () => {
    const mockConflictItem: offlineQueue.OfflineQueueItem[] = [
      {
        id: "conflict-1",
        action_type: "stock_adjustment",
        title: "Stock adjustment: -50 Moong Dal",
        endpoint: "/stock/adjustments",
        method: "POST",
        payload: { delta: -50 },
        timestamp: new Date().toISOString(),
        status: "conflict",
        error_message: "Batch balance was altered on server (current balance: 20 units).",
        conflict_details: {
          server_message: "Batch balance was altered on server (current balance: 20 units).",
        },
      },
    ];

    vi.spyOn(offlineQueue, "getAllQueueItems").mockResolvedValue(mockConflictItem);
    const resolveSpy = vi.spyOn(offlineQueue, "resolveConflict").mockResolvedValue();

    render(<SyncQueueModal isOpen={true} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Conflict Detected")).toBeDefined();
      expect(screen.getByText("Server Stock Discrepancy")).toBeDefined();
      expect(
        screen.getByText("Batch balance was altered on server (current balance: 20 units).")
      ).toBeDefined();
      expect(screen.getByText("Discard Action")).toBeDefined();
      expect(screen.getByText("Re-apply Against Current Stock")).toBeDefined();
    });

    fireEvent.click(screen.getByText("Re-apply Against Current Stock"));
    expect(resolveSpy).toHaveBeenCalledWith("conflict-1", "reapply");
  });

  it("renders Topbar with Sync Queue trigger button", () => {
    render(
      <ThemeProvider>
        <Topbar />
      </ThemeProvider>
    );
    expect(screen.getByTestId("sync-queue-trigger")).toBeDefined();
  });
});
