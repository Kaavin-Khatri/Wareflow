"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiClient } from "../lib/api-client";
import { filterNavSections, NAVIGATION_SECTIONS, NavSection } from "../lib/nav";

interface UserProfile {
  id: string;
  email: string;
  display_name?: string | null;
  role_name: string;
  permissions: string[];
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [filteredSections, setFilteredSections] = useState<NavSection[]>([]);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    async function loadUser() {
      try {
        const data = await apiClient.get<UserProfile>("/me");
        setProfile(data);
        const sections = filterNavSections(NAVIGATION_SECTIONS, data.permissions, data.role_name);
        setFilteredSections(sections);
      } catch (err) {
        console.warn("Failed to load user profile in sidebar:", err);
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, []);

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await fetch("/api/auth/session", { method: "DELETE" });
      router.push("/login");
      router.refresh();
    } catch {
      router.push("/login");
    }
  };

  const getRoleBadgeStyle = (role: string) => {
    switch (role?.toLowerCase()) {
      case "owner":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "manager":
        return "bg-blue-500/10 text-blue-400 border-blue-500/30";
      case "sales staff":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "warehouse staff":
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/30";
      case "accountant":
        return "bg-purple-500/10 text-purple-400 border-purple-500/30";
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700";
    }
  };

  return (
    <aside className="w-64 bg-zinc-950 border-r border-zinc-800/80 flex flex-col h-screen select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-zinc-800/80 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center shadow-lg shadow-indigo-500/20 font-black text-white text-base tracking-wider">
          W
        </div>
        <div>
          <span className="font-bold text-base tracking-tight text-white block">WareFlow</span>
          <span className="text-[11px] text-zinc-400 block font-medium">Wholesale ERP</span>
        </div>
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {loading ? (
          <div className="space-y-3 px-2">
            <div className="h-4 bg-zinc-800/50 rounded animate-pulse w-24 mb-3" />
            <div className="h-9 bg-zinc-800/30 rounded-lg animate-pulse" />
            <div className="h-9 bg-zinc-800/30 rounded-lg animate-pulse" />
            <div className="h-9 bg-zinc-800/30 rounded-lg animate-pulse" />
          </div>
        ) : (
          filteredSections.map((section) => (
            <div key={section.title} className="space-y-1">
              <h3 className="px-3 text-[11px] font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                {section.title}
              </h3>
              {section.items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/dashboard" && pathname.startsWith(item.href));

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? "bg-indigo-600 text-white font-semibold shadow-sm shadow-indigo-600/30"
                        : "text-zinc-400 hover:text-white hover:bg-zinc-900"
                    }`}
                  >
                    <span>{item.name}</span>
                    {item.badge && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          ))
        )}
      </div>

      {/* User Footer Profile & Sign Out */}
      <div className="p-3 border-t border-zinc-800/80 bg-zinc-900/40">
        <div className="p-2 rounded-xl bg-zinc-900/80 border border-zinc-800/60 mb-2">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center font-bold text-zinc-300 text-xs uppercase">
              {profile?.display_name ? profile.display_name.charAt(0) : "U"}
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-xs font-semibold text-zinc-200 block truncate">
                {profile?.display_name || profile?.email || "Signed In"}
              </span>
              <span
                className={`inline-block text-[10px] px-1.5 py-0.2 rounded border font-medium mt-0.5 ${getRoleBadgeStyle(
                  profile?.role_name || "",
                )}`}
              >
                {profile?.role_name || "Staff"}
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={handleLogout}
          disabled={loggingOut}
          className="w-full py-1.5 text-xs text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition text-center font-medium"
        >
          {loggingOut ? "Signing out..." : "Sign Out"}
        </button>
      </div>
    </aside>
  );
}
