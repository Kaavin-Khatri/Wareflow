"use client";

import Link from "next/link";

export default function PortalCatalogPage() {

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-slate-900/50 border border-white/10 backdrop-blur-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Wholesale Product Catalog</h1>
            <p className="text-sm text-slate-400 mt-1">
              Browse bulk wholesale inventory with tier-discounted pricing applied automatically.
            </p>
          </div>
          <Link
            href="/portal/orders"
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-lg shadow-indigo-600/25 transition-all flex items-center gap-2"
          >
            <span>View My Orders</span>
            <span>&rarr;</span>
          </Link>
        </div>
      </div>

      {/* Catalog Search & Filter Controls Placeholder */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <input
            type="text"
            placeholder="Search products by SKU, name, or brand..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500"
          />
          <span className="absolute left-3.5 top-3 text-slate-500">🔍</span>
        </div>
        <select className="w-full sm:w-48 px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40">
          <option value="">All Categories</option>
        </select>
      </div>

      {/* Product Catalog Grid Container */}
      <div className="p-12 rounded-3xl bg-white/[0.02] border border-white/10 text-center text-slate-400">
        <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center mx-auto mb-3 text-xl">
          📦
        </div>
        <h3 className="text-base font-semibold text-slate-200">Wholesale Catalog Live</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Tiered wholesale inventory and instant checkout will be available here with real-time stock sync.
        </p>
      </div>
    </div>
  );
}
