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

interface StaffMember {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  phone: string | null;
  role_id: string;
  role_name: string;
  is_active: boolean;
  created_at: string;
}

export default function StaffSettingsPage() {
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [roles, setRoles] = useState<RoleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Invite Form State
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [phone, setPhone] = useState("");
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    async function fetchData() {
      try {
        const [staffData, rolesData] = await Promise.all([
          apiClient.get<StaffMember[]>("/staff"),
          apiClient.get<RoleSummary[]>("/roles"),
        ]);
        if (!ignore) {
          setStaff(staffData);
          setRoles(rolesData);
          if (rolesData.length > 0) {
            setSelectedRoleId((prev) => {
              if (prev) return prev;
              const defaultRole = rolesData.find((r) => r.name !== "Owner") || rolesData[0];
              return defaultRole.id;
            });
          }
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load staff list or roles.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      ignore = true;
    };
  }, []);

  const refreshData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [staffData, rolesData] = await Promise.all([
        apiClient.get<StaffMember[]>("/staff"),
        apiClient.get<RoleSummary[]>("/roles"),
      ]);
      setStaff(staffData);
      setRoles(rolesData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to refresh staff data.");
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !selectedRoleId) return;

    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await apiClient.post("/staff/invite", {
        email,
        display_name: displayName || null,
        phone: phone || null,
        role_id: selectedRoleId,
      });

      setSuccessMessage(`Invitation sent to ${email}!`);
      setEmail("");
      setDisplayName("");
      setPhone("");
      await refreshData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to invite staff member.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRoleChange = async (profileId: string, newRoleId: string) => {
    try {
      await apiClient.patch(`/staff/${profileId}/role`, { role_id: newRoleId });
      setStaff((prev) =>
        prev.map((s) => {
          if (s.id === profileId) {
            const role = roles.find((r) => r.id === newRoleId);
            return { ...s, role_id: newRoleId, role_name: role ? role.name : s.role_name };
          }
          return s;
        }),
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update role");
    }
  };

  const handleToggleStatus = async (profileId: string, currentStatus: boolean) => {
    try {
      await apiClient.patch(`/staff/${profileId}/status`, { is_active: !currentStatus });
      setStaff((prev) =>
        prev.map((s) => (s.id === profileId ? { ...s, is_active: !currentStatus } : s)),
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to toggle status");
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Staff Management</h1>
          <p className="text-sm text-zinc-400 mt-1">
            Invite organization team members, assign operational roles, and manage system access.
          </p>
        </div>

        {/* Alerts */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-rose-400 hover:text-white">
              ✕
            </button>
          </div>
        )}

        {successMessage && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center justify-between">
            <span>{successMessage}</span>
            <button
              onClick={() => setSuccessMessage(null)}
              className="text-emerald-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        )}

        {/* Invite Form Card */}
        <div className="p-6 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 backdrop-blur-sm">
          <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <span>➕</span> Invite New Staff Member
          </h2>
          <form onSubmit={handleInvite} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1.5">Work Email *</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="colleague@wareflow.com"
                className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-950 border border-zinc-800 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1.5">Full Name</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Ramesh Patel"
                className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-950 border border-zinc-800 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1.5">
                Role Assignment *
              </label>
              <select
                value={selectedRoleId}
                onChange={(e) => setSelectedRoleId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-950 border border-zinc-800 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <button
                type="submit"
                disabled={submitting || !email || !selectedRoleId}
                className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition shadow-sm shadow-indigo-600/30 flex items-center justify-center gap-2"
              >
                {submitting ? "Inviting..." : "Send Invitation"}
              </button>
            </div>
          </form>
        </div>

        {/* Staff Table */}
        <div className="rounded-2xl bg-zinc-900/60 border border-zinc-800/80 overflow-hidden backdrop-blur-sm">
          <div className="p-5 border-b border-zinc-800/80 flex items-center justify-between">
            <h2 className="text-base font-semibold text-white">Active Team ({staff.length})</h2>
            <button
              onClick={refreshData}
              className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 rounded-lg bg-zinc-800/50 hover:bg-zinc-800 transition"
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="p-8 text-center text-zinc-500 text-sm animate-pulse">
              Loading team directory...
            </div>
          ) : staff.length === 0 ? (
            <div className="p-8 text-center text-zinc-500 text-sm">No staff members found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-zinc-800/60 text-xs font-semibold text-zinc-400 bg-zinc-950/40">
                    <th className="py-3.5 px-6">Member</th>
                    <th className="py-3.5 px-6">Assigned Role</th>
                    <th className="py-3.5 px-6">Account Status</th>
                    <th className="py-3.5 px-6">Joined Date</th>
                    <th className="py-3.5 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/40 text-zinc-300">
                  {staff.map((member) => (
                    <tr key={member.id} className="hover:bg-zinc-800/20 transition">
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-xl bg-zinc-800 border border-zinc-700/50 flex items-center justify-center font-bold text-zinc-200 text-xs uppercase">
                            {member.display_name
                              ? member.display_name.charAt(0)
                              : member.email.charAt(0)}
                          </div>
                          <div>
                            <span className="font-semibold text-white block">
                              {member.display_name || "Unnamed"}
                            </span>
                            <span className="text-xs text-zinc-400 block">{member.email}</span>
                          </div>
                        </div>
                      </td>

                      <td className="py-4 px-6">
                        <select
                          value={member.role_id}
                          onChange={(e) => handleRoleChange(member.id, e.target.value)}
                          className="px-2.5 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-xs font-medium text-zinc-200 focus:outline-none focus:border-indigo-500"
                        >
                          {roles.map((r) => (
                            <option key={r.id} value={r.id}>
                              {r.name}
                            </option>
                          ))}
                        </select>
                      </td>

                      <td className="py-4 px-6">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                            member.is_active
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              member.is_active ? "bg-emerald-400" : "bg-rose-400"
                            }`}
                          />
                          {member.is_active ? "Active" : "Suspended"}
                        </span>
                      </td>

                      <td className="py-4 px-6 text-xs text-zinc-400">
                        {new Date(member.created_at).toLocaleDateString("en-IN", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })}
                      </td>

                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => handleToggleStatus(member.id, member.is_active)}
                          className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                            member.is_active
                              ? "text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10"
                              : "text-zinc-400 hover:text-emerald-400 hover:bg-emerald-500/10"
                          }`}
                        >
                          {member.is_active ? "Deactivate" : "Activate"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
