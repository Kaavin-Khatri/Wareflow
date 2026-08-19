"use client";

import { useEffect, useState } from "react";
import { auth } from "@/lib/firebase-client";
import { onAuthStateChanged } from "firebase/auth";

interface InvoiceItem {
  id: string;
  invoice_number: string;
  sales_order_id: string;
  status: string;
  issue_date: string;
  due_date: string;
  total_amount: number;
  paid_amount: number;
  outstanding_balance: number;
  e_invoice_irn?: string;
  e_way_bill_no?: string;
}

interface LedgerEntry {
  date: string;
  entry_type: "debit_invoice" | "credit_payment";
  reference_no: string;
  description: string;
  debit: number;
  credit: number;
  running_balance: number;
}

interface LedgerResponse {
  retailer_id: string;
  retailer_name: string;
  current_balance: number;
  entries: LedgerEntry[];
}

export default function PortalInvoicesPage() {
  const [invoices, setInvoices] = useState<InvoiceItem[]>([]);
  const [ledger, setLedger] = useState<LedgerResponse | null>(null);
  const [tab, setTab] = useState<"invoices" | "ledger">("invoices");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) return;
      try {
        const idToken = await user.getIdToken();
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

        // Fetch Invoices
        const invRes = await fetch(`${apiUrl}/portal/invoices`, {
          headers: { Authorization: `Bearer ${idToken}` },
        });
        if (invRes.ok) {
          const invData = await invRes.json();
          setInvoices(invData);
        }

        // Fetch Ledger
        const ledgerRes = await fetch(`${apiUrl}/portal/ledger`, {
          headers: { Authorization: `Bearer ${idToken}` },
        });
        if (ledgerRes.ok) {
          const ledgerData = await ledgerRes.json();
          setLedger(ledgerData);
        }
      } catch (err) {
        console.warn("Error fetching invoices/ledger:", err);
        setError("Failed to load invoice statements.");
      } finally {
        setLoading(false);
      }
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Invoices & Statements</h1>
          <p className="text-sm text-slate-400 mt-1">
            Review GST tax invoices, payment settlements, and chronological credit statement.
          </p>
        </div>

        <div className="flex rounded-xl bg-white/5 p-1 border border-white/10">
          <button
            onClick={() => setTab("invoices")}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              tab === "invoices"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Invoices ({invoices.length})
          </button>
          <button
            onClick={() => setTab("ledger")}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              tab === "ledger"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Account Statement
          </button>
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
      ) : tab === "invoices" ? (
        invoices.length === 0 ? (
          <div className="p-12 rounded-3xl bg-white/[0.02] border border-white/10 text-center text-slate-400">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center mx-auto mb-3 text-xl">
              🧾
            </div>
            <h3 className="text-base font-semibold text-slate-200">No Invoices</h3>
            <p className="text-xs text-slate-400 mt-1">No GST invoices have been issued to your account yet.</p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60 backdrop-blur-xl">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="border-b border-white/10 bg-white/5 text-xs uppercase font-semibold text-slate-400">
                <tr>
                  <th className="px-6 py-3.5">Invoice #</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Total Amount</th>
                  <th className="px-6 py-3.5">Outstanding</th>
                  <th className="px-6 py-3.5">Due Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-white/5 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-white">
                      <div>{inv.invoice_number}</div>
                      {inv.e_invoice_irn && (
                        <span className="text-[10px] text-emerald-400">GST E-Invoice Active</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 rounded-full text-xs font-medium uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono">₹{inv.total_amount.toLocaleString("en-IN")}</td>
                    <td className="px-6 py-4 font-mono font-semibold text-rose-400">
                      ₹{inv.outstanding_balance.toLocaleString("en-IN")}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {inv.due_date ? new Date(inv.due_date).toLocaleDateString("en-IN") : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : (
        /* Account Ledger Table */
        <div className="space-y-4">
          {ledger && (
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between">
              <span className="text-xs text-slate-400">Current Outstanding Balance:</span>
              <span className="font-mono text-base font-bold text-rose-400">
                ₹{ledger.current_balance.toLocaleString("en-IN")}
              </span>
            </div>
          )}

          <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60 backdrop-blur-xl">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="border-b border-white/10 bg-white/5 text-xs uppercase font-semibold text-slate-400">
                <tr>
                  <th className="px-6 py-3.5">Date</th>
                  <th className="px-6 py-3.5">Reference</th>
                  <th className="px-6 py-3.5">Description</th>
                  <th className="px-6 py-3.5 text-right">Debit (+)</th>
                  <th className="px-6 py-3.5 text-right">Credit (-)</th>
                  <th className="px-6 py-3.5 text-right">Running Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono text-xs">
                {ledger && ledger.entries.length > 0 ? (
                  ledger.entries.map((entry, idx) => (
                    <tr key={idx} className="hover:bg-white/5 transition-colors">
                      <td className="px-6 py-3 text-slate-400">
                        {entry.date ? new Date(entry.date).toLocaleDateString("en-IN") : "-"}
                      </td>
                      <td className="px-6 py-3 font-semibold text-white">{entry.reference_no}</td>
                      <td className="px-6 py-3 font-sans text-slate-300">{entry.description}</td>
                      <td className="px-6 py-3 text-right text-rose-400">
                        {entry.debit > 0 ? `₹${entry.debit.toLocaleString("en-IN")}` : "-"}
                      </td>
                      <td className="px-6 py-3 text-right text-emerald-400">
                        {entry.credit > 0 ? `₹${entry.credit.toLocaleString("en-IN")}` : "-"}
                      </td>
                      <td className="px-6 py-3 text-right font-bold text-white">
                        ₹{entry.running_balance.toLocaleString("en-IN")}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500 font-sans">
                      No ledger transactions recorded yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
