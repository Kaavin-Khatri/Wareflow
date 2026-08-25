import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BarcodeScannerModal } from "@/components/barcode/BarcodeScannerModal";
import { ProductLabelSheetModal } from "@/components/barcode/ProductLabelSheetModal";
import { ProductBarcodeCard } from "@/components/barcode/ProductBarcodeCard";
import { apiClient } from "@/lib/api-client";

// Mock apiClient
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

// Mock html5-qrcode library
vi.mock("html5-qrcode", () => {
  return {
    Html5Qrcode: class {
      start = vi.fn().mockResolvedValue(true);
      stop = vi.fn().mockResolvedValue(true);
      clear = vi.fn().mockReturnValue(true);
      scanFile = vi.fn().mockResolvedValue("2012345678906");
    },
  };
});

describe("Barcode Scanner & Label Sheet Components (Step 18.1)", () => {
  const sampleProduct = {
    id: "prod-test-1",
    sku: "TEST-SEV-500G",
    name: "Ratlam Sev Premium 500g",
    barcode: "2012345678906",
    wholesale_price: 120,
    cost_price: 85,
    unit: "Packet",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("BarcodeScannerModal", () => {
    it("renders camera scanner modal with mode tabs", () => {
      const handleClose = vi.fn();
      const handleScan = vi.fn();

      render(
        <BarcodeScannerModal
          isOpen={true}
          onClose={handleClose}
          onScanSuccess={handleScan}
          title="Floor Barcode Scanner"
        />,
      );

      expect(screen.getByText("Floor Barcode Scanner")).toBeDefined();
      expect(screen.getByText("Camera")).toBeDefined();
      expect(screen.getByText("Image File")).toBeDefined();
      expect(screen.getByText("Manual Input")).toBeDefined();
    });

    it("switches to manual mode and resolves barcode on input submit", async () => {
      const handleClose = vi.fn();
      const handleScan = vi.fn();

      (apiClient.get as any).mockResolvedValueOnce(sampleProduct);

      render(
        <BarcodeScannerModal
          isOpen={true}
          onClose={handleClose}
          onScanSuccess={handleScan}
          autoLookupProduct={true}
        />,
      );

      // Switch to manual mode
      fireEvent.click(screen.getByText("Manual Input"));

      const input = screen.getByTestId("manual-barcode-input");
      expect(input).toBeDefined();

      fireEvent.change(input, { target: { value: "2012345678906" } });
      fireEvent.click(screen.getByText("Lookup"));

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalledWith("/products/by-barcode/2012345678906");
      });

      await waitFor(() => {
        expect(handleScan).toHaveBeenCalledWith("2012345678906", sampleProduct);
      });
    });

    it("handles cancel button click", () => {
      const handleClose = vi.fn();
      const handleScan = vi.fn();

      render(
        <BarcodeScannerModal isOpen={true} onClose={handleClose} onScanSuccess={handleScan} />,
      );

      fireEvent.click(screen.getByText("Cancel"));
      expect(handleClose).toHaveBeenCalled();
    });
  });

  describe("ProductLabelSheetModal", () => {
    it("renders printable label sheet with customized copies and barcode images", () => {
      const handleClose = vi.fn();

      render(
        <ProductLabelSheetModal isOpen={true} onClose={handleClose} product={sampleProduct} />,
      );

      expect(screen.getByText("Print Product Barcode Labels")).toBeDefined();
      expect(screen.getAllByText("Ratlam Sev Premium 500g").length).toBeGreaterThan(0);
      expect(screen.getByText("Print Label Sheet")).toBeDefined();
    });

    it("switches format to QR Code mode", () => {
      const handleClose = vi.fn();

      render(
        <ProductLabelSheetModal isOpen={true} onClose={handleClose} product={sampleProduct} />,
      );

      const codeSelect = screen.getByDisplayValue("1D Linear Barcode (EAN-13)");
      fireEvent.change(codeSelect, { target: { value: "qr" } });

      expect(screen.getByDisplayValue("2D Matrix QR Code")).toBeDefined();
    });
  });

  describe("ProductBarcodeCard", () => {
    it("renders barcode card with tabs and print sheet trigger", () => {
      render(<ProductBarcodeCard product={sampleProduct} />);

      expect(screen.getByText("Barcode (1D)")).toBeDefined();
      expect(screen.getByText("QR Code (2D)")).toBeDefined();
      expect(screen.getByText("Print Sheet")).toBeDefined();
      expect(screen.getAllByText("2012345678906").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Download PNG")).toBeDefined();
    });

    it("switches to 2D QR view on tab click", () => {
      render(<ProductBarcodeCard product={sampleProduct} />);

      fireEvent.click(screen.getByText("QR Code (2D)"));
      expect(screen.getByText(`SKU: ${sampleProduct.sku}`)).toBeDefined();
    });
  });
});
