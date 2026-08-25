"use client";

import React, { useEffect, useState } from "react";
import {
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ArrowRightLeft,
  Barcode,
  Trash2,
  AlertCircle,
  X,
  Play,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassButton } from "@/components/glass/GlassButton";
import {
  getAllQueueItems,
  removeQueueItem,
  resolveConflict,
  clearCompletedItems,
  flushOfflineQueue,
  subscribeToQueueChanges,
  OfflineQueueItem,
} from "@/lib/offline-queue";

interface SyncQueueModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SyncQueueModal({ isOpen, onClose }: SyncQueueModalProps) {
  const [items, setItems] = useState<OfflineQueueItem[]>([]);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  const loadItems = async () => {
    const list = await getAllQueueItems();
    setItems(list);
  };

  useEffect(() => {
    if (isOpen) {
      loadItems();
    }
    const unsub = subscribeToQueueChanges(() => {
      loadItems();
    });
    return unsub;
  }, [isOpen]);

  const handleSyncNow = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await flushOfflineQueue();
      if (res.conflicts > 0) {
        setSyncResult(
          `Sync complete: ${res.synced} succeeded, ${res.conflicts} conflict(s) require review.`,
        );
      } else if (res.failed > 0) {
        setSyncResult(`Sync complete: ${res.synced} succeeded, ${res.failed} network errors.`);
      } else {
        setSyncResult(`All ${res.synced} offline action(s) synced successfully!`);
      }
    } catch (err: any) {
      setSyncResult(`Sync failed: ${err.message || "Unknown error"}`);
    } finally {
      setSyncing(false);
      loadItems();
    }
  };

  const handleDiscard = async (id: string) => {
    await removeQueueItem(id);
    loadItems();
  };

  const handleReapply = async (id: string) => {
    await resolveConflict(id, "reapply");
    handleSyncNow();
  };

  const handleClearCompleted = async () => {
    await clearCompletedItems();
    loadItems();
  };

  const pendingCount = items.filter((i) => i.status === "pending" || i.status === "syncing").length;
  const conflictCount = items.filter((i) => i.status === "conflict").length;
  const completedCount = items.filter((i) => i.status === "completed").length;

  return (
    <GlassModal isOpen={isOpen} onClose={onClose} title="Offline Sync Queue" maxWidth="lg">
      <div className="space-y-5">
        {/* Header Summary Strip */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-[var(--surface-hover)] border border-[var(--border)]">
          <div className="flex items-center gap-4 text-xs font-mono">
            <div>
              <span className="text-[var(--text-muted)] text-[10px] uppercase block">Pending</span>
              <span className="text-amber-400 font-bold text-sm">{pendingCount}</span>
            </div>
            <div className="h-6 w-px bg-[var(--border)]" />
            <div>
              <span className="text-[var(--text-muted)] text-[10px] uppercase block">
                Conflicts
              </span>
              <span className="text-rose-400 font-bold text-sm">{conflictCount}</span>
            </div>
            <div className="h-6 w-px bg-[var(--border)]" />
            <div>
              <span className="text-[var(--text-muted)] text-[10px] uppercase block">Synced</span>
              <span className="text-emerald-400 font-bold text-sm">{completedCount}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {completedCount > 0 && (
              <button
                type="button"
                onClick={handleClearCompleted}
                className="px-2.5 py-1.5 rounded-xl text-xs text-[var(--text-muted)] hover:text-[var(--text)] border border-[var(--border)] bg-[var(--surface)] transition-colors"
              >
                Clear Synced
              </button>
            )}
            <GlassButton
              variant="primary"
              size="sm"
              onClick={handleSyncNow}
              disabled={syncing || (pendingCount === 0 && conflictCount === 0)}
              className="font-bold flex items-center gap-1.5 shadow-md"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} />
              <span>{syncing ? "Syncing..." : "Sync Now"}</span>
            </GlassButton>
          </div>
        </div>

        {/* Sync Result Banner */}
        {syncResult && (
          <div
            className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
              syncResult.includes("conflict")
                ? "bg-rose-500/10 border border-rose-500/30 text-rose-300"
                : "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300"
            }`}
          >
            {syncResult.includes("conflict") ? (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            )}
            <span>{syncResult}</span>
          </div>
        )}

        {/* Item List */}
        <div className="space-y-3 max-h-[55vh] overflow-y-auto pr-1">
          {items.length === 0 ? (
            <div className="py-12 text-center text-xs text-[var(--text-muted)] space-y-2">
              <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-400 opacity-60" />
              <p>Your offline sync queue is empty. All floor actions are up to date!</p>
            </div>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className={`p-4 rounded-2xl border transition-all ${
                  item.status === "conflict"
                    ? "bg-rose-950/20 border-rose-500/40 shadow-sm"
                    : item.status === "completed"
                      ? "bg-emerald-950/10 border-emerald-500/20 opacity-80"
                      : "bg-[var(--glass-bg)] border-[var(--border)]"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                        item.action_type === "stock_adjustment"
                          ? "bg-purple-500/20 text-purple-400"
                          : item.action_type === "stock_transfer"
                            ? "bg-cyan-500/20 text-cyan-400"
                            : "bg-amber-500/20 text-amber-400"
                      }`}
                    >
                      {item.action_type === "stock_adjustment" && <Layers className="w-4 h-4" />}
                      {item.action_type === "stock_transfer" && (
                        <ArrowRightLeft className="w-4 h-4" />
                      )}
                      {item.action_type === "barcode_scan_lookup" && (
                        <Barcode className="w-4 h-4" />
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-xs font-bold text-[var(--text)]">{item.title}</h4>
                        {item.status === "pending" && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            Queued
                          </span>
                        )}
                        {item.status === "syncing" && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center gap-1">
                            <RefreshCw className="w-2.5 h-2.5 animate-spin" /> Syncing
                          </span>
                        )}
                        {item.status === "completed" && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            Synced
                          </span>
                        )}
                        {item.status === "conflict" && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
                            Conflict Detected
                          </span>
                        )}
                      </div>

                      <p className="text-[11px] font-mono text-[var(--text-muted)]">
                        {item.method} {item.endpoint} •{" "}
                        {new Date(item.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>

                  {item.status !== "conflict" && (
                    <button
                      type="button"
                      onClick={() => handleDiscard(item.id)}
                      className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                      title="Discard queued item"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Conflict Card Detail & Resolution Options */}
                {item.status === "conflict" && (
                  <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 space-y-2 text-xs">
                    <div className="flex items-start gap-2 text-rose-300">
                      <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                      <div className="space-y-0.5">
                        <span className="font-bold block">Server Stock Discrepancy</span>
                        <p className="text-[11px] text-rose-200/90 leading-relaxed">
                          {item.error_message ||
                            "Batch balance was altered on the server while this device was offline. To protect inventory accuracy, automatic overwrite is blocked."}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-1 border-t border-rose-500/20">
                      <button
                        type="button"
                        onClick={() => handleDiscard(item.id)}
                        className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-neutral-900 border border-white/10 text-[var(--text-muted)] hover:text-white transition-colors"
                      >
                        Discard Action
                      </button>
                      <button
                        type="button"
                        onClick={() => handleReapply(item.id)}
                        className="px-3 py-1.5 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white transition-colors flex items-center gap-1 shadow-md"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Re-apply Against Current Stock</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-[var(--border)] text-[11px] text-[var(--text-muted)]">
          <span>Safe scope: Stock adjustments, transfers & scan lookups only.</span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)] text-[var(--text)] font-semibold hover:bg-[var(--surface)] transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </GlassModal>
  );
}
