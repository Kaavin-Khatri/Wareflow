"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { apiClient } from "@/lib/api-client";
import {
  Upload,
  FileSpreadsheet,
  Download,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  PlusCircle,
  RefreshCw,
  XCircle,
  FileText,
  Sparkles,
  ArrowRight,
  Package,
  Layers,
} from "lucide-react";

export interface PreviewRow {
  row_number: number;
  action: "create" | "update" | "reject";
  sku: string;
  name: string;
  wholesale_price?: number | null;
  cost_price?: number | null;
  category_name?: string | null;
  unit?: string | null;
  hsn_code?: string | null;
  barcode?: string | null;
  errors: string[];
}

export interface ImportSummary {
  total_rows: number;
  valid_count: number;
  create_count: number;
  update_count: number;
  reject_count: number;
}

export interface ImportResponse {
  dry_run: boolean;
  summary: ImportSummary;
  rows: PreviewRow[];
}

export default function ProductImportPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [commitLoading, setCommitLoading] = useState<boolean>(false);
  const [previewData, setPreviewData] = useState<ImportResponse | null>(null);
  const [committedData, setCommittedData] = useState<ImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filterAction, setFilterAction] = useState<"all" | "create" | "update" | "reject">("all");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDownloadTemplate = async () => {
    try {
      await apiClient.downloadBlob(
        "/products/template.csv",
        "wareflow_product_import_template.csv",
      );
    } catch (err: any) {
      setError(err?.message || "Failed to download CSV template.");
    }
  };

  const handleExportCatalog = async () => {
    try {
      await apiClient.downloadBlob("/products/export.csv", "wareflow_products_catalog.csv");
    } catch (err: any) {
      setError(err?.message || "Failed to export products catalog.");
    }
  };

  const processFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Please select a valid CSV (.csv) file.");
      return;
    }

    setSelectedFile(file);
    setError(null);
    setPreviewLoading(true);
    setCommittedData(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await apiClient.upload<ImportResponse>("/products/import?dry_run=true", formData);
      setPreviewData(res);
    } catch (err: any) {
      console.error("Preview import failed:", err);
      setError(err?.message || "Failed to parse CSV preview.");
      setPreviewData(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleCommitImport = async () => {
    if (!selectedFile || !previewData || previewData.summary.valid_count === 0) return;

    if (
      !confirm(
        `Are you sure you want to commit this import? This will create ${previewData.summary.create_count} new product(s) and update ${previewData.summary.update_count} existing product(s).`,
      )
    ) {
      return;
    }

    setCommitLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await apiClient.upload<ImportResponse>(
        "/products/import?dry_run=false",
        formData,
      );
      setCommittedData(res);
      setPreviewData(null);
    } catch (err: any) {
      console.error("Commit import failed:", err);
      setError(err?.message || "Failed to commit product import.");
    } finally {
      setCommitLoading(false);
    }
  };

  const filteredRows = (previewData?.rows || []).filter((r) => {
    if (filterAction === "all") return true;
    return r.action === filterAction;
  });

  return (
    <AppLayout>
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Header with Navigation & Templates */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
          <div className="flex items-center gap-3">
            <Link href="/admin/products">
              <button className="p-2 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-[var(--text-muted)] hover:text-[var(--text)] transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </button>
            </Link>
            <div>
              <h1 className="text-xl font-bold text-[var(--text)] flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-purple-400" />
                Bulk Product Import & Export
              </h1>
              <p className="text-xs text-[var(--text-muted)]">
                Onboard supplier price lists, update wholesale catalog prices, and export SKUs via
                CSV.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={handleDownloadTemplate}
              className="flex items-center gap-1.5 text-xs font-semibold"
            >
              <Download className="w-3.5 h-3.5 text-purple-400" />
              <span>Download CSV Template</span>
            </GlassButton>
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={handleExportCatalog}
              className="flex items-center gap-1.5 text-xs font-semibold"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
              <span>Export Catalog CSV</span>
            </GlassButton>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-start gap-2.5 animate-in fade-in">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
            <div className="flex-1 leading-relaxed">{error}</div>
          </div>
        )}

        {/* Post-Commit Success Card */}
        {committedData && (
          <GlassCard className="p-6 text-center space-y-4 animate-in fade-in zoom-in-95">
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center mx-auto shadow-lg">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-[var(--text)]">
                Product Catalog Import Successful
              </h2>
              <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto">
                Processed {committedData.summary.total_rows} line items:{" "}
                <span className="font-bold text-emerald-400">
                  {committedData.summary.create_count} created
                </span>
                ,{" "}
                <span className="font-bold text-cyan-400">
                  {committedData.summary.update_count} updated
                </span>
                ,{" "}
                <span className="font-mono text-rose-400">
                  {committedData.summary.reject_count} rejected
                </span>
                .
              </p>
            </div>
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setCommittedData(null);
                  setSelectedFile(null);
                  setPreviewData(null);
                }}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--surface-hover)] border border-[var(--border)] text-[var(--text)] hover:bg-[var(--surface)] transition-all"
              >
                Import Another CSV
              </button>
              <Link href="/admin/products">
                <GlassButton
                  variant="primary"
                  size="md"
                  className="font-bold flex items-center gap-1.5 shadow-lg"
                >
                  <span>View Product Catalog</span>
                  <ArrowRight className="w-4 h-4" />
                </GlassButton>
              </Link>
            </div>
          </GlassCard>
        )}

        {/* Upload Dropzone (When not committed) */}
        {!committedData && (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-3xl p-8 text-center transition-all ${
              isDragging
                ? "border-[var(--accent)] bg-[var(--accent)]/10 scale-[0.99]"
                : "border-[var(--border)] hover:border-[var(--accent)]/60 bg-[var(--glass-bg)]"
            }`}
          >
            <div className="max-w-md mx-auto space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-[var(--surface-hover)] border border-[var(--border)] text-[var(--accent)] flex items-center justify-center mx-auto shadow-inner">
                <Upload className="w-7 h-7" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-[var(--text)]">
                  {selectedFile ? selectedFile.name : "Drag and drop your product CSV file"}
                </h3>
                <p className="text-xs text-[var(--text-muted)]">
                  Supports comma-separated `.csv` files with SKU, Name, and Wholesale Price.
                </p>
              </div>
              <div className="pt-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,text/csv"
                  onChange={handleFileChange}
                  className="hidden"
                  data-testid="csv-file-input"
                />
                <GlassButton
                  type="button"
                  variant="primary"
                  size="md"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={previewLoading}
                  className="font-bold shadow-md"
                >
                  {previewLoading ? (
                    <span className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Analyzing CSV Rows...
                    </span>
                  ) : (
                    <span>{selectedFile ? "Choose Different File" : "Select CSV File"}</span>
                  )}
                </GlassButton>
              </div>
            </div>
          </div>
        )}

        {/* Dry-Run Validation Preview Section */}
        {previewData && !committedData && (
          <div className="space-y-4 animate-in fade-in">
            {/* KPI Summary Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <GlassCard className="p-3.5 flex items-center justify-between border-[var(--border)]">
                <div>
                  <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
                    Total Rows
                  </span>
                  <span className="text-xl font-bold font-mono text-[var(--text)]">
                    {previewData.summary.total_rows}
                  </span>
                </div>
                <div className="w-9 h-9 rounded-xl bg-[var(--surface-hover)] text-[var(--text-muted)] flex items-center justify-center">
                  <FileText className="w-5 h-5" />
                </div>
              </GlassCard>

              <GlassCard className="p-3.5 flex items-center justify-between border-emerald-500/30 bg-emerald-500/5">
                <div>
                  <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">
                    New (Create)
                  </span>
                  <span className="text-xl font-bold font-mono text-emerald-400">
                    {previewData.summary.create_count}
                  </span>
                </div>
                <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                  <PlusCircle className="w-5 h-5" />
                </div>
              </GlassCard>

              <GlassCard className="p-3.5 flex items-center justify-between border-cyan-500/30 bg-cyan-500/5">
                <div>
                  <span className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider block">
                    Existing (Update)
                  </span>
                  <span className="text-xl font-bold font-mono text-cyan-400">
                    {previewData.summary.update_count}
                  </span>
                </div>
                <div className="w-9 h-9 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center">
                  <RefreshCw className="w-5 h-5" />
                </div>
              </GlassCard>

              <GlassCard className="p-3.5 flex items-center justify-between border-rose-500/30 bg-rose-500/5">
                <div>
                  <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block">
                    Rejected (Errors)
                  </span>
                  <span className="text-xl font-bold font-mono text-rose-400">
                    {previewData.summary.reject_count}
                  </span>
                </div>
                <div className="w-9 h-9 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center">
                  <XCircle className="w-5 h-5" />
                </div>
              </GlassCard>
            </div>

            {/* Filter Pills & Commit Action Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-2xl bg-[var(--surface-hover)] border border-[var(--border)]">
              {/* Filter Tabs */}
              <div className="flex items-center gap-1 text-xs">
                <button
                  type="button"
                  onClick={() => setFilterAction("all")}
                  className={`px-3 py-1.5 rounded-xl font-medium transition-colors ${
                    filterAction === "all"
                      ? "bg-[var(--accent)] text-white font-semibold"
                      : "text-[var(--text-muted)] hover:text-[var(--text)]"
                  }`}
                >
                  All Rows ({previewData.rows.length})
                </button>
                <button
                  type="button"
                  onClick={() => setFilterAction("create")}
                  className={`px-3 py-1.5 rounded-xl font-medium transition-colors ${
                    filterAction === "create"
                      ? "bg-emerald-600 text-white font-semibold"
                      : "text-emerald-400 hover:text-emerald-300"
                  }`}
                >
                  Creates ({previewData.summary.create_count})
                </button>
                <button
                  type="button"
                  onClick={() => setFilterAction("update")}
                  className={`px-3 py-1.5 rounded-xl font-medium transition-colors ${
                    filterAction === "update"
                      ? "bg-cyan-600 text-white font-semibold"
                      : "text-cyan-400 hover:text-cyan-300"
                  }`}
                >
                  Updates ({previewData.summary.update_count})
                </button>
                <button
                  type="button"
                  onClick={() => setFilterAction("reject")}
                  className={`px-3 py-1.5 rounded-xl font-medium transition-colors ${
                    filterAction === "reject"
                      ? "bg-rose-600 text-white font-semibold"
                      : "text-rose-400 hover:text-rose-300"
                  }`}
                >
                  Errors ({previewData.summary.reject_count})
                </button>
              </div>

              {/* Confirm Import Button */}
              <GlassButton
                variant="primary"
                size="md"
                onClick={handleCommitImport}
                disabled={commitLoading || previewData.summary.valid_count === 0}
                className="font-bold flex items-center gap-2 shadow-lg sm:self-auto self-stretch justify-center"
              >
                {commitLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Committing Catalog...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                    <span>Confirm & Commit {previewData.summary.valid_count} Products</span>
                  </>
                )}
              </GlassButton>
            </div>

            {/* Dry-Run Preview Table */}
            <div className="rounded-2xl border border-[var(--border)] overflow-hidden bg-[var(--glass-bg)]">
              <div className="overflow-x-auto max-h-[60vh]">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="sticky top-0 bg-neutral-900/95 backdrop-blur-md text-[var(--text-muted)] font-mono border-b border-[var(--border)] z-10">
                    <tr>
                      <th className="py-2.5 px-3 w-12 text-center">#</th>
                      <th className="py-2.5 px-3 w-24">Action</th>
                      <th className="py-2.5 px-3">SKU</th>
                      <th className="py-2.5 px-3">Product Name</th>
                      <th className="py-2.5 px-3 text-right">Wholesale Price</th>
                      <th className="py-2.5 px-3 text-right">Cost Price</th>
                      <th className="py-2.5 px-3">Category</th>
                      <th className="py-2.5 px-3">Unit</th>
                      <th className="py-2.5 px-3">Barcode</th>
                      <th className="py-2.5 px-3">Status / Errors</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)]">
                    {filteredRows.length === 0 ? (
                      <tr>
                        <td
                          colSpan={10}
                          className="py-8 text-center text-xs text-[var(--text-muted)]"
                        >
                          No rows matching the current filter.
                        </td>
                      </tr>
                    ) : (
                      filteredRows.map((row) => (
                        <tr
                          key={row.row_number}
                          className={`hover:bg-white/[0.02] transition-colors ${
                            row.action === "reject"
                              ? "bg-rose-500/5"
                              : row.action === "create"
                                ? "bg-emerald-500/5"
                                : "bg-cyan-500/5"
                          }`}
                        >
                          <td className="py-2 px-3 text-center font-mono text-[11px] text-[var(--text-muted)]">
                            {row.row_number}
                          </td>
                          <td className="py-2 px-3">
                            {row.action === "create" && (
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                Create
                              </span>
                            )}
                            {row.action === "update" && (
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                                Update
                              </span>
                            )}
                            {row.action === "reject" && (
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/30">
                                Reject
                              </span>
                            )}
                          </td>
                          <td className="py-2 px-3 font-mono font-semibold text-[var(--text)]">
                            {row.sku || <span className="text-rose-400 italic">Empty</span>}
                          </td>
                          <td className="py-2 px-3 text-[var(--text)] max-w-xs truncate">
                            {row.name || <span className="text-rose-400 italic">Empty</span>}
                          </td>
                          <td className="py-2 px-3 text-right font-mono font-medium text-[var(--text)]">
                            {row.wholesale_price !== null && row.wholesale_price !== undefined ? (
                              `₹${row.wholesale_price.toFixed(2)}`
                            ) : (
                              <span className="text-rose-400 italic">—</span>
                            )}
                          </td>
                          <td className="py-2 px-3 text-right font-mono text-[var(--text-muted)]">
                            {row.cost_price !== null && row.cost_price !== undefined
                              ? `₹${row.cost_price.toFixed(2)}`
                              : "—"}
                          </td>
                          <td className="py-2 px-3 text-[var(--text-muted)]">
                            {row.category_name || "—"}
                          </td>
                          <td className="py-2 px-3 font-mono text-[11px] text-[var(--text-muted)]">
                            {row.unit || "Piece"}
                          </td>
                          <td className="py-2 px-3 font-mono text-[11px] text-purple-300">
                            {row.barcode || "—"}
                          </td>
                          <td className="py-2 px-3">
                            {row.errors.length > 0 ? (
                              <div className="space-y-0.5">
                                {row.errors.map((err, i) => (
                                  <div
                                    key={i}
                                    className="text-[11px] text-rose-400 flex items-center gap-1 font-medium"
                                  >
                                    <AlertTriangle className="w-3 h-3 shrink-0" />
                                    <span>{err}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3 shrink-0" />
                                <span>Valid</span>
                              </span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
