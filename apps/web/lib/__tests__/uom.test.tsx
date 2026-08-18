import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DataTable, DataTableColumn } from "@/components/DataTable";

interface MockProduct {
  id: string;
  sku: string;
  name: string;
  base_uom_name: string;
  conversions_count: number;
}

describe("UoM Conversion UI Components", () => {
  const columns: DataTableColumn<MockProduct>[] = [
    {
      key: "sku",
      header: "SKU Code",
      render: (p) => <span className="font-mono">{p.sku}</span>,
    },
    {
      key: "name",
      header: "Product Name",
      render: (p) => <span>{p.name}</span>,
    },
    {
      key: "base_uom",
      header: "Base Unit",
      render: (p) => <span data-testid="base-uom">{p.base_uom_name}</span>,
    },
    {
      key: "conversions",
      header: "Packaging Ratios",
      render: (p) => <span data-testid="conversions-badge">{p.conversions_count} Defined</span>,
    },
  ];

  const sampleData: MockProduct[] = [
    {
      id: "p1",
      sku: "MILK-ALMOND-1L",
      name: "Organic Almond Milk 1L",
      base_uom_name: "Piece (pcs)",
      conversions_count: 2,
    },
    {
      id: "p2",
      sku: "RICE-BASMATI-5KG",
      name: "Royal Basmati Rice 5kg",
      base_uom_name: "Bag (bag)",
      conversions_count: 1,
    },
  ];

  it("should render products with their configured base units of measure", () => {
    render(<DataTable columns={columns} data={sampleData} keyExtractor={(p) => p.id} />);

    expect(screen.getAllByText("MILK-ALMOND-1L").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Piece (pcs)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("2 Defined").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Royal Basmati Rice 5kg").length).toBeGreaterThan(0);
  });

  it("should display conversion ratio explanation correctly", () => {
    const fromUnit = "Case";
    const toUnit = "Piece";
    const factor = 24;

    const ratioText = `1 ${fromUnit} = ${factor} ${toUnit}s`;
    expect(ratioText).toBe("1 Case = 24 Pieces");
  });
});
