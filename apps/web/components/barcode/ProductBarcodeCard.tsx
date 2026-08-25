"use client";

import React, { useState } from "react";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { ProductLabelSheetModal } from "./ProductLabelSheetModal";
import { Barcode, QrCode, Download, Printer, Copy, Check } from "lucide-react";

export interface ProductBarcodeCardProps {
  product: {
    id: string;
    sku: string;
    name: string;
    barcode?: string | null;
    wholesale_price?: number;
    unit?: string | null;
  };
  className?: string;
}

export function ProductBarcodeCard({ product, className }: ProductBarcodeCardProps) {
  const [activeTab, setActiveTab] = useState<"barcode" | "qr">("barcode");
  const [showPrintModal, setShowPrintModal] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const barcodeImageUrl = `${apiUrl}/products/${product.id}/barcode.png`;
  const qrImageUrl = `${apiUrl}/products/${product.id}/qr.png`;

  const barcodeValue = product.barcode || product.sku;

  const handleCopyCode = () => {
    if (!barcodeValue) return;
    navigator.clipboard.writeText(barcodeValue);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      <GlassCard className={`p-4 space-y-3.5 ${className || ""}`}>
        {/* Header with Switcher Tabs */}
        <div className="flex items-center justify-between gap-2 border-b border-[var(--border)] pb-2.5">
          <div className="flex items-center gap-1 p-0.5 rounded-lg bg-[var(--surface-hover)] border border-[var(--border)] text-xs">
            <button
              type="button"
              onClick={() => setActiveTab("barcode")}
              className={`px-2.5 py-1 rounded-md font-medium flex items-center gap-1.5 transition-colors ${
                activeTab === "barcode"
                  ? "bg-[var(--accent)] text-white font-semibold shadow-sm"
                  : "text-[var(--text-muted)] hover:text-[var(--text)]"
              }`}
            >
              <Barcode className="w-3.5 h-3.5" />
              <span>Barcode (1D)</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("qr")}
              className={`px-2.5 py-1 rounded-md font-medium flex items-center gap-1.5 transition-colors ${
                activeTab === "qr"
                  ? "bg-[var(--accent)] text-white font-semibold shadow-sm"
                  : "text-[var(--text-muted)] hover:text-[var(--text)]"
              }`}
            >
              <QrCode className="w-3.5 h-3.5" />
              <span>QR Code (2D)</span>
            </button>
          </div>

          <GlassButton
            size="sm"
            variant="secondary"
            onClick={() => setShowPrintModal(true)}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <Printer className="w-3.5 h-3.5 text-[var(--accent)]" />
            <span>Print Sheet</span>
          </GlassButton>
        </div>

        {/* Code Image Render Viewport */}
        <div className="rounded-2xl p-4 bg-white text-black flex flex-col items-center justify-center min-h-[140px] shadow-sm border border-slate-200">
          {activeTab === "barcode" ? (
            <div className="text-center space-y-1">
              <img
                src={barcodeImageUrl}
                alt={`Barcode for ${product.name}`}
                className="max-h-24 object-contain mx-auto"
              />
              <div className="text-xs font-mono font-bold text-slate-700 tracking-wider">
                {barcodeValue}
              </div>
            </div>
          ) : (
            <div className="text-center space-y-1">
              <img
                src={qrImageUrl}
                alt={`QR code for ${product.name}`}
                className="w-24 h-24 object-contain mx-auto"
              />
              <div className="text-[11px] font-mono text-slate-600">
                SKU: {product.sku}
              </div>
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-between text-xs pt-1">
          <button
            type="button"
            onClick={handleCopyCode}
            className="flex items-center gap-1 text-[var(--text-muted)] hover:text-[var(--text)] font-mono"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
            <span>{copied ? "Copied!" : barcodeValue}</span>
          </button>

          <a
            href={activeTab === "barcode" ? barcodeImageUrl : qrImageUrl}
            download={`product_${product.sku}_${activeTab}.png`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-semibold text-[var(--accent)] hover:underline"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PNG</span>
          </a>
        </div>
      </GlassCard>

      {/* Label Sheet Printing Modal */}
      {showPrintModal && (
        <ProductLabelSheetModal
          isOpen={showPrintModal}
          onClose={() => setShowPrintModal(false)}
          product={product}
        />
      )}
    </>
  );
}
