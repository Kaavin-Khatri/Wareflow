import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ProductImportPage from "@/app/admin/products/import/page";
import { apiClient } from "@/lib/api-client";

// Mock apiClient
vi.mock("@/lib/api-client", () => ({
  getAuthToken: async () => "test_token",
  apiClient: {
    upload: vi.fn(),
    downloadBlob: vi.fn(),
  },
}));

// Mock Next.js AppLayout
vi.mock("@/components/AppLayout", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe("Bulk CSV Product Import & Export UI Suite (Step 18.2)", () => {
  const samplePreviewResponse = {
    dry_run: true,
    summary: {
      total_rows: 3,
      valid_count: 2,
      create_count: 1,
      update_count: 1,
      reject_count: 1,
    },
    rows: [
      {
        row_number: 2,
        action: "create",
        sku: "NAMKEEN-SEV-500G",
        name: "Ratlam Sev 500g",
        wholesale_price: 120,
        cost_price: 85,
        category_name: "Namkeen",
        unit: "Packet",
        hsn_code: "21069099",
        barcode: "(auto EAN-13)",
        errors: [],
      },
      {
        row_number: 3,
        action: "update",
        sku: "GRAIN-RICE-25KG",
        name: "Basmati Rice 25kg",
        wholesale_price: 2450,
        cost_price: 2100,
        category_name: "Grains",
        unit: "Bag",
        hsn_code: "10063020",
        barcode: "8901234567890",
        errors: [],
      },
      {
        row_number: 4,
        action: "reject",
        sku: "BAD-SKU",
        name: "Invalid Item",
        wholesale_price: null,
        cost_price: null,
        category_name: null,
        unit: null,
        hsn_code: null,
        barcode: null,
        errors: ["Wholesale price is required."],
      },
    ],
  };

  const sampleCommitResponse = {
    dry_run: false,
    summary: {
      total_rows: 3,
      valid_count: 2,
      create_count: 1,
      update_count: 1,
      reject_count: 1,
    },
    rows: samplePreviewResponse.rows,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    window.confirm = vi.fn().mockReturnValue(true);
  });

  it("renders page title, template download, and drag-and-drop dropzone", () => {
    render(<ProductImportPage />);

    expect(screen.getByText("Bulk Product Import & Export")).toBeDefined();
    expect(screen.getByText("Download CSV Template")).toBeDefined();
    expect(screen.getByText("Export Catalog CSV")).toBeDefined();
    expect(screen.getByText("Drag and drop your product CSV file")).toBeDefined();
  });

  it("handles CSV file upload and displays dry-run preview with KPI metrics", async () => {
    (apiClient.upload as any).mockResolvedValueOnce(samplePreviewResponse);

    render(<ProductImportPage />);

    const fileInput = screen.getByTestId("csv-file-input");
    const testFile = new File(["sku,name\nTEST,Test Product"], "test_catalog.csv", {
      type: "text/csv",
    });

    fireEvent.change(fileInput, { target: { files: [testFile] } });

    await waitFor(() => {
      expect(apiClient.upload).toHaveBeenCalledWith(
        "/products/import?dry_run=true",
        expect.any(FormData),
      );
    });

    // Check KPI summary cards
    expect(screen.getByText("New (Create)")).toBeDefined();
    expect(screen.getByText("Existing (Update)")).toBeDefined();
    expect(screen.getByText("Rejected (Errors)")).toBeDefined();

    // Check table rows
    expect(screen.getByText("NAMKEEN-SEV-500G")).toBeDefined();
    expect(screen.getByText("Ratlam Sev 500g")).toBeDefined();
    expect(screen.getByText("GRAIN-RICE-25KG")).toBeDefined();
    expect(screen.getByText("Wholesale price is required.")).toBeDefined();
  });

  it("allows filtering preview rows by action type (create, update, reject)", async () => {
    (apiClient.upload as any).mockResolvedValueOnce(samplePreviewResponse);

    render(<ProductImportPage />);

    const fileInput = screen.getByTestId("csv-file-input");
    const testFile = new File(["sku,name"], "test.csv", { type: "text/csv" });
    fireEvent.change(fileInput, { target: { files: [testFile] } });

    await waitFor(() => {
      expect(screen.getByText("NAMKEEN-SEV-500G")).toBeDefined();
    });

    // Filter to Creates only
    fireEvent.click(screen.getByText("Creates (1)"));
    expect(screen.getByText("NAMKEEN-SEV-500G")).toBeDefined();

    // Filter to Errors only
    fireEvent.click(screen.getByText("Errors (1)"));
    expect(screen.getByText("Wholesale price is required.")).toBeDefined();
  });

  it("commits valid rows on confirm and renders success confirmation view", async () => {
    (apiClient.upload as any)
      .mockResolvedValueOnce(samplePreviewResponse) // dry-run
      .mockResolvedValueOnce(sampleCommitResponse); // commit

    render(<ProductImportPage />);

    const fileInput = screen.getByTestId("csv-file-input");
    const testFile = new File(["sku,name"], "test.csv", { type: "text/csv" });
    fireEvent.change(fileInput, { target: { files: [testFile] } });

    await waitFor(() => {
      expect(screen.getByText("Confirm & Commit 2 Products")).toBeDefined();
    });

    fireEvent.click(screen.getByText("Confirm & Commit 2 Products"));

    await waitFor(() => {
      expect(apiClient.upload).toHaveBeenCalledWith(
        "/products/import?dry_run=false",
        expect.any(FormData),
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Product Catalog Import Successful")).toBeDefined();
      expect(screen.getByText("View Product Catalog")).toBeDefined();
    });
  });

  it("triggers CSV template download and catalog export", async () => {
    (apiClient.downloadBlob as any).mockResolvedValue(true);

    render(<ProductImportPage />);

    fireEvent.click(screen.getByText("Download CSV Template"));
    expect(apiClient.downloadBlob).toHaveBeenCalledWith(
      "/products/template.csv",
      "wareflow_product_import_template.csv",
    );

    fireEvent.click(screen.getByText("Export Catalog CSV"));
    expect(apiClient.downloadBlob).toHaveBeenCalledWith(
      "/products/export.csv",
      "wareflow_products_catalog.csv",
    );
  });
});
