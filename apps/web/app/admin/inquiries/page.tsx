"use client";

import React, { useState, useEffect, useMemo } from "react";
import AppLayout from "@/components/AppLayout";
import { ListViewTemplate } from "@/components/templates/ListViewTemplate";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { apiClient } from "@/lib/api-client";
import {
  HelpCircle,
  Clock,
  CheckCircle2,
  MessageSquare,
  Package,
  Store,
  Send,
  Search,
  Filter,
} from "lucide-react";

export interface ProductInquiry {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  retailer_id: string | null;
  retailer_name: string | null;
  customer_id: string | null;
  message: string;
  status: "open" | "responded" | "closed" | string;
  response: string | null;
  created_at: string;
  responded_at: string | null;
}

export default function AdminInquiriesPage() {
  const [inquiries, setInquiries] = useState<ProductInquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Response Modal State
  const [selectedInquiry, setSelectedInquiry] = useState<ProductInquiry | null>(null);
  const [responseText, setResponseText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const fetchInquiries = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<ProductInquiry[]>("/inquiries");
      setInquiries(data || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function init() {
      if (!ignore) {
        await fetchInquiries();
      }
    }
    init();
    return () => {
      ignore = true;
    };
  }, []);

  // Filtered inquiries
  const filteredInquiries = useMemo(() => {
    return inquiries.filter((inq) => {
      const matchesStatus =
        statusFilter === "all" || inq.status.toLowerCase() === statusFilter.toLowerCase();

      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !searchQuery ||
        inq.product_name.toLowerCase().includes(q) ||
        inq.product_sku.toLowerCase().includes(q) ||
        (inq.retailer_name && inq.retailer_name.toLowerCase().includes(q)) ||
        inq.message.toLowerCase().includes(q);

      return matchesStatus && matchesSearch;
    });
  }, [inquiries, statusFilter, searchQuery]);

  // Metrics
  const openCount = inquiries.filter((i) => i.status.toLowerCase() === "open").length;
  const respondedCount = inquiries.filter((i) => i.status.toLowerCase() === "responded").length;

  const handleOpenRespondModal = (inquiry: ProductInquiry) => {
    setSelectedInquiry(inquiry);
    setResponseText(inquiry.response || "");
    setModalError(null);
  };

  const handleSendResponse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInquiry || !responseText.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setModalError(null);

    try {
      const updatedInquiry = await apiClient.patch<ProductInquiry>(
        `/inquiries/${selectedInquiry.id}/respond`,
        { response: responseText.trim() }
      );

      setInquiries((prev) =>
        prev.map((item) => (item.id === updatedInquiry.id ? updatedInquiry : item))
      );
      setSelectedInquiry(null);
      setResponseText("");
    } catch (err: unknown) {
      setModalError(err instanceof Error ? err.message : "Failed to send response");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppLayout>
      <ListViewTemplate
        title="Product Inquiries & Quotes"
        description="Staff inbox for retailer queries and bulk quotation requests"
        secondaryActions={
          <GlassButton
            variant="secondary"
            onClick={fetchInquiries}
            className="flex items-center gap-1.5"
          >
            <Clock className="w-4 h-4" />
            Refresh
          </GlassButton>
        }
      >
        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <MessageSquare className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Total Inquiries</p>
              <h3 className="text-xl font-bold text-white">{inquiries.length}</h3>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Pending Action</p>
              <h3 className="text-xl font-bold text-amber-300">{openCount} Open</h3>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Responded</p>
              <h3 className="text-xl font-bold text-emerald-300">{respondedCount} Answered</h3>
            </div>
          </GlassCard>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search product, SKU, retailer, or message..."
              className="w-full pl-10 pr-4 py-2.5 rounded-2xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400 hidden sm:inline" />
            {(["all", "open", "responded"] as const).map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all ${
                  statusFilter === status
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "bg-white/5 hover:bg-white/10 text-slate-400"
                }`}
              >
                {status === "all" ? "All" : status === "open" ? `Open (${openCount})` : "Responded"}
              </button>
            ))}
          </div>
        </div>

        {/* Inquiry Cards / List */}
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            Loading inquiry inbox...
          </div>
        ) : error ? (
          <div className="p-8 rounded-3xl bg-rose-500/10 border border-rose-500/20 text-center text-rose-300 text-sm">
            {error}
          </div>
        ) : filteredInquiries.length === 0 ? (
          <div className="p-12 rounded-3xl bg-white/[0.02] border border-white/10 text-center text-slate-400">
            <HelpCircle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h4 className="text-base font-semibold text-slate-300">No inquiries found</h4>
            <p className="text-xs text-slate-500 mt-1">
              {searchQuery || statusFilter !== "all"
                ? "Try adjusting your search query or status filter."
                : "No customer or retailer inquiries submitted yet."}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredInquiries.map((inquiry) => (
              <GlassCard key={inquiry.id} className="p-5 sm:p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/5 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
                      <Package className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center gap-2">
                        {inquiry.product_name}
                        <span className="text-xs text-slate-400 font-normal">({inquiry.product_sku})</span>
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                        <Store className="w-3.5 h-3.5 text-slate-500" />
                        <span>{inquiry.retailer_name || "Direct Customer / Guest"}</span>
                        <span>•</span>
                        <span>{new Date(inquiry.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    {inquiry.status.toLowerCase() === "open" ? (
                      <GlassBadge variant="warning" className="uppercase text-[10px] tracking-wider">
                        Action Required
                      </GlassBadge>
                    ) : (
                      <GlassBadge variant="success" className="uppercase text-[10px] tracking-wider">
                        Responded
                      </GlassBadge>
                    )}
                  </div>
                </div>

                {/* Inquiry Message Box */}
                <div className="p-3.5 rounded-2xl bg-white/[0.03] border border-white/5 text-xs text-slate-200">
                  <p className="text-[11px] font-semibold text-indigo-300 uppercase tracking-wider mb-1">
                    Retailer Question:
                  </p>
                  <p className="leading-relaxed whitespace-pre-wrap">{inquiry.message}</p>
                </div>

                {/* Staff Response Preview (if answered) */}
                {inquiry.response && (
                  <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-200">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-[11px] font-semibold text-emerald-300 uppercase tracking-wider flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Staff Answer:
                      </p>
                      {inquiry.responded_at && (
                        <span className="text-[10px] text-emerald-400">
                          {new Date(inquiry.responded_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                    <p className="leading-relaxed whitespace-pre-wrap">{inquiry.response}</p>
                  </div>
                )}

                {/* Action Row */}
                <div className="flex items-center justify-end gap-2 pt-1">
                  <GlassButton
                    variant={inquiry.status.toLowerCase() === "open" ? "primary" : "secondary"}
                    size="sm"
                    onClick={() => handleOpenRespondModal(inquiry)}
                    className="flex items-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" />
                    {inquiry.status.toLowerCase() === "open" ? "Respond to Retailer" : "Edit Response"}
                  </GlassButton>
                </div>
              </GlassCard>
            ))}
          </div>
        )}

        {/* Response Modal */}
        {selectedInquiry && (
          <GlassModal
            isOpen={true}
            onClose={() => setSelectedInquiry(null)}
            title={`Reply to Inquiry: ${selectedInquiry.product_name}`}
            description={`Inquiry from ${selectedInquiry.retailer_name || "Retailer"} regarding ${selectedInquiry.product_sku}`}
          >
            <form onSubmit={handleSendResponse} className="space-y-4 pt-2">
              {modalError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                  {modalError}
                </div>
              )}

              <div className="p-3.5 rounded-2xl bg-white/[0.03] border border-white/5 text-xs text-slate-300">
                <p className="text-[11px] font-semibold text-slate-400 mb-1">Question:</p>
                <p>{selectedInquiry.message}</p>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">
                  Your Answer (Retailer will receive in-app & notification)
                </label>
                <textarea
                  rows={5}
                  value={responseText}
                  onChange={(e) => setResponseText(e.target.value)}
                  placeholder="Provide quotation details, dispatch timelines, or pricing breakdown..."
                  disabled={isSubmitting}
                  className="w-full p-3.5 rounded-2xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:opacity-50"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <GlassButton
                  type="button"
                  variant="secondary"
                  onClick={() => setSelectedInquiry(null)}
                  disabled={isSubmitting}
                >
                  Cancel
                </GlassButton>
                <GlassButton
                  type="submit"
                  variant="primary"
                  disabled={!responseText.trim() || isSubmitting}
                  className="flex items-center gap-1.5"
                >
                  {isSubmitting ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Sending & Notifying...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Send Response</span>
                    </>
                  )}
                </GlassButton>
              </div>
            </form>
          </GlassModal>
        )}
      </ListViewTemplate>
    </AppLayout>
  );
}
