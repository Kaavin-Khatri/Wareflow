import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  enqueueOfflineAction,
  getAllQueueItems,
  getPendingQueueCount,
  removeQueueItem,
  resolveConflict,
  flushOfflineQueue,
  clearCompletedItems,
} from "@/lib/offline-queue";

describe("IndexedDB Offline Action Queue Engine (Step 19.1)", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    // Clear in-memory queue
    const all = await getAllQueueItems();
    for (const item of all) {
      await removeQueueItem(item.id);
    }
  });

  it("enqueues a stock adjustment with pending status and FIFO timestamp", async () => {
    const item = await enqueueOfflineAction(
      "stock_adjustment",
      "Stock adjustment: -5 Ratlam Sev (Damage)",
      "/stock/adjustments",
      {
        product_id: "prod-1",
        warehouse_id: "wh-1",
        batch_id: "batch-1",
        delta: -5,
        reason: "damage",
      }
    );

    expect(item.id).toBeDefined();
    expect(item.action_type).toBe("stock_adjustment");
    expect(item.status).toBe("pending");
    expect(item.payload.delta).toBe(-5);

    const pendingCount = await getPendingQueueCount();
    expect(pendingCount).toBe(1);
  });

  it("maintains FIFO ordering for multiple queued actions", async () => {
    await enqueueOfflineAction("stock_adjustment", "Action 1", "/stock/adjustments", { delta: -1 });
    await enqueueOfflineAction("stock_transfer", "Action 2", "/stock/transfers", { quantity: 10 });
    await enqueueOfflineAction("barcode_scan_lookup", "Action 3", "/products/by-barcode/123", {});

    const items = await getAllQueueItems();
    expect(items.length).toBe(3);
    expect(items[0].title).toBe("Action 1");
    expect(items[1].title).toBe("Action 2");
    expect(items[2].title).toBe("Action 3");
  });

  it("flushes queue successfully when server accepts requests", async () => {
    await enqueueOfflineAction("stock_adjustment", "Adj 1", "/stock/adjustments", { delta: -2 });

    // Mock successful fetch
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "ok" }),
    });

    const result = await flushOfflineQueue("http://localhost:8000");
    expect(result.synced).toBe(1);
    expect(result.conflicts).toBe(0);

    const items = await getAllQueueItems();
    expect(items[0].status).toBe("completed");
  });

  it("surfaces conflict when server rejects action due to changed batch balance", async () => {
    await enqueueOfflineAction("stock_adjustment", "Conflict Adj", "/stock/adjustments", {
      product_id: "prod-1",
      delta: -20,
    });

    // Mock 422 Unprocessable Content balance error
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({ detail: "Insufficient stock balance in target batch." }),
    });

    const result = await flushOfflineQueue("http://localhost:8000");
    expect(result.synced).toBe(0);
    expect(result.conflicts).toBe(1);

    const items = await getAllQueueItems();
    expect(items[0].status).toBe("conflict");
    expect(items[0].error_message).toContain("Insufficient stock balance");
    expect(items[0].conflict_details?.server_message).toBe(
      "Insufficient stock balance in target batch."
    );
  });

  it("allows user to discard or reapply conflict items", async () => {
    const item = await enqueueOfflineAction("stock_adjustment", "Bad Adj", "/stock/adjustments", {
      delta: -10,
    });

    // Discard
    await resolveConflict(item.id, "discard");
    const afterDiscard = await getAllQueueItems();
    expect(afterDiscard.length).toBe(0);

    // Enqueue & Reapply
    const item2 = await enqueueOfflineAction(
      "stock_adjustment",
      "Reapply Adj",
      "/stock/adjustments",
      { delta: -5 }
    );
    await resolveConflict(item2.id, "reapply", { delta: -3 });

    const afterReapply = await getAllQueueItems();
    expect(afterReapply[0].status).toBe("pending");
    expect(afterReapply[0].payload.delta).toBe(-3);
  });
});
