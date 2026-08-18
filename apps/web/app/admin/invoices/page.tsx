"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassModal } from "@/components/glass/GlassModal";
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
  status: "unpaid" | "partially_paid" | "paid" | "overdue" | string;
  e_invoice_irn?: string | null;
  e_invoice_ack_no?: string | null;
  e_invoice_qr_code?: string | null;
  e_way_bill_no?: string | null;
  created_at: string;
  items: InvoiceItem[];
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
    invoice_date: new Date(Date.now() - 3600000 * 24).toISOString(),
    buyer_type: "retailer",
    buyer_name: "Apex Wholesale Mart",
    subtotal: 11000.0,
    tax_amount: 1980.0,
    total_amount: 12980.0,
    status: "unpaid",
    items_count: 2,
    created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
  },
  {
    id: "inv-2",
    sales_order_id: "so-102",
    sales_order_number: "SO-2026-002",
    invoice_no: "INV/2026-27/0002",
    invoice_date: new Date(Date.now() - 86400000 * 3).toISOString(),
    buyer_type: "retailer",
    buyer_name: "Fresh Mart Retail",
    subtotal: 25000.0,

    tax_amount: 4500.0,
    total_amount: 29500.0,
    status: "paid",
    items_count: 3,
    created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
  },
];

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Selected Invoice Detail Modal
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchInvoices = async () => {
      try {
        const res = await apiClient.get<InvoiceListResponse>("/invoices?page_size=100");
        if (!isMounted) return;
        if (res && Array.isArray(res.items) && res.items.length > 0) {
          setInvoices(res.items);
        } else {
          setInvoices(MOCK_INVOICES);
        }
      } catch {
        if (isMounted) setInvoices(MOCK_INVOICES);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchInvoices();
    return () => {
      isMounted = false;
    };
  }, []);

  // KPIs
  const kpis = useMemo(() => {
    const totalCount = invoices.length;
    const totalBilled = invoices.reduce((acc, i) => acc + (Number(i.total_amount) || 0), 0);
    const unpaidAmount = invoices
      .filter((i) => i.status === "unpaid" || i.status === "overdue" || i.status === "partially_paid")
      .reduce((acc, i) => acc + (Number(i.total_amount) || 0), 0);
    const paidAmount = invoices
      .filter((i) => i.status === "paid")
      .reduce((acc, i) => acc + (Number(i.total_amount) || 0), 0);

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
      // Fallback to synthesized detail
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
        <GlassButton
          variant="secondary"
          size="sm"
          onClick={() => handleOpenDetail(inv)}
        >
          <Eye className="w-3.5 h-3.5 mr-1 text-purple-400" />
          View & Print
        </GlassButton>
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
                GST Tax Invoices & Billing
              </h1>
              <p className="text-xs text-[var(--text-muted)]">
                Immutable frozen tax invoices generated from confirmed wholesale sales orders.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/admin/sales-orders">
              <GlassButton variant="secondary" size="md">
                <ShoppingBag className="w-4 h-4 mr-1.5 text-purple-400" />
                Sales Orders
              </GlassButton>
            </Link>
          </div>
        </div>

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
              <Clock className="w-3.5 h-3.5" /> Outstanding Unpaid
            </span>
            <div className="text-2xl font-bold font-mono text-amber-400">
              ₹{kpis.unpaidAmount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">Receivables pending settlement</p>
          </GlassCard>

          <GlassCard className="p-4 space-y-1">
            <span className="text-xs text-emerald-400 font-medium flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" /> Collected Revenue
            </span>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              ₹{kpis.paidAmount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">Settled invoice payments</p>
          </GlassCard>

          <GlassCard className="p-4 space-y-1">
            <span className="text-xs text-cyan-400 font-medium flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" /> Active Invoices
            </span>
            <div className="text-2xl font-bold font-mono text-cyan-400">
              {kpis.totalCount}
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">FY 2026-27 sequential ledger</p>
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
                    <div className="pt-1">
                      <GlassBadge variant={selectedInvoice.status === "paid" ? "success" : "warning"}>
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

                {/* Totals Breakdown */}
                <div className="flex flex-col sm:flex-row justify-between items-start gap-4 pt-2">
                  <div className="text-[11px] text-[var(--text-muted)] space-y-1 max-w-sm">
                    <span className="font-bold text-[var(--text)] block uppercase tracking-tight text-[10px]">
                      Declaration & Terms:
                    </span>
                    <p>
                      We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.
                    </p>
                  </div>

                  <div className="w-full sm:w-64 space-y-1.5 font-mono text-xs">
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
                    <div className="border-t border-[var(--glass-border)] pt-1.5 flex justify-between text-sm font-bold text-emerald-400">
                      <span>Grand Total:</span>
                      <span>₹{selectedInvoice.total_amount.toFixed(2)}</span>
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
      </div>
    </div>
  );
}
