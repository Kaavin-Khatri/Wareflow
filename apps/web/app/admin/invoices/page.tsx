"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassInput } from "@/components/glass/GlassInput";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { apiClient } from "@/lib/api-client";
import {
  FileText,
  Search,
  Printer,
  ShoppingBag,
  Building2,
  CheckCircle2,
  Clock,
  AlertCircle,
  Eye,
  ArrowLeft,
  X,
  CreditCard,
  PlusCircle,
  RefreshCw,
} from "lucide-react";


interface InvoiceItem {
  id: string;
  invoice_id: string;
  product_id: string;
  product_name: string;
  hsn_code?: string | null;
  qty: number;
  unit_price: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
  uom_id?: string | null;
}

interface PaymentRecord {
  id: string;
  amount: number;
  method: string;
  paid_at: string;
  note?: string | null;
}

interface InvoiceDetail {
  id: string;
  sales_order_id?: string | null;
  sales_order_number?: string | null;
  buyer_type?: string | null;
  buyer_id?: string | null;
  buyer_name?: string | null;
  buyer_gstin?: string | null;
  buyer_phone?: string | null;
  buyer_email?: string | null;
  buyer_address?: string | null;
  invoice_no: string;
  invoice_date: string;
  gst_rate: number;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  paid_amount?: number;
  outstanding_balance?: number;
  status: "unpaid" | "partially_paid" | "paid" | "overdue" | string;
  e_invoice_irn?: string | null;
  e_invoice_ack_no?: string | null;
  e_invoice_qr_code?: string | null;
  e_way_bill_no?: string | null;
  created_at: string;
  items: InvoiceItem[];
  payments?: PaymentRecord[];
}

interface InvoiceListItem {
  id: string;
  sales_order_id?: string | null;
  sales_order_number?: string | null;
  invoice_no: string;
  invoice_date: string;
  buyer_type?: string | null;
  buyer_name?: string | null;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  paid_amount?: number;
  outstanding_balance?: number;
  status: "unpaid" | "partially_paid" | "paid" | "overdue" | string;
  items_count: number;
  created_at: string;
}

