"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { signOut } from "firebase/auth";
import { auth } from "@/lib/firebase-client";

export default function DashboardPage() {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await signOut(auth);
    } catch {
      // ignore
    }
    await fetch("/api/auth/session", { method: "DELETE" });
    router.push("/login");
    router.refresh();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-emerald-500/30 selection:text-emerald-300">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-tr from-emerald-500 to-teal-400 font-bold text-slate-950">
              W
            </div>
            <span className="text-lg font-bold text-white tracking-tight">WareFlow</span>
          </div>
          <button
            onClick={handleLogout}
            className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 transition-all hover:bg-slate-700 hover:text-white"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto max-w-7xl px-6 py-10">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8 shadow-xl">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Wholesale Command Center</h1>
              <p className="text-sm text-slate-400">
                Session authenticated via Firebase • Server-side session cookie active
              </p>
            </div>
          </div>

          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-5">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Authentication
              </span>
              <p className="mt-2 text-sm font-medium text-emerald-400">Firebase Verified</p>
            </div>
            <div className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-5">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Session Security
              </span>
              <p className="mt-2 text-sm font-medium text-emerald-400">httpOnly Cookie</p>
            </div>
            <div className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-5">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                RBAC Level
              </span>
              <p className="mt-2 text-sm font-medium text-emerald-400">Server Enforced</p>
            </div>
          </div>

          <div className="mt-8 flex gap-4">
            <Link
              href="/debug"
              className="rounded-xl bg-emerald-500 px-4 py-2.5 text-xs font-semibold text-slate-950 transition-all hover:bg-emerald-400"
            >
              System Health & DB Probe
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
