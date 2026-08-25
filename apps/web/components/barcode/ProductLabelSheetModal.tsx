"use client";

import React, { useState } from "react";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassButton } from "@/components/glass/GlassButton";
import { Printer, Sliders, Check, Sparkles, Layers, QrCode } from "lucide-react";

export interface PrintableProduct {
  id: string;
  sku: string;
  name: string;
  barcode?: string | null;
  wholesale_price?: number;
  unit?: string | null;
}

export interface ProductLabelSheetModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: PrintableProduct;
}

export function ProductLabelSheetModal({ isOpen, onClose, product }: ProductLabelSheetModalProps) {
  const [copies, setCopies] = useState<number>(24);
  const [sheetLayout, setSheetLayout] = useState<"a4-24" | "a4-14" | "single">("a4-24");
  const [showPrice, setShowPrice] = useState<boolean>(true);
  const [showSku, setShowSku] = useState<boolean>(true);
  const [codeType, setCodeType] = useState<"barcode" | "qr">("barcode");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const barcodeImageUrl = `${apiUrl}/products/${product.id}/barcode.png`;
  const qrImageUrl = `${apiUrl}/products/${product.id}/qr.png`;

  const handlePrint = () => {
    window.print();
  };

  const labelCount = sheetLayout === "a4-24" ? 24 : sheetLayout === "a4-14" ? 14 : 1;
  const activeCount = Math.max(1, copies);

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title="Print Product Barcode Labels"
      description="Generate standard multi-sticker sheets formatted for warehouse labeling."
      maxWidth="2xl"
    >
      <div className="space-y-4 pt-1">
        {/* Controls & Configuration Bar (Hidden in Print) */}
        <div className="print:hidden p-4 rounded-2xl bg-[var(--surface-hover)] border border-[var(--border)] space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            {/* Sheet Format */}
            <div className="space-y-1">
              <label className="font-semibold text-[var(--text)]">Sheet Format</label>
              <select
                value={sheetLayout}
                onChange={(e) => {
                  const val = e.target.value as any;
                  setSheetLayout(val);
                  if (val === "a4-24") setCopies(24);
                  else if (val === "a4-14") setCopies(14);
                  else setCopies(1);
                }}
                className="w-full px-2.5 py-1.5 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
              >
                <option value="a4-24">A4 Sheet — 24 Labels (3×8 Grid)</option>
                <option value="a4-14">A4 Sheet — 14 Labels (2×7 Grid)</option>
                <option value="single">Single Label Sticker</option>
              </select>
            </div>

            {/* Code Type */}
            <div className="space-y-1">
              <label className="font-semibold text-[var(--text)]">Code Format</label>
              <select
                value={codeType}
                onChange={(e) => setCodeType(e.target.value as any)}
                className="w-full px-2.5 py-1.5 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
              >
                <option value="barcode">1D Linear Barcode (EAN-13)</option>
                <option value="qr">2D Matrix QR Code</option>
              </select>
            </div>

            {/* Total Label Count */}
            <div className="space-y-1">
              <label className="font-semibold text-[var(--text)]">Stickers Count</label>
              <input
                type="number"
                min={1}
                max={96}
                value={copies}
                onChange={(e) => setCopies(Number(e.target.value))}
                className="w-full px-2.5 py-1.5 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] font-mono focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
          </div>

          {/* Toggles */}
          <div className="flex items-center gap-4 pt-1 text-xs text-[var(--text)]">
            <label className="inline-flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={showPrice}
                onChange={(e) => setShowPrice(e.target.checked)}
                className="rounded border-[var(--border)] text-[var(--accent)] focus:ring-0"
              />
              <span>Include Wholesale Price</span>
            </label>
            <label className="inline-flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={showSku}
                onChange={(e) => setShowSku(e.target.checked)}
                className="rounded border-[var(--border)] text-[var(--accent)] focus:ring-0"
              />
              <span>Include SKU Code</span>
            </label>
          </div>
        </div>

        {/* Printable Labels Sheet Preview Canvas */}
        <div className="border border-[var(--border)] rounded-2xl p-4 bg-slate-950/80 max-h-[50vh] overflow-y-auto print:max-h-none print:overflow-visible print:border-none print:bg-white print:p-0">
          <div
            className={`grid gap-2.5 print:gap-1.5 ${
              sheetLayout === "a4-24"
                ? "grid-cols-2 sm:grid-cols-3 print:grid-cols-3"
                : sheetLayout === "a4-14"
                  ? "grid-cols-1 sm:grid-cols-2 print:grid-cols-2"
                  : "grid-cols-1 max-w-xs mx-auto"
            }`}
          >
            {Array.from({ length: activeCount }).map((_, idx) => (
              <div
                key={idx}
                className="border border-slate-700/60 rounded-xl p-2 bg-white text-black text-center space-y-1 shadow-sm break-inside-avoid print:border-dashed print:border-slate-300 print:shadow-none"
              >
                <div className="text-[10px] font-bold text-slate-800 truncate leading-tight">
                  {product.name}
                </div>

                <div className="flex items-center justify-center my-0.5 min-h-[44px]">
                  {codeType === "barcode" ? (
                    <img
                      src={barcodeImageUrl}
                      alt={`Barcode for ${product.sku}`}
                      className="max-h-12 w-auto object-contain mx-auto print:max-h-11"
                    />
                  ) : (
                    <img
                      src={qrImageUrl}
                      alt={`QR code for ${product.sku}`}
                      className="w-12 h-12 object-contain mx-auto"
                    />
                  )}
                </div>

                <div className="flex items-center justify-between text-[9px] font-mono text-slate-600 px-1 border-t border-slate-200 pt-0.5">
                  {showSku ? <span>SKU: {product.sku}</span> : <span />}
                  {showPrice && product.wholesale_price !== undefined ? (
                    <span className="font-bold text-slate-900">₹{product.wholesale_price}</span>
                  ) : (
                    <span />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Actions (Hidden in Print) */}
        <div className="print:hidden flex items-center justify-between pt-2 border-t border-[var(--border)]">
          <div className="text-xs text-[var(--text-muted)] font-mono">
            {activeCount} labels configured
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-xl text-xs text-[var(--text-muted)] hover:text-[var(--text)] font-semibold"
            >
              Close
            </button>
            <GlassButton
              variant="primary"
              onClick={handlePrint}
              className="flex items-center gap-1.5 font-bold shadow-lg"
            >
              <Printer className="w-4 h-4" />
              <span>Print Label Sheet</span>
            </GlassButton>
          </div>
        </div>
      </div>
    </GlassModal>
  );
}
