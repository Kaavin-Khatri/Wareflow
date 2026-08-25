/**
 * IndexedDB Offline Action Queue & Conflict Engine
 *
 * Scope Boundary:
 * - Allowed offline actions: stock_adjustment, stock_transfer, barcode_scan_lookup
 * - Strictly online-only: sales/purchase order confirmations, invoice creation, payments
 */

import { openDB, IDBPDatabase } from "idb";

export type OfflineActionType = "stock_adjustment" | "stock_transfer" | "barcode_scan_lookup";

export type OfflineActionStatus = "pending" | "syncing" | "completed" | "conflict" | "failed";

export interface ConflictDetails {
  server_message?: string;
  current_server_balance?: number;
  intended_change?: number;
  product_name?: string;
  batch_number?: string;
  warehouse_name?: string;
}

export interface OfflineQueueItem {
  id: string;
  action_type: OfflineActionType;
  title: string;
  endpoint: string;
  method: "POST" | "PATCH" | "PUT";
  payload: Record<string, any>;
  timestamp: string;
  status: OfflineActionStatus;
  error_message?: string;
  conflict_details?: ConflictDetails;
}

const DB_NAME = "wareflow_offline_db";
const DB_VERSION = 1;
const STORE_NAME = "offline_queue";

// In-memory fallback for SSR or environments without IndexedDB
let memoryQueue: OfflineQueueItem[] = [];
const listeners: Array<() => void> = [];

function notifyListeners() {
  listeners.forEach((fn) => {
    try {
      fn();
    } catch (e) {
      console.error("[OfflineQueue] Listener error:", e);
    }
  });
}

export function subscribeToQueueChanges(callback: () => void): () => void {
  listeners.push(callback);
  return () => {
    const idx = listeners.indexOf(callback);
    if (idx !== -1) listeners.splice(idx, 1);
  };
}

async function getDB(): Promise<IDBPDatabase | null> {
  if (typeof window === "undefined" || !window.indexedDB) {
    return null;
  }
  try {
    return await openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: "id" });
          store.createIndex("status", "status");
          store.createIndex("timestamp", "timestamp");
        }
      },
    });
  } catch (err) {
    console.warn("[OfflineQueue] IndexedDB init fallback:", err);
    return null;
  }
}

export async function enqueueOfflineAction(
  actionType: OfflineActionType,
  title: string,
  endpoint: string,
  payload: Record<string, any>,
  method: "POST" | "PATCH" | "PUT" = "POST"
): Promise<OfflineQueueItem> {
  const item: OfflineQueueItem = {
    id: `queue-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
    action_type: actionType,
    title,
    endpoint,
    method,
    payload,
    timestamp: new Date().toISOString(),
    status: "pending",
  };

  const db = await getDB();
  if (db) {
    await db.put(STORE_NAME, item);
  } else {
    memoryQueue.push(item);
  }

  notifyListeners();
  return item;
}

export async function getAllQueueItems(): Promise<OfflineQueueItem[]> {
  const db = await getDB();
  if (db) {
    const items = await db.getAll(STORE_NAME);
    return items.sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }
  return [...memoryQueue].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
}

export async function getPendingQueueCount(): Promise<number> {
  const items = await getAllQueueItems();
  return items.filter((i) => i.status === "pending" || i.status === "conflict").length;
}

export async function removeQueueItem(id: string): Promise<void> {
  const db = await getDB();
  if (db) {
    await db.delete(STORE_NAME, id);
  } else {
    memoryQueue = memoryQueue.filter((i) => i.id !== id);
  }
  notifyListeners();
}

export async function updateQueueItem(item: OfflineQueueItem): Promise<void> {
  const db = await getDB();
  if (db) {
    await db.put(STORE_NAME, item);
  } else {
    const idx = memoryQueue.findIndex((i) => i.id === item.id);
    if (idx !== -1) memoryQueue[idx] = item;
    else memoryQueue.push(item);
  }
  notifyListeners();
}

export async function resolveConflict(
  id: string,
  resolution: "reapply" | "discard",
  overridePayload?: Record<string, any>
): Promise<void> {
  if (resolution === "discard") {
    await removeQueueItem(id);
    return;
  }

  const items = await getAllQueueItems();
  const item = items.find((i) => i.id === id);
  if (!item) return;

  item.status = "pending";
  item.error_message = undefined;
  item.conflict_details = undefined;
  if (overridePayload) {
    item.payload = { ...item.payload, ...overridePayload };
  }

  await updateQueueItem(item);
}

export async function clearCompletedItems(): Promise<void> {
  const items = await getAllQueueItems();
  const completed = items.filter((i) => i.status === "completed");
  for (const item of completed) {
    await removeQueueItem(item.id);
  }
}

/**
 * Flush all pending offline queue items in FIFO order.
 * Catches server conflicts (e.g. 409 / 422 negative balance or batch unavailable)
 * and marks them as 'conflict' with details for user review.
 */
export async function flushOfflineQueue(
  baseUrl: string = "http://localhost:8000"
): Promise<{
  synced: number;
  conflicts: number;
  failed: number;
}> {
  const items = await getAllQueueItems();
  const pending = items.filter((i) => i.status === "pending");

  let synced = 0;
  let conflicts = 0;
  let failed = 0;

  for (const item of pending) {
    item.status = "syncing";
    await updateQueueItem(item);

    try {
      // Build full URL
      const fullUrl = item.endpoint.startsWith("http")
        ? item.endpoint
        : `${baseUrl}${item.endpoint.startsWith("/") ? "" : "/"}${item.endpoint}`;

      // In browser, retrieve credentials/cookies automatically
      const res = await fetch(fullUrl, {
        method: item.method,
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(item.payload),
      });

      if (res.ok) {
        item.status = "completed";
        item.error_message = undefined;
        item.conflict_details = undefined;
        await updateQueueItem(item);
        synced++;
      } else {
        const errorData = await res.json().catch(() => ({ detail: "Server error" }));
        const detailMessage = typeof errorData.detail === "string"
          ? errorData.detail
          : JSON.stringify(errorData.detail || "Server rejected transaction");

        // Detect Conflict vs General Network Failure
        // 409 (Conflict), 422 (Unprocessable Content / Insufficient balance / batch closed)
        if (res.status === 409 || res.status === 422 || detailMessage.toLowerCase().includes("balance") || detailMessage.toLowerCase().includes("stock")) {
          item.status = "conflict";
          item.error_message = detailMessage;
          item.conflict_details = {
            server_message: detailMessage,
            product_name: item.payload.product_name || item.payload.product_id,
            intended_change: item.payload.quantity_change ?? item.payload.quantity,
            batch_number: item.payload.batch_number || item.payload.batch_id,
          };
          conflicts++;
        } else {
          item.status = "failed";
          item.error_message = detailMessage;
          failed++;
        }
        await updateQueueItem(item);
      }
    } catch (networkError: any) {
      console.warn("[OfflineQueue] Sync failed for item:", item.id, networkError);
      item.status = "pending"; // leave pending for next reconnection
      await updateQueueItem(item);
      failed++;
    }
  }

  notifyListeners();
  return { synced, conflicts, failed };
}
