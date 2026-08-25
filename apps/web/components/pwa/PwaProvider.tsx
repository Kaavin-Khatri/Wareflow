"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { OfflineBanner } from "./OfflineBanner";
import { SyncQueueModal } from "./SyncQueueModal";
import {
  flushOfflineQueue,
  getPendingQueueCount,
  subscribeToQueueChanges,
  getAllQueueItems,
} from "@/lib/offline-queue";

interface PwaContextType {
  isOffline: boolean;
  pendingCount: number;
  hasConflicts: boolean;
  openSyncQueue: () => void;
  closeSyncQueue: () => void;
}

const PwaContext = createContext<PwaContextType>({
  isOffline: false,
  pendingCount: 0,
  hasConflicts: false,
  openSyncQueue: () => {},
  closeSyncQueue: () => {},
});

export const usePwa = () => useContext(PwaContext);

export function PwaProvider({ children }: { children: React.ReactNode }) {
  const [isOffline, setIsOffline] = useState<boolean>(false);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [hasConflicts, setHasConflicts] = useState<boolean>(false);
  const [isSyncModalOpen, setIsSyncModalOpen] = useState<boolean>(false);

  const refreshCounts = async () => {
    const count = await getPendingQueueCount();
    setPendingCount(count);
    const all = await getAllQueueItems();
    setHasConflicts(all.some((i) => i.status === "conflict"));
  };

  useEffect(() => {
    // 1. Service worker registration
    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/sw.js")
          .then((reg) => {
            console.log("[PWA] ServiceWorker registered with scope:", reg.scope);
          })
          .catch((err) => {
            console.warn("[PWA] ServiceWorker registration failed:", err);
          });
      });
    }

    // 2. Connectivity listeners
    const handleOnline = async () => {
      setIsOffline(false);
      console.log("[PWA] Connection restored. Flushing offline queue...");
      await flushOfflineQueue();
      refreshCounts();
    };

    const handleOffline = () => {
      setIsOffline(true);
      console.log("[PWA] Device went offline. Floor operations will be queued.");
      refreshCounts();
    };

    if (typeof window !== "undefined") {
      setIsOffline(!navigator.onLine);
    }
    refreshCounts();

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    const unsub = subscribeToQueueChanges(() => refreshCounts());

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      unsub();
    };
  }, []);

  return (
    <PwaContext.Provider
      value={{
        isOffline,
        pendingCount,
        hasConflicts,
        openSyncQueue: () => setIsSyncModalOpen(true),
        closeSyncQueue: () => setIsSyncModalOpen(false),
      }}
    >
      {children}
      <OfflineBanner onOpenSyncQueue={() => setIsSyncModalOpen(true)} />
      <SyncQueueModal isOpen={isSyncModalOpen} onClose={() => setIsSyncModalOpen(false)} />
    </PwaContext.Provider>
  );
}
