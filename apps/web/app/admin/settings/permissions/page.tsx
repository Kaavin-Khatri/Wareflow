"use client";

import { useEffect, useState } from "react";
import AppLayout from "../../../../components/AppLayout";
import { apiClient } from "../../../../lib/api-client";

interface RoleSummary {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
}

interface PermissionSummary {
  id: string;
  code: string;
  description: string | null;
}

export default function PermissionsMatrixPage() {
  const [roles, setRoles] = useState<RoleSummary[]>([]);
  const [permissions, setPermissions] = useState<PermissionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingRoleId, setSavingRoleId] = useState<string | null>(null);
  const [lastSavedMessage, setLastSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    async function fetchMatrix() {
      try {
        const [rolesData, permsData] = await Promise.all([
          apiClient.get<RoleSummary[]>("/roles"),
          apiClient.get<PermissionSummary[]>("/permissions"),
        ]);
        if (!ignore) {
          setRoles(rolesData);
          setPermissions(permsData);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load permission matrix.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    fetchMatrix();

    return () => {
      ignore = true;
    };
  }, []);

  const refreshMatrix = async () => {
    setLoading(true);
    setError(null);
    try {
      const [rolesData, permsData] = await Promise.all([
        apiClient.get<RoleSummary[]>("/roles"),
        apiClient.get<PermissionSummary[]>("/permissions"),
      ]);
      setRoles(rolesData);
      setPermissions(permsData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to refresh permission matrix.");
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePermission = async (role: RoleSummary, permCode: string) => {
    if (role.name === "Owner") return; // Owner permissions cannot be revoked

    const hasPerm = role.permissions.includes(permCode);
    const newPerms = hasPerm
      ? role.permissions.filter((p) => p !== permCode)
      : [...role.permissions, permCode];

    // Optimistic UI Update
    setRoles((prev) => prev.map((r) => (r.id === role.id ? { ...r, permissions: newPerms } : r)));

    setSavingRoleId(role.id);
    setLastSavedMessage(null);

    try {
      await apiClient.patch(`/roles/${role.id}/permissions`, {
        permission_codes: newPerms,
      });
      setLastSavedMessage(`Permissions updated for ${role.name}!`);
      setTimeout(() => setLastSavedMessage(null), 3000);
    } catch (err: unknown) {
      // Revert on error
      setRoles((prev) =>
        prev.map((r) => (r.id === role.id ? { ...r, permissions: role.permissions } : r)),
      );
      setError(err instanceof Error ? err.message : "Failed to update role permissions.");
    } finally {
      setSavingRoleId(null);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Role Permissions Matrix
            </h1>
            <p className="text-sm text-zinc-400 mt-1">
              Configure fine-grained system permissions across operational roles in real time.
            </p>
          </div>
          {lastSavedMessage && (
            <div className="px-3.5 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold animate-fade-in flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              {lastSavedMessage}
            </div>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-rose-400 hover:text-white">
              ✕
            </button>
          </div>
        )}

        {/* Matrix Container */}
        <div className="rounded-2xl bg-zinc-900/60 border border-zinc-800/80 overflow-hidden backdrop-blur-sm shadow-xl">
          <div className="p-5 border-b border-zinc-800/80 flex items-center justify-between bg-zinc-950/40">
            <div>
              <h2 className="text-sm font-semibold text-white">Live Access Matrix</h2>
              <span className="text-xs text-zinc-400 block mt-0.5">
                Changes apply immediately to staff members with the corresponding role.
              </span>
            </div>
            <button
              onClick={refreshMatrix}
              className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 rounded-lg bg-zinc-800/50 hover:bg-zinc-800 transition"
            >
              Refresh Matrix
            </button>
          </div>

          {loading ? (
            <div className="p-12 text-center text-zinc-500 text-sm animate-pulse">
              Loading permission matrix...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-400 bg-zinc-950/80">
                    <th className="py-4 px-6 font-bold text-white min-w-[200px]">System Role</th>
                    {permissions.map((perm) => (
                      <th
                        key={perm.id}
                        className="py-4 px-4 font-semibold text-center whitespace-nowrap min-w-[130px]"
                        title={perm.description || perm.code}
                      >
                        <span className="block text-zinc-200">{perm.code}</span>
                        <span className="text-[10px] font-normal text-zinc-300 block truncate max-w-[120px]">
                          {perm.description}
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/40 text-zinc-300">
                  {roles.map((role) => {
                    const isOwner = role.name === "Owner";
                    const isSaving = savingRoleId === role.id;

                    return (
                      <tr
                        key={role.id}
                        className={`hover:bg-zinc-800/20 transition ${
                          isOwner ? "bg-amber-500/[0.02]" : ""
                        }`}
                      >
                        <td className="py-4 px-6 font-semibold">
                          <div className="flex items-center gap-2">
                            <span className="text-white text-sm">{role.name}</span>
                            {isOwner && (
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
                                ROOT
                              </span>
                            )}
                            {isSaving && (
                              <span className="text-[10px] text-indigo-400 animate-pulse font-normal">
                                Saving...
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] font-normal text-zinc-400 block mt-0.5">
                            {role.description || "Operational role"}
                          </span>
                        </td>

                        {permissions.map((perm) => {
                          const isChecked = isOwner || role.permissions.includes(perm.code);

                          return (
                            <td key={perm.id} className="py-4 px-4 text-center">
                              <label className="inline-flex items-center justify-center cursor-pointer p-2 rounded-lg hover:bg-zinc-800/40 transition">
                                <input
                                  type="checkbox"
                                  checked={isChecked}
                                  disabled={isOwner}
                                  onChange={() => handleTogglePermission(role, perm.code)}
                                  className="w-4 h-4 rounded border-zinc-700 bg-zinc-950 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-zinc-900 disabled:opacity-60 cursor-pointer disabled:cursor-not-allowed"
                                />
                              </label>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
