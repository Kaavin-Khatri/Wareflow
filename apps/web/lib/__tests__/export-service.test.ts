import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "../api-client";

describe("apiClient.downloadBlob (Excel / PDF Document Export)", () => {
  beforeEach(() => {
    // Mock URL.createObjectURL and URL.revokeObjectURL
    global.window.URL.createObjectURL = vi.fn().mockReturnValue("blob:mock-url-123");
    global.window.URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should trigger browser blob download for purchase order PDF export", async () => {
    const mockBlob = new Blob(["%PDF-1.4 mock pdf content"], { type: "application/pdf" });
    const appendChildSpy = vi.spyOn(document.body, "appendChild");
    const removeChildSpy = vi.spyOn(document.body, "removeChild");

    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      statusText: "OK",
      blob: async () => mockBlob,
    } as Response);

    await apiClient.downloadBlob("/purchase-orders/po-1/pdf", "PO-2026-0001.pdf");

    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/purchase-orders/po-1/pdf"));
    expect(window.URL.createObjectURL).toHaveBeenCalledWith(mockBlob);
    expect(appendChildSpy).toHaveBeenCalled();
    expect(removeChildSpy).toHaveBeenCalled();
    expect(window.URL.revokeObjectURL).toHaveBeenCalledWith("blob:mock-url-123");
  });

  it("should trigger browser blob download for stock overview Excel (.xlsx) export", async () => {
    const mockBlob = new Blob(["mock-excel-binary-stream"], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      statusText: "OK",
      blob: async () => mockBlob,
    } as Response);

    await apiClient.downloadBlob("/stock/overview.xlsx", "Stock_Overview.xlsx");

    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/stock/overview.xlsx"));
    expect(window.URL.createObjectURL).toHaveBeenCalledWith(mockBlob);
    expect(window.URL.revokeObjectURL).toHaveBeenCalledWith("blob:mock-url-123");
  });

  it("should trigger browser blob download for AR Aging Excel (.xlsx) export", async () => {
    const mockBlob = new Blob(["mock-excel-binary-stream"], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      statusText: "OK",
      blob: async () => mockBlob,
    } as Response);

    await apiClient.downloadBlob("/analytics/ar-aging.xlsx", "Wareflow_AR_Aging_Report_today.xlsx");

    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/analytics/ar-aging.xlsx"));
    expect(window.URL.createObjectURL).toHaveBeenCalledWith(mockBlob);
  });

  it("should throw error when export endpoint returns error status code", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
    } as Response);

    await expect(
      apiClient.downloadBlob("/purchase-orders/non-existent/pdf", "fail.pdf"),
    ).rejects.toThrow("Download failed with status 404");
  });
});
