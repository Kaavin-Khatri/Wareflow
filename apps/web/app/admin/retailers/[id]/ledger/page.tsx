"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import AppLayout from "@/components/AppLayout";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassInput } from "@/components/glass/GlassInput";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { apiClient } from "@/lib/api-client";
import {
  ArrowLeft,
  ReceiptText,
  FileText,
  CreditCard,
  PlusCircle,
  Printer,
  Download,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  IndianRupee,
  Calendar,
} from "lucide-react";

export interface LedgerEntry {
  id: string;
  date: string;
  entry_type: "invoice" | "payment";
  reference_no: string;
  description: string;
  debit_amount: number;
  credit_amount: number;
  running_balance: number;
  status: string;
}

export interface RetailerLedgerResponse {
  retailer_id: string;
  retailer_name: string;
  gstin: string | null;
  credit_limit: number;
  current_credit_balance: number;
  available_credit: number;
  total_invoiced: number;
  total_paid: number;
  entries: LedgerEntry[];
}

export interface InvoiceItem {
  id: string;
  invoice_no: string;
  invoice_date: string;
  total_amount: number;
  paid_amount: number;
  outstanding_balance: number;
  status: string;
}

export default function RetailerLedgerPage() {
  const params = useParams();
  const retailerId = params?.id as string;

  const [ledger, setLedger] = useState<RetailerLedgerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState<"all" | "invoice" | "payment">("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Payment Recording Modal State
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [invoices, setInvoices] = useState<InvoiceItem[]>([]);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [payAmount, setPayAmount] = useState<number>(0);
  const [payMethod, setPayMethod] = useState<string>("upi");
  const [payDate, setPayDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [payNote, setPayNote] = useState<string>("");
  const [submittingPayment, setSubmittingPayment] = useState(false);
  const [payFormError, setPayFormError] = useState<string | null>(null);

  const loadData = async () => {
    if (!retailerId) return;
    try {
      setLoading(true);
      setError(null);
      const [ledgerData, invoicesData] = await Promise.all([
        apiClient.get<RetailerLedgerResponse>(`/retailers/${retailerId}/ledger`),
        apiClient.get<{ items: InvoiceItem[] }>(
          `/invoices?retailer_id=${retailerId}&page_size=100`,
        ),
      ]);
      setLedger(ledgerData);
      setInvoices(invoicesData.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load retailer ledger.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function init() {
      if (!retailerId) return;
      try {
        setLoading(true);
        setError(null);
        const [ledgerData, invoicesData] = await Promise.all([
          apiClient.get<RetailerLedgerResponse>(`/retailers/${retailerId}/ledger`),
          apiClient.get<{ items: InvoiceItem[] }>(
            `/invoices?retailer_id=${retailerId}&page_size=100`,
          ),
        ]);
        if (!ignore) {
          setLedger(ledgerData);
          setInvoices(invoicesData.items || []);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load retailer ledger.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    init();
    return () => {
      ignore = true;
    };
  }, [retailerId]);

  const handleOpenRecordPayment = () => {
    setPayFormError(null);
    // Auto-select first unpaid invoice if available
    const unpaidInv = invoices.find((inv) => inv.status !== "paid" && inv.outstanding_balance > 0);
    if (unpaidInv) {
      setSelectedInvoiceId(unpaidInv.id);
      setPayAmount(unpaidInv.outstanding_balance);
    } else if (invoices.length > 0) {
      setSelectedInvoiceId(invoices[0].id);
      setPayAmount(invoices[0].outstanding_balance || invoices[0].total_amount);
    }
    setPayMethod("upi");
    setPayDate(new Date().toISOString().split("T")[0]);
    setPayNote("");
    setPaymentModalOpen(true);
  };

  const handleInvoiceChange = (invId: string) => {
    setSelectedInvoiceId(invId);
    const chosen = invoices.find((i) => i.id === invId);
    if (chosen) {
      setPayAmount(
        chosen.outstanding_balance > 0 ? chosen.outstanding_balance : chosen.total_amount,
      );
    }
  };

  const handleRecordPaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInvoiceId) {
      setPayFormError("Please select an invoice to apply the payment to.");
      return;
    }
    if (payAmount <= 0) {
      setPayFormError("Payment amount must be greater than zero.");
      return;
    }

    const chosenInv = invoices.find((i) => i.id === selectedInvoiceId);
    if (
      chosenInv &&
      chosenInv.outstanding_balance > 0 &&
      payAmount > chosenInv.outstanding_balance + 0.01
    ) {
      setPayFormError(
        `Payment amount (₹${payAmount.toLocaleString("en-IN")}) exceeds invoice outstanding balance (₹${chosenInv.outstanding_balance.toLocaleString("en-IN")}).`,
      );
      return;
    }

    try {
      setSubmittingPayment(true);
      setPayFormError(null);
      await apiClient.post(`/invoices/${selectedInvoiceId}/payments`, {
        amount: Number(payAmount),
        method: payMethod,
        paid_at: new Date(payDate).toISOString(),
        note: payNote.trim() || undefined,
      });

      setSuccess(`Payment of ₹${Number(payAmount).toLocaleString("en-IN")} recorded successfully.`);
      setPaymentModalOpen(false);
      await loadData();
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: unknown) {
      setPayFormError(err instanceof Error ? err.message : "Failed to record payment.");
    } finally {
      setSubmittingPayment(false);
    }
  };

  const exportCSV = () => {
    if (!ledger || !ledger.entries.length) return;
    const headers = [
      "Date",
      "Type",
      "Reference",
      "Description",
      "Debit (INR)",
      "Credit (INR)",
      "Running Balance (INR)",
      "Status",
    ];
    const rows = ledger.entries.map((e) => [
      new Date(e.date).toLocaleString("en-IN"),
      e.entry_type.toUpperCase(),
      e.reference_no,
      `"${e.description.replace(/"/g, '""')}"`,
      e.debit_amount.toFixed(2),
      e.credit_amount.toFixed(2),
      e.running_balance.toFixed(2),
      e.status,
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `statement_${ledger.retailer_name.replace(/\s+/g, "_")}_${new Date().toISOString().slice(0, 10)}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredEntries = useMemo(() => {
    if (!ledger) return [];
    return ledger.entries.filter((entry) => {
      if (typeFilter !== "all" && entry.entry_type !== typeFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return (
          entry.reference_no.toLowerCase().includes(q) ||
          entry.description.toLowerCase().includes(q) ||
          entry.status.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [ledger, typeFilter, searchQuery]);

  const columns: DataTableColumn<LedgerEntry>[] = [
    {
      key: "date",
      header: "Date & Time",
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-2">
          <Calendar className="w-3.5 h-3.5 text-[var(--text-muted)]" />
          <span className="text-xs font-mono text-[var(--text)]">
            {new Date(row.date).toLocaleString("en-IN", {
              day: "2-digit",
              month: "short",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>
      ),
    },
    {
      key: "entry_type",
      header: "Type",
      sortable: true,
      render: (row) =>
        row.entry_type === "invoice" ? (
          <span className="px-2.5 py-0.5 rounded-lg text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 inline-flex items-center gap-1.5">
            <FileText className="w-3 h-3" />
            Tax Invoice (Debit)
          </span>
        ) : (
          <span className="px-2.5 py-0.5 rounded-lg text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 inline-flex items-center gap-1.5">
            <CheckCircle2 className="w-3 h-3" />
            Payment (Credit)
          </span>
        ),
    },
    {
      key: "reference_no",
      header: "Reference #",
      sortable: true,
      render: (row) => (
        <span className="text-xs font-mono font-bold text-cyan-400">{row.reference_no}</span>
      ),
    },
    {
      key: "description",
      header: "Description",
      render: (row) => (
        <span className="text-xs text-[var(--text-muted)] truncate max-w-sm block">
          {row.description}
        </span>
      ),
    },
    {
      key: "debit_amount",
      header: "Debit (+ Charge)",
      align: "right",
      sortable: true,
      render: (row) => (
        <span
          className={`text-xs font-mono font-semibold ${row.debit_amount > 0 ? "text-rose-400" : "text-[var(--text-muted)]"}`}
        >
          {row.debit_amount > 0
            ? `+ ₹${row.debit_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
            : "—"}
        </span>
      ),
    },
    {
      key: "credit_amount",
      header: "Credit (- Settled)",
      align: "right",
      sortable: true,
      render: (row) => (
        <span
          className={`text-xs font-mono font-semibold ${row.credit_amount > 0 ? "text-emerald-400" : "text-[var(--text-muted)]"}`}
        >
          {row.credit_amount > 0
            ? `- ₹${row.credit_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
            : "—"}
        </span>
      ),
    },
    {
      key: "running_balance",
      header: "Balance Owed",
      align: "right",
      sortable: true,
      render: (row) => (
        <span className="text-xs font-mono font-bold text-[var(--text)] bg-white/[0.04] px-2.5 py-1 rounded-md border border-white/[0.06]">
          ₹{row.running_balance.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </span>
      ),
    },
  ];

  const creditLimit = ledger?.credit_limit || 0;
  const currentBalance = ledger?.current_credit_balance || 0;
  const availableCredit = ledger?.available_credit || 0;
  const creditUtilizationPct =
    creditLimit > 0 ? Math.min(100, Math.round((currentBalance / creditLimit) * 100)) : 0;
  const settlementRate =
    ledger && ledger.total_invoiced > 0
      ? Math.round((ledger.total_paid / ledger.total_invoiced) * 100)
      : 100;

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Top Breadcrumb & Actions Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/admin/retailers">
              <GlassButton
                variant="ghost"
                size="sm"
                className="h-9 w-9 p-0 text-[var(--text-muted)] hover:text-[var(--text)]"
              >
                <ArrowLeft className="w-4 h-4" />
              </GlassButton>
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-[var(--text)] flex items-center gap-2">
                  <ReceiptText className="w-5 h-5 text-cyan-400" />
                  {ledger?.retailer_name || "Retailer"} Statement
                </h1>
                {ledger?.gstin && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    GSTIN: {ledger.gstin}
                  </span>
                )}
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                Accounts-Receivable (AR) Ledger & Chronological Statement
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            <GlassButton
              variant="outline"
              size="sm"
              onClick={exportCSV}
              disabled={!ledger || !ledger.entries.length}
              className="text-xs gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </GlassButton>
            <GlassButton
              variant="outline"
              size="sm"
              onClick={() => window.print()}
              className="text-xs gap-1.5"
            >
              <Printer className="w-3.5 h-3.5" />
              Print Statement
            </GlassButton>
            <GlassButton
              variant="primary"
              size="sm"
              onClick={handleOpenRecordPayment}
              className="text-xs gap-1.5 shadow-lg shadow-purple-500/20"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              Record Payment
            </GlassButton>
          </div>
        </div>

        {/* Notifications */}
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}
        {success && (
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            {success}
          </div>
        )}

        {/* Financial KPI Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard className="p-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[var(--text-muted)]">
                Current Balance Owed
              </span>
              <div className="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center">
                <IndianRupee className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold font-mono text-[var(--text)] mt-2">
              ₹{currentBalance.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div className="flex items-center gap-1.5 mt-2 text-[11px] text-rose-400 font-medium">
              <AlertCircle className="w-3 h-3" />
              Net Accounts Receivable
            </div>
          </GlassCard>

          <GlassCard className="p-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[var(--text-muted)]">
                Credit Line & Limit
              </span>
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center justify-center">
                <CreditCard className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold font-mono text-[var(--text)] mt-2">
              ₹{creditLimit.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div className="mt-2 flex items-center justify-between text-[11px] text-[var(--text-muted)]">
              <span>{creditUtilizationPct}% Utilized</span>
              <span className="text-emerald-400 font-medium">
                ₹{availableCredit.toLocaleString("en-IN")} Available
              </span>
            </div>
            <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden mt-1.5">
              <div
                className={`h-full transition-all rounded-full ${
                  creditUtilizationPct >= 90
                    ? "bg-rose-500"
                    : creditUtilizationPct >= 70
                      ? "bg-amber-500"
                      : "bg-emerald-500"
                }`}
                style={{ width: `${creditUtilizationPct}%` }}
              />
            </div>
          </GlassCard>

          <GlassCard className="p-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[var(--text-muted)]">
                Total Invoiced (Debit)
              </span>
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold font-mono text-[var(--text)] mt-2">
              ₹{(ledger?.total_invoiced || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div className="flex items-center gap-1.5 mt-2 text-[11px] text-[var(--text-muted)]">
              <span>Cumulative gross billings</span>
            </div>
          </GlassCard>

          <GlassCard className="p-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[var(--text-muted)]">
                Total Settled (Credit)
              </span>
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-2">
              ₹{(ledger?.total_paid || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div className="flex items-center gap-1.5 mt-2 text-[11px] text-emerald-400/90 font-medium">
              <span>{settlementRate}% Settlement Rate</span>
            </div>
          </GlassCard>
        </div>

        {/* Ledger Statement Table Card */}
        <GlassCard className="p-5 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-white/[0.08] pb-4">
            <div>
              <h2 className="text-base font-semibold text-[var(--text)] flex items-center gap-2">
                <ReceiptText className="w-4 h-4 text-purple-400" />
                Ledger Transactions Statement
              </h2>
              <p className="text-xs text-[var(--text-muted)]">
                Chronological list of all issued tax invoices and settled payments
              </p>
            </div>

            <div className="flex items-center gap-2.5 flex-wrap w-full sm:w-auto">
              {/* Type Filter Buttons */}
              <div className="flex bg-white/[0.04] p-1 rounded-lg border border-white/[0.08]">
                <button
                  type="button"
                  onClick={() => setTypeFilter("all")}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    typeFilter === "all"
                      ? "bg-purple-600 text-white shadow"
                      : "text-[var(--text-muted)] hover:text-white"
                  }`}
                >
                  All ({ledger?.entries.length || 0})
                </button>
                <button
                  type="button"
                  onClick={() => setTypeFilter("invoice")}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    typeFilter === "invoice"
                      ? "bg-rose-600 text-white shadow"
                      : "text-[var(--text-muted)] hover:text-white"
                  }`}
                >
                  Invoices ({ledger?.entries.filter((e) => e.entry_type === "invoice").length || 0})
                </button>
                <button
                  type="button"
                  onClick={() => setTypeFilter("payment")}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    typeFilter === "payment"
                      ? "bg-emerald-600 text-white shadow"
                      : "text-[var(--text-muted)] hover:text-white"
                  }`}
                >
                  Payments ({ledger?.entries.filter((e) => e.entry_type === "payment").length || 0})
                </button>
              </div>

              {/* Search input */}
              <div className="w-full sm:w-48">
                <GlassInput
                  placeholder="Search ref #..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-8 text-xs"
                />
              </div>
            </div>
          </div>

          <DataTable
            data={filteredEntries}
            columns={columns}
            keyExtractor={(row) => row.id}
            isLoading={loading}
            emptyTitle="No transactions found."
            emptyDescription="No tax invoices or payment records found for this retailer."
          />
        </GlassCard>

        {/* Record Payment Modal */}
        <GlassModal
          isOpen={paymentModalOpen}
          onClose={() => setPaymentModalOpen(false)}
          title={`Record Payment for ${ledger?.retailer_name || "Retailer"}`}
          maxWidth="md"
        >
          <form onSubmit={handleRecordPaymentSubmit} className="space-y-4">
            {payFormError && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {payFormError}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-[var(--text)] mb-1.5">
                Apply to Invoice <span className="text-rose-400">*</span>
              </label>
              <select
                value={selectedInvoiceId}
                onChange={(e) => handleInvoiceChange(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl bg-black/40 border border-white/10 text-white focus:outline-none focus:ring-1 focus:ring-purple-500"
                required
              >
                <option value="" disabled>
                  Select an invoice...
                </option>
                {invoices.map((inv) => (
                  <option key={inv.id} value={inv.id}>
                    {inv.invoice_no} — ₹{inv.total_amount.toLocaleString("en-IN")} (Outstanding: ₹
                    {(inv.outstanding_balance || inv.total_amount).toLocaleString("en-IN")}) [
                    {inv.status.toUpperCase()}]
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-[var(--text)] mb-1.5">
                  Payment Amount (₹) <span className="text-rose-400">*</span>
                </label>
                <GlassInput
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={payAmount}
                  onChange={(e) => setPayAmount(parseFloat(e.target.value) || 0)}
                  placeholder="e.g. 5000"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[var(--text)] mb-1.5">
                  Payment Method <span className="text-rose-400">*</span>
                </label>
                <select
                  value={payMethod}
                  onChange={(e) => setPayMethod(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-black/40 border border-white/10 text-white focus:outline-none focus:ring-1 focus:ring-purple-500"
                >
                  <option value="upi">UPI / QR</option>
                  <option value="bank_transfer">Bank Transfer (NEFT/RTGS/IMPS)</option>
                  <option value="cheque">Cheque</option>
                  <option value="cash">Cash</option>
                  <option value="card">Debit / Credit Card</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text)] mb-1.5">
                Payment Date
              </label>
              <GlassInput
                type="date"
                value={payDate}
                onChange={(e) => setPayDate(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text)] mb-1.5">
                Transaction Note / Reference
              </label>
              <GlassInput
                type="text"
                placeholder="e.g. UTR #1234567890 or Cheque #98765"
                value={payNote}
                onChange={(e) => setPayNote(e.target.value)}
              />
            </div>

            <div className="pt-3 border-t border-white/[0.08] flex items-center justify-end gap-2.5">
              <GlassButton
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setPaymentModalOpen(false)}
                disabled={submittingPayment}
              >
                Cancel
              </GlassButton>
              <GlassButton
                type="submit"
                variant="primary"
                size="sm"
                disabled={submittingPayment}
                className="shadow-lg shadow-purple-500/20"
              >
                {submittingPayment ? "Recording..." : "Record & Post Payment"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>
      </div>
    </AppLayout>
  );
}
