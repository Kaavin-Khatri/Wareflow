"use client";

import React, { useState, useEffect, useRef } from "react";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassButton } from "@/components/glass/GlassButton";
import { apiClient } from "@/lib/api-client";
import {
  Camera,
  ScanLine,
  Upload,
  Keyboard,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Package,
  Layers,
  ArrowRight,
} from "lucide-react";
import { Html5Qrcode } from "html5-qrcode";

export interface ScannedProduct {
  id: string;
  sku: string;
  name: string;
  barcode?: string | null;
  wholesale_price?: number;
  cost_price?: number;
  unit?: string | null;
  is_active?: boolean;
}

export interface BarcodeScannerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScanSuccess: (scannedCode: string, product?: ScannedProduct | null) => void;
  title?: string;
  description?: string;
  autoLookupProduct?: boolean;
}

export function BarcodeScannerModal({
  isOpen,
  onClose,
  onScanSuccess,
  title = "Scan Product Barcode / QR",
  description = "Align product barcode or QR code within the scanning frame.",
  autoLookupProduct = true,
}: BarcodeScannerModalProps) {
  const [scannerMode, setScannerMode] = useState<"camera" | "upload" | "manual">("camera");
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [manualCode, setManualCode] = useState("");
  const [isLookingUp, setIsLookingUp] = useState(false);
  const [resolvedProduct, setResolvedProduct] = useState<ScannedProduct | null>(null);
  const [lastScannedCode, setLastScannedCode] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<"environment" | "user">("environment");

  const scannerRef = useRef<Html5Qrcode | null>(null);
  const scannerContainerId = "wareflow-html5-qr-reader";

  // Play a brief positive beep sound on barcode scan
  const playScanBeep = () => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        const ctx = new AudioCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(880, ctx.currentTime); // A5 note
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.15);
      }
    } catch {
      // Audio context might be restricted before user interaction
    }
  };

  // Handle successful code detection
  const handleDecodedText = async (decodedText: string) => {
    if (isLookingUp || decodedText === lastScannedCode) return;
    setLastScannedCode(decodedText);
    playScanBeep();

    if (!autoLookupProduct) {
      onScanSuccess(decodedText, null);
      onClose();
      return;
    }

    setIsLookingUp(true);
    setCameraError(null);

    try {
      const product = await apiClient.get<ScannedProduct>(
        `/products/by-barcode/${encodeURIComponent(decodedText)}`,
      );
      setResolvedProduct(product);
      onScanSuccess(decodedText, product);
      // Brief pause so user sees resolution confirmation before auto closing
      setTimeout(() => {
        onClose();
      }, 900);
    } catch (err: any) {
      console.warn("Product lookup by barcode failed:", err);
      // Still pass scanned code back to form
      onScanSuccess(decodedText, null);
      setCameraError(`Scanned code "${decodedText}" not found in catalog.`);
    } finally {
      setIsLookingUp(false);
    }
  };

  // Start Html5Qrcode camera
  useEffect(() => {
    if (!isOpen || scannerMode !== "camera") {
      if (scannerRef.current) {
        scannerRef.current
          .stop()
          .catch(() => {})
          .finally(() => {
            scannerRef.current?.clear();
            scannerRef.current = null;
          });
      }
      return;
    }

    let isMounted = true;

    const startCamera = async () => {
      setCameraError(null);
      try {
        const scanner = new Html5Qrcode(scannerContainerId);
        scannerRef.current = scanner;

        await scanner.start(
          { facingMode },
          {
            fps: 15,
            qrbox: { width: 260, height: 180 },
            aspectRatio: 1.333,
          },
          (decodedText) => {
            if (isMounted) {
              handleDecodedText(decodedText);
            }
          },
          () => {
            // Ignore frame-level scan misses
          },
        );
      } catch (err: any) {
        if (isMounted) {
          console.warn("Camera start warning:", err);
          setCameraError(
            err?.message ||
              "Could not access camera. Please check browser camera permissions or try manual entry.",
          );
        }
      }
    };

    const timer = setTimeout(startCamera, 300);

    return () => {
      isMounted = false;
      clearTimeout(timer);
      if (scannerRef.current) {
        scannerRef.current
          .stop()
          .catch(() => {})
          .finally(() => {
            scannerRef.current?.clear();
            scannerRef.current = null;
          });
      }
    };
  }, [isOpen, scannerMode, facingMode]);

  // Handle file upload scanning
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setIsLookingUp(true);
      setCameraError(null);
      const scanner = new Html5Qrcode("upload-scanner-temp");
      const decodedText = await scanner.scanFile(file, true);
      scanner.clear();
      await handleDecodedText(decodedText);
    } catch (err: any) {
      console.warn("File scan error:", err);
      setCameraError("No readable barcode or QR code detected in the selected image.");
    } finally {
      setIsLookingUp(false);
    }
  };

  // Handle manual input submit
  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualCode.trim()) return;
    handleDecodedText(manualCode.trim());
  };

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      description={description}
      maxWidth="md"
    >
      <div className="space-y-4 pt-1">
        {/* Mode Switcher Tabs */}
        <div className="flex items-center p-1 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)] gap-1 text-xs">
          <button
            type="button"
            onClick={() => setScannerMode("camera")}
            className={`flex-1 py-1.5 rounded-lg font-medium flex items-center justify-center gap-1.5 transition-colors ${
              scannerMode === "camera"
                ? "bg-[var(--accent)] text-white font-semibold shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text)]"
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            <span>Camera</span>
          </button>
          <button
            type="button"
            onClick={() => setScannerMode("upload")}
            className={`flex-1 py-1.5 rounded-lg font-medium flex items-center justify-center gap-1.5 transition-colors ${
              scannerMode === "upload"
                ? "bg-[var(--accent)] text-white font-semibold shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text)]"
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Image File</span>
          </button>
          <button
            type="button"
            onClick={() => setScannerMode("manual")}
            className={`flex-1 py-1.5 rounded-lg font-medium flex items-center justify-center gap-1.5 transition-colors ${
              scannerMode === "manual"
                ? "bg-[var(--accent)] text-white font-semibold shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text)]"
            }`}
          >
            <Keyboard className="w-3.5 h-3.5" />
            <span>Manual Input</span>
          </button>
        </div>

        {/* Resolved Product Banner */}
        {resolvedProduct && (
          <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between gap-3 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <span className="text-xs font-bold text-[var(--text)] block truncate">
                  {resolvedProduct.name}
                </span>
                <span className="text-[11px] font-mono text-emerald-400 block">
                  SKU: {resolvedProduct.sku} • ₹{resolvedProduct.wholesale_price}
                </span>
              </div>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/20 px-2 py-1 rounded-md shrink-0">
              Matched
            </span>
          </div>
        )}

        {/* Error Alert */}
        {cameraError && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-start gap-2 animate-in fade-in">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
            <div className="flex-1 leading-relaxed">{cameraError}</div>
          </div>
        )}

        {/* Camera View Mode */}
        {scannerMode === "camera" && (
          <div className="relative rounded-2xl overflow-hidden bg-black border border-[var(--glass-border)] aspect-[4/3] flex items-center justify-center shadow-inner">
            <div id={scannerContainerId} className="w-full h-full" />

            {/* Targeting Reticle & Scanning Animation */}
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="relative w-64 h-44 rounded-2xl border-2 border-dashed border-[var(--accent)] bg-[var(--accent)]/5 shadow-[0_0_24px_rgba(139,92,246,0.3)] flex items-center justify-center">
                {/* Laser scan line animation */}
                <div className="absolute inset-x-2 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-pulse" />
                <span className="text-[10px] font-mono tracking-widest text-[var(--accent)] bg-black/60 px-2 py-0.5 rounded-full uppercase">
                  Align Barcode / QR
                </span>
              </div>
            </div>

            {/* Flip Camera Button */}
            <button
              type="button"
              onClick={() =>
                setFacingMode((prev) => (prev === "environment" ? "user" : "environment"))
              }
              title="Flip Camera"
              className="absolute top-3 right-3 p-2 rounded-xl bg-black/60 text-white hover:bg-black/80 border border-white/20 transition-all active:scale-95"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Image File Mode */}
        {scannerMode === "upload" && (
          <div className="p-6 rounded-2xl border-2 border-dashed border-[var(--border)] hover:border-[var(--accent)] bg-[var(--glass-bg)] text-center space-y-3 transition-colors">
            <div className="w-12 h-12 rounded-2xl bg-[var(--surface-hover)] text-[var(--accent)] flex items-center justify-center mx-auto shadow-sm">
              <Upload className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold text-[var(--text)]">
                Upload barcode photo or scan image
              </p>
              <p className="text-[11px] text-[var(--text-muted)]">
                Supports PNG, JPEG, WEBP containing 1D Barcodes or QR Codes
              </p>
            </div>
            <label className="inline-block">
              <span className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent)] text-white cursor-pointer hover:bg-[var(--accent-hover)] transition-all shadow-md">
                Select Image File
              </span>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
                data-testid="barcode-file-input"
              />
            </label>
            <div id="upload-scanner-temp" className="hidden" />
          </div>
        )}

        {/* Manual Input Mode */}
        {scannerMode === "manual" && (
          <form onSubmit={handleManualSubmit} className="space-y-3">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[var(--text)]">
                Enter Barcode / SKU Manually:
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  autoFocus
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value)}
                  placeholder="e.g. 2012345678906 or SKU-NAMKEEN-001"
                  data-testid="manual-barcode-input"
                  className="flex-1 px-3 py-2 text-xs rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] font-mono focus:outline-none focus:border-[var(--accent)]"
                />
                <GlassButton
                  variant="primary"
                  size="sm"
                  disabled={!manualCode.trim() || isLookingUp}
                  className="font-bold flex items-center gap-1.5"
                >
                  <span>{isLookingUp ? "Finding..." : "Lookup"}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </GlassButton>
              </div>
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">
              Accepts 13-digit EAN-13, 12-digit UPC, Code-128, or direct SKU codes.
            </p>
          </form>
        )}

        {/* Footer info */}
        <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] pt-2 border-t border-[var(--border)] font-mono">
          <span>Supported: EAN-13, UPC, QR, Code-128</span>
          <button
            type="button"
            onClick={onClose}
            className="text-[var(--text-muted)] hover:text-[var(--text)] font-sans"
          >
            Cancel
          </button>
        </div>
      </div>
    </GlassModal>
  );
}
