"use client";

import React, { useEffect, useState } from "react";
import { WifiOff, RefreshCw, Layers, AlertTriangle } from "lucide-react";
import {
  getPendingQueueCount,
  subscribeToQueueChanges,
  getAllQueueItems,
} from "@/lib/offline-queue";

interface OfflineBannerProps {
  onOpenSyncQueue?: () => void;
}

export function OfflineBanner({ onOpenSyncQueue }: OfflineBannerProps) {
  const [isOffline, setIsOffline] = useState<boolean>(false);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [hasConflicts, setHasConflicts] = useState<boolean>(false);

  const updateStatus = async () => {
    if (typeof window !== "undefined") {
      setIsOffline(!navigator.onLine);
    }
    const count = await getPendingQueueCount();
    setPendingCount(count);

    const all = await getAllQueueItems();
    setHasConflicts(all.some((i) => i.status === "conflict"));
  };

  useEffect(() => {
    updateStatus();

    const handleOnline = () => updateStatus();
    const handleOffline = () => updateStatus();

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    const unsub = subscribeToQueueChanges(() => updateStatus());

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      unsub();
    };
  }, []);

  // Show banner if offline OR if there are pending actions / conflicts
  if (!isOffline && pendingCount === 0 && !hasConflicts) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 max-w-xl w-[92vw] animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div
        className={`p-3.5 rounded-2xl border backdrop-blur-xl shadow-2xl flex items-center justify-between gap-3 text-xs transition-colors ${
          hasConflicts
            ? "bg-rose-950/90 border-rose-500/40 text-rose-200"
            : isOffline
              ? "bg-amber-950/90 border-amber-500/40 text-amber-200"
              : "bg-purple-950/90 border-purple-500/40 text-purple-200"
        }`}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div
            className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
              hasConflicts
                ? "bg-rose-500/20 text-rose-400"
                : isOffline
                  ? "bg-amber-500/20 text-amber-400"
                  : "bg-purple-500/20 text-purple-400"
            }`}
          >
            {hasConflicts ? (
              <AlertTriangle className="w-4 h-4" />
            ) : isOffline ? (
              <WifiOff className="w-4 h-4" />
            ) : (
              <Layers className="w-4 h-4" />
            )}
          </div>

          <div className="min-w-0">
            <span className="font-bold block truncate">
              {hasConflicts
                ? "Sync Conflict Requires Review"
                : isOffline
                  ? "Offline Mode Active"
                  : "Offline Changes Pending"}
            </span>
            <p className="text-[11px] opacity-90 truncate">
              {hasConflicts
                ? "Server batch balances changed during offline disconnect."
                : isOffline
                  ? `WiFi unavailable. ${pendingCount} floor action(s) safely queued.`
                  : `${pendingCount} action(s) ready to sync to server.`}
            </p>
          </div>
        </div>

        {onOpenSyncQueue && (
          <button
            type="button"
            onClick={onOpenSyncQueue}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs shrink-0 border shadow-sm transition-all ${
              hasConflicts
                ? "bg-rose-600 hover:bg-rose-500 text-white border-rose-400"
                : isOffline
                  ? "bg-amber-600 hover:bg-amber-500 text-white border-amber-400"
                  : "bg-purple-600 hover:bg-purple-500 text-white border-purple-400"
            }`}
          >
            Sync Queue ({pendingCount})
          </button>
        )}
      </div>
    </div>
  );
}
