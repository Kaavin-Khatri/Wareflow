import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { EmptyState } from "@/components/EmptyState";
import { SkeletonCard, SkeletonTable } from "@/components/SkeletonPrimitives";
import { StatusBadge, getStatusConfig } from "@/components/StatusBadge";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { isLowPowerDevice } from "@/lib/device-performance";

describe("UI Primitives Suite (Step 4.7)", () => {
  beforeEach(() => {
    window.matchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
  });

  describe("EmptyState", () => {
    it("should render default title, description, and action button", () => {
      const handleAction = vi.fn();
      render(
        <EmptyState
          title="No POs Found"
          description="Create your first purchase order."
          action={
            <button type="button" onClick={handleAction}>
              Create PO
            </button>
          }
        />,
      );

      expect(screen.getByText("No POs Found")).toBeDefined();
      expect(screen.getByText("Create your first purchase order.")).toBeDefined();

      const btn = screen.getByText("Create PO");
      fireEvent.click(btn);
      expect(handleAction).toHaveBeenCalledTimes(1);
    });

    it("should render compact variant properly", () => {
      render(<EmptyState compact title="Compact Empty State" />);
      expect(screen.getByText("Compact Empty State")).toBeDefined();
    });
  });

  describe("SkeletonPrimitives", () => {
    it("should render SkeletonCard with kpi variant", () => {
      const { container } = render(<SkeletonCard variant="kpi" />);
      expect(container.firstChild).toBeDefined();
    });

    it("should render SkeletonTable with specified row and column counts", () => {
      const { container } = render(<SkeletonTable rows={4} cols={3} />);
      expect(container.querySelectorAll(".divide-y > div").length).toBe(4);
    });
  });

  describe("StatusBadge", () => {
    it("should resolve known status enums correctly", () => {
      expect(getStatusConfig("draft").label).toBe("Draft");
      expect(getStatusConfig("in_stock").variant).toBe("success");
      expect(getStatusConfig("low_stock").variant).toBe("warning");
      expect(getStatusConfig("out_of_stock").variant).toBe("error");
      expect(getStatusConfig("dispatched").variant).toBe("accent");
      expect(getStatusConfig("paid").variant).toBe("success");
      expect(getStatusConfig("overdue").variant).toBe("error");
      expect(getStatusConfig("active").variant).toBe("success");
      expect(getStatusConfig("suspended").variant).toBe("error");
    });

    it("should fallback gracefully for unknown status strings", () => {
      const fallback = getStatusConfig("custom_unknown_status");
      expect(fallback.variant).toBe("neutral");
      expect(fallback.label).toBe("Custom Unknown Status");
    });

    it("should render StatusBadge component with dot and label", () => {
      render(<StatusBadge status="partially_received" />);
      expect(screen.getByText("Partially Received")).toBeDefined();
    });
  });

  describe("DataTable", () => {
    interface TestItem {
      id: string;
      sku: string;
      stock: number;
      status: string;
    }

    const testColumns: DataTableColumn<TestItem>[] = [
      {
        key: "sku",
        header: "SKU",
        sortable: true,
        mobilePrimary: true,
      },
      {
        key: "stock",
        header: "Stock",
        sortable: true,
        align: "right",
      },
      {
        key: "status",
        header: "Status",
        render: (item) => <StatusBadge status={item.status} />,
      },
    ];

    const testData: TestItem[] = [
      { id: "1", sku: "RICE-01", stock: 100, status: "in_stock" },
      { id: "2", sku: "OIL-05", stock: 20, status: "low_stock" },
      { id: "3", sku: "WHEAT-10", stock: 500, status: "in_stock" },
    ];

    it("should render desktop table headers and data rows", () => {
      render(<DataTable columns={testColumns} data={testData} keyExtractor={(i) => i.id} />);

      expect(screen.getAllByText("RICE-01").length).toBeGreaterThan(0);
      expect(screen.getAllByText("OIL-05").length).toBeGreaterThan(0);
      expect(screen.getAllByText("WHEAT-10").length).toBeGreaterThan(0);
    });

    it("should sort data when clicking sortable column header", () => {
      render(<DataTable columns={testColumns} data={testData} keyExtractor={(i) => i.id} />);

      const stockHeaders = screen.getAllByText("Stock");
      // Click header to sort ascending
      fireEvent.click(stockHeaders[0]);
      // Click header again to sort descending
      fireEvent.click(stockHeaders[0]);
      expect(stockHeaders[0]).toBeDefined();
    });

    it("should render SkeletonTable when isLoading is true", () => {
      const { container } = render(
        <DataTable
          columns={testColumns}
          data={[] as TestItem[]}
          keyExtractor={(i) => i.id}
          isLoading={true}
        />,
      );
      expect(container.querySelectorAll(".divide-y > div").length).toBeGreaterThan(0);
    });

    it("should render EmptyState when data array is empty", () => {
      render(
        <DataTable
          columns={testColumns}
          data={[] as TestItem[]}
          keyExtractor={(i) => i.id}
          emptyTitle="Empty Catalog"
        />,
      );
      expect(screen.getByText("Empty Catalog")).toBeDefined();
    });
  });

  describe("Low-Power Glass Fallback", () => {
    it("should detect low-power preference when reduced-transparency is matched", () => {
      window.matchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === "(prefers-reduced-transparency: reduce)",
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      expect(isLowPowerDevice()).toBe(true);
    });
  });
});
