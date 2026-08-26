"use client";

import { useCallback, useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { GlassSelect } from "@/components/glass/GlassSelect";
import { apiClient } from "@/lib/api-client";

interface AuditLogEntry {
  id: string;
  actor_id: string | null;
  actor_email: string | null;
  actor_name: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  description: string;
  before_value: Record<string, unknown> | null;
  after_value: Record<string, unknown> | null;
  created_at: string;
}

interface AuditLogResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function AdminAuditLogPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [entityFilter, setEntityFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected entry for diff inspection modal
  const [selectedEntry, setSelectedEntry] = useState<AuditLogEntry | null>(null);

  const loadLogs = useCallback(async (currentPage: number, entityType: string) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("page", currentPage.toString());
      params.set("page_size", "25");
      if (entityType) {
        params.set("entity_type", entityType);
      }

      const res = await apiClient.get<AuditLogResponse>(`/admin/audit-log?${params.toString()}`);
      setLogs(res.items);
      setTotal(res.total);
      setPage(res.page);
      setTotalPages(res.total_pages);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLogs(page, entityFilter);

    const handle2FAVerified = () => {
      setError(null);
      loadLogs(page, entityFilter);
    };

    window.addEventListener("wareflow:2fa-verified", handle2FAVerified);
    return () => {
      window.removeEventListener("wareflow:2fa-verified", handle2FAVerified);
    };
  }, [page, entityFilter, loadLogs]);

  const handleFilterChange = (val: string) => {
    setEntityFilter(val);
    setPage(1);
  };

  const getEntityBadgeStyle = (entityType: string) => {
    switch (entityType.toLowerCase()) {
      case "product":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "retailer":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "role_permissions":
        return "bg-purple-500/10 text-purple-400 border-purple-500/20";
      case "staff":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700";
    }
  };

  const getActionIcon = (action: string) => {
    if (action.includes("price")) {
      return (
        <span className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </span>
      );
    }
    if (action.includes("credit")) {
      return (
        <span className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
            />
          </svg>
        </span>
      );
    }
    if (action.includes("permission") || action.includes("role")) {
      return (
        <span className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        </span>
      );
    }
    return (
      <span className="p-2 rounded-xl bg-zinc-800 border border-zinc-700 text-zinc-400">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </span>
    );
  };

  return (
    <AppLayout>
      <div className="space-y-8 max-w-6xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              General Admin Action Audit Log
            </h1>
            <p className="text-sm text-zinc-400 mt-1">
              Immutable timeline of pricing changes, credit limits, staff access, and permission
              modifications.
            </p>
          </div>

          {/* Filter Bar */}
          <div className="flex items-center gap-3">
            <GlassSelect
              value={entityFilter}
              onChange={handleFilterChange}
              options={[
                { value: "", label: "All Entity Types" },
                { value: "product", label: "Products (Pricing)" },
                { value: "retailer", label: "Retailers (Credit Limits)" },
                { value: "role_permissions", label: "Permission Matrix" },
                { value: "staff", label: "Staff & Roles" },
              ]}
              className="w-56"
            />

            <button
              onClick={() => loadLogs(page, entityFilter)}
              className="px-3 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white hover:bg-zinc-800 text-xs font-medium transition cursor-pointer flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Refresh
            </button>
          </div>
        </div>

        {/* 2FA Verification Alert Banner */}
        {error && error.toLowerCase().includes("two-factor") && (
          <div className="p-5 rounded-2xl bg-indigo-500/10 border border-indigo-500/25 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg backdrop-blur-sm animate-fade-in">
            <div className="flex items-start sm:items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-500/30">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">Two-Factor Authentication Required</h4>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Administrative audit logs contain sensitive organizational records. Please verify your 2FA code to view this data.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                window.dispatchEvent(
                  new CustomEvent("wareflow:2fa-required", {
                    detail: { endpoint: "/admin/audit-log" },
                  }),
                );
              }}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition cursor-pointer shrink-0 self-start sm:self-auto"
            >
              Verify 2FA Now
            </button>
          </div>
        )}

        {/* General Error Alert */}
        {error && !error.toLowerCase().includes("two-factor") && (
          <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>{error}</span>
            </div>
            <button
              type="button"
              onClick={() => loadLogs(page, entityFilter)}
              className="px-3 py-1 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs font-medium transition cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {/* Timeline List */}
        {loading ? (
          <div className="p-16 text-center text-zinc-500 text-sm animate-pulse">
            Loading audit timeline...
          </div>
        ) : logs.length === 0 ? (
          <div className="p-16 text-center rounded-2xl bg-zinc-900/40 border border-zinc-800/80 space-y-3">
            <div className="w-12 h-12 mx-auto rounded-2xl bg-zinc-800/50 flex items-center justify-center text-zinc-500">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-zinc-300">No audit events recorded</h3>
            <p className="text-xs text-zinc-500 max-w-sm mx-auto">
              Sensitive operations such as price changes, credit adjustments, and role updates will
              appear here in real time.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {logs.map((log) => (
              <div
                key={log.id}
                className="group p-5 rounded-2xl bg-zinc-900/60 hover:bg-zinc-900/90 border border-zinc-800/80 transition shadow-lg backdrop-blur-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Event Summary */}
                <div className="flex items-start gap-3.5">
                  {getActionIcon(log.action)}
                  <div className="space-y-1">
                    <p className="text-sm text-zinc-100 font-medium leading-relaxed">
                      {log.description}
                    </p>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-400">
                      <span className="font-mono text-zinc-500">
                        {new Date(log.created_at).toLocaleString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                      <span>•</span>
                      <span
                        className={`px-2 py-0.5 rounded-md border text-[11px] font-medium capitalize ${getEntityBadgeStyle(log.entity_type)}`}
                      >
                        {log.entity_type.replace("_", " ")}
                      </span>
                      {log.actor_email && (
                        <>
                          <span>•</span>
                          <span className="text-zinc-400">by {log.actor_email}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Diff Inspect Button */}
                {(log.before_value || log.after_value) && (
                  <button
                    onClick={() => setSelectedEntry(log)}
                    className="shrink-0 px-3.5 py-1.5 rounded-xl bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 hover:text-white text-xs font-medium border border-zinc-700/60 transition flex items-center gap-1.5 cursor-pointer self-start md:self-center"
                  >
                    <svg
                      className="w-3.5 h-3.5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                      />
                    </svg>
                    Inspect Diff
                  </button>
                )}
              </div>
            ))}

            {/* Pagination Controls */}
            <div className="pt-4 flex items-center justify-between text-xs text-zinc-400">
              <div>
                Showing page <span className="font-semibold text-zinc-200">{page}</span> of{" "}
                <span className="font-semibold text-zinc-200">{totalPages}</span> ({total} total
                actions)
              </div>
              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 disabled:opacity-40 hover:bg-zinc-800 text-zinc-200 transition cursor-pointer"
                >
                  Previous
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                  className="px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 disabled:opacity-40 hover:bg-zinc-800 text-zinc-200 transition cursor-pointer"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Diff Inspection Modal */}
        {selectedEntry && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
            <div className="w-full max-w-2xl rounded-2xl bg-zinc-900 border border-zinc-800 p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                <div className="space-y-0.5">
                  <h3 className="text-base font-bold text-white">Audit Event Details</h3>
                  <p className="text-xs text-zinc-400">{selectedEntry.description}</p>
                </div>
                <button
                  onClick={() => setSelectedEntry(null)}
                  className="text-zinc-500 hover:text-white text-sm cursor-pointer"
                >
                  ✕
                </button>
              </div>

              {/* Before vs After Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-red-400 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                    Before State
                  </span>
                  <pre className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 text-xs font-mono text-zinc-300 overflow-x-auto max-h-60">
                    {JSON.stringify(selectedEntry.before_value, null, 2) || "null"}
                  </pre>
                </div>

                <div className="space-y-2">
                  <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    After State
                  </span>
                  <pre className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 text-xs font-mono text-zinc-300 overflow-x-auto max-h-60">
                    {JSON.stringify(selectedEntry.after_value, null, 2) || "null"}
                  </pre>
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => setSelectedEntry(null)}
                  className="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-medium transition cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