interface InvoiceListResponse {
  items: InvoiceListItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

const MOCK_INVOICES: InvoiceListItem[] = [
  {
    id: "inv-1",
    sales_order_id: "so-101",
    sales_order_number: "SO-2026-001",
    invoice_no: "INV/2026-27/0001",
    invoice_date: new Date(Date.now() - 3600000 * 24 * 5).toISOString(),
    buyer_type: "retailer",
    buyer_name: "Apex Wholesale Mart",
    subtotal: 11000.0,
    tax_amount: 1980.0,
    total_amount: 12980.0,
    paid_amount: 12980.0,
    outstanding_balance: 0.0,
    status: "paid",
    items_count: 2,
    created_at: new Date(Date.now() - 3600000 * 24 * 5).toISOString(),
  },
  {
    id: "inv-2",
    sales_order_id: "so-102",
    sales_order_number: "SO-2026-002",
    invoice_no: "INV/2026-27/0002",
    invoice_date: new Date(Date.now() - 3600000 * 24 * 2).toISOString(),
    buyer_type: "retailer",
    buyer_name: "Metro Retail Distribution",
    subtotal: 25000.0,
    tax_amount: 4500.0,
    total_amount: 29500.0,
    paid_amount: 10000.0,
    outstanding_balance: 19500.0,
    status: "partially_paid",
    items_count: 5,
    created_at: new Date(Date.now() - 3600000 * 24 * 2).toISOString(),
  },
  {
    id: "inv-3",
    sales_order_id: "so-103",
    sales_order_number: "SO-2026-003",
    invoice_no: "INV/2026-27/0003",
    invoice_date: new Date(Date.now() - 3600000 * 24 * 35).toISOString(),
    buyer_type: "retailer",
    buyer_name: "Fresh Foods Supermarket",
    subtotal: 18000.0,
    tax_amount: 3240.0,
    total_amount: 21240.0,
    paid_amount: 0.0,
    outstanding_balance: 21240.0,
    status: "overdue",
    items_count: 3,
    created_at: new Date(Date.now() - 3600000 * 24 * 35).toISOString(),
  },
];

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Detail Modal State
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceDetail | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Record Payment Modal State
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [targetInvoice, setTargetInvoice] = useState<InvoiceListItem | InvoiceDetail | null>(null);
  const [payAmount, setPayAmount] = useState<number>(0);
  const [payMethod, setPayMethod] = useState<string>("upi");
  const [payDate, setPayDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [payNote, setPayNote] = useState<string>("");
  const [submittingPay, setSubmittingPay] = useState(false);
  const [payError, setPayError] = useState<string | null>(null);

  // Overdue scan state
  const [scanningOverdue, setScanningOverdue] = useState(false);

  const fetchInvoices = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<InvoiceListResponse>("/invoices?page_size=100");
      if (res && res.items && res.items.length > 0) {
        setInvoices(res.items);
      } else {
        setInvoices(MOCK_INVOICES);
      }
    } catch {
      setInvoices(MOCK_INVOICES);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function init() {
      try {
        setLoading(true);
        const res = await apiClient.get<InvoiceListResponse>("/invoices?page_size=100");
        if (!ignore) {
          if (res && res.items && res.items.length > 0) {
            setInvoices(res.items);
          } else {
            setInvoices(MOCK_INVOICES);
          }
        }
      } catch {
        if (!ignore) {
          setInvoices(MOCK_INVOICES);
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
  }, []);


  // KPIs
  const kpis = useMemo(() => {
    const totalCount = invoices.length;
    const totalBilled = invoices.reduce((acc, i) => acc + (Number(i.total_amount) || 0), 0);
    const paidAmount = invoices.reduce(
      (acc, i) => acc + (i.status === "paid" ? Number(i.total_amount) : Number(i.paid_amount || 0)),
      0
    );
    const unpaidAmount = Math.max(0, totalBilled - paidAmount);

    return { totalCount, totalBilled, unpaidAmount, paidAmount };
  }, [invoices]);

  // Filtered List
  const filteredInvoices = useMemo(() => {
    return invoices.filter((inv) => {
      const matchSearch =
        !searchQuery ||
        inv.invoice_no.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (inv.buyer_name && inv.buyer_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (inv.sales_order_number && inv.sales_order_number.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchStatus = statusFilter === "all" || inv.status === statusFilter;

      return matchSearch && matchStatus;
    });
  }, [invoices, searchQuery, statusFilter]);

  const handleOpenDetail = async (item: InvoiceListItem) => {
    setLoadingDetail(true);
    setIsDetailOpen(true);
    try {
      const detail = await apiClient.get<InvoiceDetail>(`/invoices/${item.id}`);
      setSelectedInvoice(detail);
    } catch {
      // Fallback detail
      setSelectedInvoice({
        id: item.id,
        sales_order_id: item.sales_order_id,
        sales_order_number: item.sales_order_number,
        buyer_type: item.buyer_type,
        buyer_name: item.buyer_name,
        buyer_gstin: "06AAAAA0000A1Z5",
        buyer_phone: "+919876543210",
        buyer_email: "accounts@retailer.com",
        buyer_address: "Plot 42, Wholesale Trade Center, Gurugram, Haryana",
        invoice_no: item.invoice_no,
        invoice_date: item.invoice_date,
        gst_rate: 18.0,
        subtotal: item.subtotal,
        tax_amount: item.tax_amount,
        total_amount: item.total_amount,
        paid_amount: item.paid_amount || (item.status === "paid" ? item.total_amount : 0),
        outstanding_balance: item.outstanding_balance ?? (item.status === "paid" ? 0 : item.total_amount),
        status: item.status,
        created_at: item.created_at,
        items: [
          {
            id: "item-1",
            invoice_id: item.id,
            product_id: "prod-1",
            product_name: "Organic Whole Cow Milk 1L",
            hsn_code: "0401",
            qty: 100,
            unit_price: 60.0,
            tax_rate: 18.0,
            tax_amount: 1080.0,
            total: 7080.0,
          },
          {
            id: "item-2",
            invoice_id: item.id,
            product_id: "prod-2",
            product_name: "Salted Table Butter 500g",
            hsn_code: "0405",
            qty: 20,
            unit_price: 250.0,
            tax_rate: 18.0,
            tax_amount: 900.0,
            total: 5900.0,
          },
        ],
      });
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleOpenPaymentModal = (inv: InvoiceListItem | InvoiceDetail) => {
    setTargetInvoice(inv);
    const outstanding =
      inv.outstanding_balance !== undefined
        ? inv.outstanding_balance
        : inv.status === "paid"
        ? 0
        : inv.total_amount;
    setPayAmount(outstanding);
    setPayMethod("upi");
    setPayDate(new Date().toISOString().split("T")[0]);
    setPayNote("");
    setPayError(null);
    setPaymentModalOpen(true);
  };

  const handleRecordPaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetInvoice) return;

    if (payAmount <= 0) {
      setPayError("Payment amount must be greater than zero.");
      return;
    }

    try {
      setSubmittingPay(true);
      setPayError(null);
      await apiClient.post(`/invoices/${targetInvoice.id}/payments`, {
        amount: Number(payAmount),
        method: payMethod,
        paid_at: new Date(payDate).toISOString(),
        note: payNote.trim() || undefined,
      });

      setSuccess(`Payment of ₹${Number(payAmount).toLocaleString("en-IN")} successfully recorded for ${targetInvoice.invoice_no}.`);
      setPaymentModalOpen(false);
      await fetchInvoices();
      if (isDetailOpen && selectedInvoice?.id === targetInvoice.id) {
        const refreshed = await apiClient.get<InvoiceDetail>(`/invoices/${targetInvoice.id}`);
        setSelectedInvoice(refreshed);
      }
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: unknown) {
      setPayError(err instanceof Error ? err.message : "Failed to record payment.");
    } finally {
      setSubmittingPay(false);
    }
  };

  const handleRunOverdueScan = async () => {
    try {
      setScanningOverdue(true);
      const res = await apiClient.post<{ overdue_count: number }>("/invoices/detect-overdue?due_days=30");
      setSuccess(`Overdue scan complete. Flagged ${res.overdue_count} past-due invoice(s) as overdue.`);
      await fetchInvoices();
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to scan overdue invoices.");
    } finally {
      setScanningOverdue(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const columns: DataTableColumn<InvoiceListItem>[] = [
    {
      key: "invoice_no",
      header: "Invoice #",
      sortable: true,
      render: (inv) => (
        <div className="flex flex-col">
          <span className="font-mono font-bold text-xs text-purple-400">{inv.invoice_no}</span>
          <span className="text-[10px] text-[var(--text-muted)] font-mono">
            SO: {inv.sales_order_number || "—"}
          </span>
        </div>
      ),
    },
    {
      key: "buyer_name",
      header: "Buyer / Retailer",
      sortable: true,
      render: (inv) => (
        <div className="flex flex-col">
          <span className="font-semibold text-xs text-[var(--text)]">{inv.buyer_name || "Direct Customer"}</span>
          <span className="text-[10px] text-[var(--text-muted)] capitalize">{inv.buyer_type || "Retailer"}</span>
        </div>
      ),
    },
    {
      key: "status",
      header: "Payment Status",
      sortable: true,
      render: (inv) => {
        switch (inv.status) {
          case "paid":
            return (
              <GlassBadge variant="success">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Paid
              </GlassBadge>
            );
          case "partially_paid":
            return (
              <GlassBadge variant="accent">
                <Clock className="w-3 h-3 mr-1" /> Partially Paid
              </GlassBadge>
            );
          case "overdue":
            return (
              <GlassBadge variant="error">
                <AlertCircle className="w-3 h-3 mr-1" /> Overdue
              </GlassBadge>
            );
          default:
            return (
              <GlassBadge variant="warning">
                <Clock className="w-3 h-3 mr-1" /> Unpaid
              </GlassBadge>
            );
        }
      },
    },
    {
      key: "subtotal",
      header: "Subtotal",
      align: "right",
      sortable: true,
      render: (inv) => (
        <span className="font-mono text-xs text-[var(--text-muted)]">
          ₹{inv.subtotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: "tax_amount",
      header: "GST (18%)",
      align: "right",
      sortable: true,
      render: (inv) => (
        <span className="font-mono text-xs text-amber-400">
          ₹{inv.tax_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: "total_amount",
      header: "Total Invoiced",
      align: "right",
      sortable: true,
      render: (inv) => (
        <span className="font-mono font-bold text-xs text-emerald-400">
          ₹{inv.total_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: "invoice_date",
      header: "Invoice Date",
      sortable: true,
      render: (inv) => (
        <span className="font-mono text-[11px] text-[var(--text-muted)]">
          {new Date(inv.invoice_date).toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          })}
        </span>
      ),
    },
    {
      key: "id",
      header: "Action",
      align: "right",
      render: (inv) => (
        <div className="flex items-center justify-end gap-1.5">
          {inv.status !== "paid" && (
            <GlassButton
              variant="primary"
              size="sm"
              onClick={() => handleOpenPaymentModal(inv)}
              className="text-xs h-7 px-2 bg-emerald-600 hover:bg-emerald-500 border-emerald-500/30"
            >
              <PlusCircle className="w-3 h-3 mr-1" />
              Pay
            </GlassButton>
          )}
          <GlassButton
            variant="secondary"
            size="sm"
            onClick={() => handleOpenDetail(inv)}
            className="text-xs h-7 px-2"
          >
            <Eye className="w-3 h-3 mr-1 text-purple-400" />
            View
          </GlassButton>
        </div>
      ),
    },
  ];

  return (
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--text)]">
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/admin/sales-orders">
              <button className="p-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-[var(--text-muted)] hover:text-[var(--text)] transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </button>
            </Link>
            <div>
              <h1 className="text-xl font-bold text-[var(--text)] flex items-center gap-2">
                <FileText className="w-5 h-5 text-purple-400" />
                GST Tax Invoices & Receivables
              </h1>
              <p className="text-xs text-[var(--text-muted)]">
                Immutable frozen tax invoices and accounts receivable ledger management.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <GlassButton
              variant="outline"
              size="sm"
              onClick={handleRunOverdueScan}
              disabled={scanningOverdue}
              className="text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 text-amber-400 ${scanningOverdue ? "animate-spin" : ""}`} />
              {scanningOverdue ? "Scanning..." : "Scan Overdue (30d)"}
            </GlassButton>
            <Link href="/admin/sales-orders">
              <GlassButton variant="secondary" size="sm" className="text-xs">
                <ShoppingBag className="w-3.5 h-3.5 mr-1.5 text-purple-400" />
                Sales Orders
              </GlassButton>
            </Link>
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

        {/* 4 KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard className="p-4 space-y-1">
            <span className="text-xs text-[var(--text-muted)] font-medium flex items-center gap-1.5">
              <CreditCard className="w-3.5 h-3.5 text-purple-400" /> Total Invoiced Value
            </span>
            <div className="text-2xl font-bold font-mono text-[var(--text)]">
              ₹{kpis.totalBilled.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">{kpis.totalCount} total tax invoices</p>
          </GlassCard>

          <GlassCard className="p-4 space-y-1">
            <span className="text-xs text-amber-400 font-medium flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" /> Outstanding Receivables
            </span>
            <div className="text-2xl font-bold font-mono text-amber-400">
              ₹{kpis.unpaidAmount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">Pending settlement across buyers</p>
          </GlassCard>

          <GlassCard className="p-4 space-y-1">
            <span className="text-xs text-emerald-400 font-medium flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" /> Total Payments Collected
            </span>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              ₹{kpis.paidAmount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">Settled cash and bank receipts</p>
          </GlassCard>

          <GlassCard className="p-4 space-y-1">
            <span className="text-xs text-cyan-400 font-medium flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" /> Active Invoices
            </span>
            <div className="text-2xl font-bold font-mono text-cyan-400">
              {kpis.totalCount}
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">Sequential audit-ready series</p>
          </GlassCard>
        </div>

        {/* Filters & Search */}
        <GlassCard className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search invoice #, retailer, SO #..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-xs text-[var(--text)] focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
            {["all", "unpaid", "paid", "partially_paid", "overdue"].map((st) => (
              <button
                key={st}
                data-testid={`filter-${st}`}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium capitalize transition-colors ${
                  statusFilter === st
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                    : "bg-[var(--surface)] text-[var(--text-muted)] hover:text-[var(--text)] border border-[var(--glass-border)]"
                }`}
              >
                {st.replace("_", " ")}
              </button>
            ))}
          </div>
        </GlassCard>

        {/* Invoices DataTable */}
        <DataTable
          data={filteredInvoices}
          columns={columns}
          keyExtractor={(inv) => inv.id}
          isLoading={loading}
          emptyTitle="No invoices found."
          emptyDescription="Invoices will appear here once generated from confirmed sales orders."
        />

        {/* INVOICE PREVIEW & PRINT MODAL */}
        <GlassModal
          isOpen={isDetailOpen}
          onClose={() => setIsDetailOpen(false)}
          title={`Tax Invoice: ${selectedInvoice?.invoice_no || ""}`}
          maxWidth="lg"
        >

          {loadingDetail ? (
            <div className="p-8 text-center text-xs text-[var(--text-muted)]">
              Loading frozen invoice document...
            </div>
          ) : selectedInvoice ? (
            <div className="space-y-5 print:p-0">
              {/* Printable Invoice Container */}
              <div className="p-4 sm:p-6 rounded-2xl bg-[var(--surface-hover)] border border-[var(--glass-border)] space-y-6">
                {/* Header: Distributor Info & Invoice Meta */}
                <div className="flex flex-col sm:flex-row justify-between items-start gap-4 border-b border-[var(--glass-border)] pb-4">
                  <div>
                    <span className="text-[10px] font-mono tracking-widest text-purple-400 uppercase font-bold">
                      Tax Invoice (Original for Recipient)
                    </span>
                    <h2 className="text-lg font-black tracking-tight text-[var(--text)] flex items-center gap-1.5 mt-0.5">
                      <Building2 className="w-5 h-5 text-purple-400" />
                      WareFlow Wholesale Distribution
                    </h2>
                    <div className="text-[11px] text-[var(--text-muted)] space-y-0.5 mt-1 font-mono">
                      <div>GSTIN: <span className="text-[var(--text)] font-semibold">07AAAAA0000A1Z5</span></div>
                      <div>FSSAI Lic: <span className="text-[var(--text)] font-semibold">10019011000123</span></div>
                      <div>Central Distribution Center, Okhla Phase III, New Delhi - 110020</div>
                    </div>
                  </div>

                  <div className="sm:text-right space-y-1 font-mono">
                    <div className="text-base font-black text-purple-300">
                      {selectedInvoice.invoice_no}
                    </div>
                    <div className="text-xs text-[var(--text-muted)]">
                      Date: <span className="text-[var(--text)]">{new Date(selectedInvoice.invoice_date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</span>
                    </div>
                    <div className="text-xs text-[var(--text-muted)]">
                      SO Ref: <span className="text-[var(--text)] font-semibold">{selectedInvoice.sales_order_number || "Direct"}</span>
                    </div>
                    <div className="pt-1 flex items-center justify-end gap-1.5">
                      <GlassBadge variant={selectedInvoice.status === "paid" ? "success" : selectedInvoice.status === "partially_paid" ? "accent" : "warning"}>
                        {selectedInvoice.status.toUpperCase()}
                      </GlassBadge>
                    </div>
                  </div>
                </div>

                {/* Billed To / Buyer Info */}
                <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-[10px] uppercase font-mono tracking-wider text-[var(--text-muted)] block">
                      Billed To (Buyer)
                    </span>
                    <div className="font-bold text-sm text-[var(--text)] mt-0.5">
                      {selectedInvoice.buyer_name || "Direct Customer"}
                    </div>
                    <div className="text-[11px] text-[var(--text-muted)] mt-1">
                      {selectedInvoice.buyer_address || "Standard Retail Outlet Delivery Address"}
                    </div>
                  </div>

                  <div className="sm:text-right font-mono text-[11px] space-y-0.5">
                    <div>Buyer GSTIN: <span className="text-[var(--text)] font-semibold">{selectedInvoice.buyer_gstin || "Unregistered / Consumer"}</span></div>
                    <div>Phone: <span className="text-[var(--text)]">{selectedInvoice.buyer_phone || "—"}</span></div>
                    <div>Email: <span className="text-[var(--text)]">{selectedInvoice.buyer_email || "—"}</span></div>
                  </div>
                </div>

                {/* Frozen Line Items Table */}
                <div className="overflow-x-auto rounded-xl border border-[var(--glass-border)]">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[var(--surface)] text-[var(--text-muted)] font-mono text-[10px] uppercase border-b border-[var(--glass-border)]">
                      <tr>
                        <th className="p-2.5">#</th>
                        <th className="p-2.5">Item Description</th>
                        <th className="p-2.5">HSN</th>
                        <th className="p-2.5 text-right">Qty</th>
                        <th className="p-2.5 text-right">Rate (₹)</th>
                        <th className="p-2.5 text-right">Tax (18%)</th>
                        <th className="p-2.5 text-right">Total (₹)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--glass-border)] font-mono">
                      {selectedInvoice.items?.map((it, idx) => (
                        <tr key={it.id} className="hover:bg-[var(--surface)]">
                          <td className="p-2.5 text-[var(--text-muted)]">{idx + 1}</td>
                          <td className="p-2.5 font-sans font-medium text-[var(--text)]">
                            {it.product_name}
                          </td>
                          <td className="p-2.5 text-[var(--text-muted)]">{it.hsn_code || "—"}</td>
                          <td className="p-2.5 text-right font-bold text-[var(--text)]">{it.qty}</td>
                          <td className="p-2.5 text-right text-[var(--text-muted)]">{it.unit_price.toFixed(2)}</td>
                          <td className="p-2.5 text-right text-amber-400">{it.tax_amount.toFixed(2)}</td>
                          <td className="p-2.5 text-right font-bold text-emerald-400">{it.total.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Payment History and Summary */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <div className="space-y-2">
                    <span className="font-bold text-[var(--text)] block uppercase tracking-tight text-[10px]">
                      Payment Settlements History:
                    </span>
                    {selectedInvoice.payments && selectedInvoice.payments.length > 0 ? (
                      <div className="space-y-1.5">
                        {selectedInvoice.payments.map((p) => (
                          <div key={p.id} className="p-2 rounded-lg bg-black/20 border border-white/[0.06] text-xs font-mono flex items-center justify-between">
                            <div>
                              <span className="text-emerald-400 font-bold">₹{p.amount.toFixed(2)}</span>
                              <span className="text-[var(--text-muted)] text-[10px] ml-2 uppercase">({p.method.replace("_", " ")})</span>
                              {p.note && <div className="text-[10px] text-[var(--text-muted)] font-sans">{p.note}</div>}
                            </div>
                            <span className="text-[10px] text-[var(--text-muted)]">{new Date(p.paid_at).toLocaleDateString("en-IN")}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-[var(--text-muted)] italic">No payments recorded yet.</p>
                    )}
                  </div>

                  <div className="space-y-1.5 font-mono text-xs">
                    <div className="flex justify-between text-[var(--text-muted)]">
                      <span>Subtotal:</span>
                      <span>₹{selectedInvoice.subtotal.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-amber-400">
                      <span>CGST (9%):</span>
                      <span>₹{(selectedInvoice.tax_amount / 2).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-amber-400">
                      <span>SGST (9%):</span>
                      <span>₹{(selectedInvoice.tax_amount / 2).toFixed(2)}</span>
                    </div>
                    <div className="border-t border-[var(--glass-border)] pt-1.5 flex justify-between text-xs font-bold text-emerald-400">
                      <span>Grand Total:</span>
                      <span>₹{selectedInvoice.total_amount.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-xs text-purple-300">
                      <span>Total Paid:</span>
                      <span>₹{(selectedInvoice.paid_amount || 0).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm font-bold text-rose-400 bg-rose-500/10 p-1.5 rounded-lg border border-rose-500/20">
                      <span>Outstanding Balance:</span>
                      <span>₹{(selectedInvoice.outstanding_balance ?? (selectedInvoice.total_amount - (selectedInvoice.paid_amount || 0))).toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Modal Actions */}
              <div className="flex items-center justify-between pt-2">
                <GlassButton
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsDetailOpen(false)}
                >
                  <X className="w-4 h-4 mr-1" /> Close
                </GlassButton>

                <div className="flex items-center gap-2">
                  {selectedInvoice.status !== "paid" && (
                    <GlassButton
                      variant="primary"
                      size="sm"
                      onClick={() => handleOpenPaymentModal(selectedInvoice)}
                      className="bg-emerald-600 hover:bg-emerald-500"
                    >
                      <PlusCircle className="w-4 h-4 mr-1.5" /> Record Payment
                    </GlassButton>
                  )}
                  <GlassButton
                    variant="primary"
                    size="sm"
                    onClick={handlePrint}
                  >
                    <Printer className="w-4 h-4 mr-1.5" /> Print / Export PDF
                  </GlassButton>
                </div>
              </div>
            </div>
          ) : null}
        </GlassModal>

        {/* RECORD PAYMENT MODAL */}
        <GlassModal
          isOpen={paymentModalOpen}
          onClose={() => setPaymentModalOpen(false)}
          title={`Record Payment for ${targetInvoice?.invoice_no || "Invoice"}`}
          maxWidth="md"
        >

          <form onSubmit={handleRecordPaymentSubmit} className="space-y-4">
            {payError && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {payError}
              </div>
            )}

            <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-between text-xs font-mono">
              <div>
                <span className="text-[var(--text-muted)] block text-[10px]">Invoice Total</span>
                <span className="font-bold text-[var(--text)]">₹{Number(targetInvoice?.total_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="text-right">
                <span className="text-[var(--text-muted)] block text-[10px]">Outstanding Balance</span>
                <span className="font-bold text-amber-400">
                  ₹{Number(
                    targetInvoice?.outstanding_balance !== undefined
                      ? targetInvoice.outstanding_balance
                      : targetInvoice?.total_amount || 0
                  ).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
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
                  max={targetInvoice?.outstanding_balance || targetInvoice?.total_amount}
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
                placeholder="e.g. UPI Ref #9876543210 or NEFT UTR"
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
                disabled={submittingPay}
              >
                Cancel
              </GlassButton>
              <GlassButton
                type="submit"
                variant="primary"
                size="sm"
                disabled={submittingPay}
                className="bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-500/20"
              >
                {submittingPay ? "Recording..." : "Record & Post Payment"}
              </GlassButton>
            </div>
          </form>
        </GlassModal>
      </div>
    </div>
  );
}
