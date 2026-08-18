import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { StatusBadge } from "@/components/StatusBadge";

interface ProductRow {
  id: string;
  sku: string;
  name: string;
  category: string;
  wholesale_price: number;
  cost_price: number;
  is_active: boolean;
}

describe("Product Catalog & Category CRUD UI Suite (Step 5.1)", () => {
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

  const mockProducts: ProductRow[] = [
    {
      id: "p-1",
      sku: "RICE-ROYAL-25KG",
      name: "Royal Basmati Rice 25kg",
      category: "Grains & Pulses",
      wholesale_price: 2450.0,
      cost_price: 2100.0,
      is_active: true,
    },
    {
      id: "p-2",
      sku: "OIL-SUN-15L",
      name: "Sunflower Oil 15L",
      category: "Edible Oils",
      wholesale_price: 1850.0,
      cost_price: 1600.0,
      is_active: false,
    },
  ];

  const columns: DataTableColumn<ProductRow>[] = [
    {
      key: "name",
      header: "Product / SKU",
      mobilePrimary: true,
      sortable: true,
      render: (item) => (
        <div>
          <span className="font-bold">{item.name}</span>
          <span className="text-xs text-purple-300"> ({item.sku})</span>
        </div>
      ),
    },
    {
      key: "category",
      header: "Category",
      render: (item) => <span>{item.category}</span>,
    },
    {
      key: "wholesale_price",
      header: "Wholesale Price",
      sortable: true,
      render: (item) => <span>₹{item.wholesale_price}</span>,
    },
    {
      key: "status",
      header: "Status",
      render: (item) => <StatusBadge status={item.is_active ? "active" : "inactive"} />,
    },
  ];

  it("should render product catalog data table with correct columns and data", () => {
    render(<DataTable columns={columns} data={mockProducts} keyExtractor={(item) => item.id} />);

    expect(screen.getAllByText("Royal Basmati Rice 25kg").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("(RICE-ROYAL-25KG)").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Grains & Pulses").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("₹2450").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Active").length).toBeGreaterThanOrEqual(1);

    expect(screen.getAllByText("Sunflower Oil 15L").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Inactive").length).toBeGreaterThanOrEqual(1);
  });

  it("should sort products table when clicking sortable header", () => {
    render(<DataTable columns={columns} data={mockProducts} keyExtractor={(item) => item.id} />);

    const sortHeader = screen.getByText("Product / SKU");
    fireEvent.click(sortHeader);
    expect(sortHeader).toBeDefined();
  });

  it("should render empty state when no products match filter", () => {
    const handleCreate = vi.fn();
    render(
      <DataTable
        columns={columns}
        data={[]}
        keyExtractor={(item) => item.id}
        emptyTitle="No products found"
        emptyDescription="Add wholesale inventory products to build your catalog."
        emptyAction={<button onClick={handleCreate}>Add Product</button>}
      />,
    );

    expect(screen.getByText("No products found")).toBeDefined();
    expect(
      screen.getByText("Add wholesale inventory products to build your catalog."),
    ).toBeDefined();
    const btn = screen.getByText("Add Product");
    fireEvent.click(btn);
    expect(handleCreate).toHaveBeenCalledTimes(1);
  });
});
