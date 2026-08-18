import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { StatusBadge } from "@/components/StatusBadge";

interface MockStockItem {
  product_id: string;
  sku: string;
  name: string;
  base_uom_name: string;
  total_on_hand: number;
  preferred_uom_name?: string;
  preferred_uom_qty?: number;
  stock_status: "ok" | "low" | "critical";
  warehouses: { warehouse_name: string; on_hand: number }[];
}

describe("Multi-Warehouse Stock View UI Components", () => {
  const columns: DataTableColumn<MockStockItem>[] = [
    {
      key: "sku",
      header: "SKU",
      render: (item) => <span className="font-mono">{item.sku}</span>,
    },
    {
      key: "name",
      header: "Product Name",
      render: (item) => <span>{item.name}</span>,
    },
    {
      key: "total_on_hand",
      header: "Total On Hand",
      render: (item) => (
        <div>
          <span data-testid="total-on-hand">
            {item.total_on_hand} {item.base_uom_name}
          </span>
          {item.preferred_uom_name && (
            <span data-testid="preferred-uom">
              ≈ {item.preferred_uom_qty} {item.preferred_uom_name}s
            </span>
          )}
        </div>
      ),
    },
    {
      key: "warehouses",
      header: "Warehouses",
      render: (item) => (
        <div data-testid="warehouse-chips">
          {item.warehouses.map((w) => (
            <span key={w.warehouse_name}>
              {w.warehouse_name}: {w.on_hand}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: "stock_status",
      header: "Status",
      render: (item) => <StatusBadge status={item.stock_status} />,
    },
  ];

  const sampleStock: MockStockItem[] = [
    {
      product_id: "p1",
      sku: "RICE-5KG",
      name: "Basmati Rice 5kg",
      base_uom_name: "pcs",
      total_on_hand: 120,
      preferred_uom_name: "Case",
      preferred_uom_qty: 5,
      stock_status: "ok",
      warehouses: [
        { warehouse_name: "Main Hub", on_hand: 80 },
        { warehouse_name: "North Depot", on_hand: 40 },
      ],
    },
    {
      product_id: "p2",
      sku: "OIL-1L",
      name: "Sunflower Oil 1L",
      base_uom_name: "pcs",
      total_on_hand: 8,
      stock_status: "critical",
      warehouses: [{ warehouse_name: "Main Hub", on_hand: 8 }],
    },
  ];

  it("should render stock overview with multi-warehouse distributions and status badges", () => {
    render(
      <DataTable columns={columns} data={sampleStock} keyExtractor={(item) => item.product_id} />,
    );

    expect(screen.getAllByText("RICE-5KG").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Basmati Rice 5kg").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/120 pcs/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/5 Cases/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Main Hub: 80/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Healthy").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Critical").length).toBeGreaterThan(0);
  });
});
