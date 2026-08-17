"use client";

import Link from "next/link";
import AppLayout from "@/components/AppLayout";

export default function DashboardPage() {
  return (
    <AppLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Wholesale Command Center</h1>
          <p className="text-sm text-zinc-400 mt-1">
            Real-time wholesale operations, team access control, and inventory management.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6 backdrop-blur-sm">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Authentication Engine
            </span>
            <p className="mt-2 text-base font-bold text-emerald-400">Firebase Verified</p>
            <span className="text-xs text-zinc-400 mt-1 block">Google + Apple + Password</span>
          </div>

          <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6 backdrop-blur-sm">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Session Protection
            </span>
            <p className="mt-2 text-base font-bold text-indigo-400">httpOnly Cookie</p>
            <span className="text-xs text-zinc-400 mt-1 block">Server-Side Verified</span>
          </div>

          <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6 backdrop-blur-sm">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Access Matrix
            </span>
            <p className="mt-2 text-base font-bold text-amber-400">Data-Driven RBAC</p>
            <span className="text-xs text-zinc-400 mt-1 block">Real-time DB Permissions</span>
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6 backdrop-blur-sm">
          <h2 className="text-base font-semibold text-white mb-4">Quick Administration Actions</h2>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/admin/settings/staff"
              className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition shadow-sm shadow-indigo-600/30"
            >
              👥 Manage Staff Members
            </Link>
            <Link
              href="/admin/settings/permissions"
              className="px-4 py-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white font-medium text-xs transition"
            >
              🛡️ Role Permission Matrix
            </Link>
            <Link
              href="/debug"
              className="px-4 py-2.5 rounded-xl bg-zinc-800/60 hover:bg-zinc-800 text-zinc-300 hover:text-white font-medium text-xs transition"
            >
              ⚡ System Health Probe
            </Link>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
