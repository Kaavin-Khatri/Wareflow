"use client";

import { useEffect, useState } from "react";
import { auth } from "@/lib/firebase-client";
import { onAuthStateChanged } from "firebase/auth";

interface OrderItem {
  id: string;
  so_number: string;
  status: string;
  order_date: string;
  total_amount: number;
  items_count: number;
  created_at: string;
}

export default function PortalOrdersPage() {
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) return;
      try {
        const idToken = await user.getIdToken();
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/portal/orders`, {
          headers: { Authorization: `Bearer ${idToken}` },
        });
        if (res.ok) {
          const data = await res.json();
          setOrders(data);
        } else {
          setError("Failed to load your orders.");
        }
      } catch (err) {
        console.warn("Orders fetch error:", err);
        setError("Network error fetching orders.");
      } finally {
        setLoading(false);
      }
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">My Sales Orders</h1>
          <p className="text-sm text-slate-400 mt-1">
            Track and monitor the status of wholesale orders placed with your distributor.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center p-12">
          <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
        </div>
      ) : orders.length === 0 ? (
        <div className="p-12 rounded-3xl bg-white/[0.02] border border-white/10 text-center text-slate-400">
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center mx-auto mb-3 text-xl">
            📋
          </div>
          <h3 className="text-base font-semibold text-slate-200">No Orders Found</h3>
          <p className="text-xs text-slate-400 mt-1">You haven&apos;t placed any wholesale sales orders yet.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60 backdrop-blur-xl">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-white/10 bg-white/5 text-xs uppercase font-semibold text-slate-400">
              <tr>
                <th className="px-6 py-3.5">SO Number</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Total Amount</th>
                <th className="px-6 py-3.5">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-white/5 transition-colors">
                  <td className="px-6 py-4 font-mono font-medium text-white">{o.so_number}</td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 rounded-full text-xs font-medium uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      {o.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono font-semibold text-emerald-400">
                    ₹{o.total_amount.toLocaleString("en-IN")}
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-400">
                    {o.order_date ? new Date(o.order_date).toLocaleDateString("en-IN") : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
