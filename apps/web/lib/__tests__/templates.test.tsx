import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  ListViewTemplate,
  DetailViewTemplate,
  FormTemplate,
  FormSection,
  DashboardTemplate,
} from "@/components/templates";
import { AnimeCheckIcon, AnimeMorphIcon, AnimeMicroPress } from "@/components/motion/AnimeMicro";

describe("Four Locked Page Templates Suite", () => {
  it("ListViewTemplate renders page header, search bar, filters, table, and pagination", () => {
    render(
      <ListViewTemplate
        title="Products Catalog"
        description="Wholesale inventory master list"
        searchQuery="Basmati"
        filters={<div>Category Filter</div>}
        pagination={<div>Pagination Slot</div>}
      >
        <div>Table Rows Data</div>
      </ListViewTemplate>,
    );

    expect(screen.getByText("Products Catalog")).toBeDefined();
    expect(screen.getByText("Wholesale inventory master list")).toBeDefined();
    expect(screen.getByText("Category Filter")).toBeDefined();
    expect(screen.getByText("Table Rows Data")).toBeDefined();
    expect(screen.getByText("Pagination Slot")).toBeDefined();
  });

  it("DetailViewTemplate renders 8-col main area and 4-col sticky side panel", () => {
    render(
      <DetailViewTemplate
        title="Purchase Order #PO-100"
        subtitle="Supplier: Royal Agro"
        backHref="/purchasing"
        backLabel="Back to POs"
        sidePanel={<div>Side Panel Coordinates</div>}
      >
        <div>Main Line Items 8-Col</div>
      </DetailViewTemplate>,
    );

    expect(screen.getByText("Purchase Order #PO-100")).toBeDefined();
    expect(screen.getByText("Supplier: Royal Agro")).toBeDefined();
    expect(screen.getByText("Back to POs")).toBeDefined();
    expect(screen.getByText("Main Line Items 8-Col")).toBeDefined();
    expect(screen.getByText("Side Panel Coordinates")).toBeDefined();
  });

  it("FormTemplate renders form sections and sticky bottom action bar", () => {
    render(
      <FormTemplate
        title="Create Product"
        description="Add a new SKU"
        backHref="/inventory"
        submitLabel="Save Product"
        isDirty={true}
      >
        <FormSection title="General Specs" description="SKU and HSN">
          <div>Input Field A</div>
        </FormSection>
      </FormTemplate>,
    );

    expect(screen.getByText("Create Product")).toBeDefined();
    expect(screen.getByText("General Specs")).toBeDefined();
    expect(screen.getByText("Input Field A")).toBeDefined();
    expect(screen.getByText("Unsaved changes")).toBeDefined();
    expect(screen.getByText("Save Product")).toBeDefined();
  });

  it("DashboardTemplate renders KPI row, main content, and side alerts", () => {
    render(
      <DashboardTemplate
        title="Executive Overview"
        kpiMetrics={[
          {
            id: "1",
            title: "Total Revenue",
            value: "₹50,00,000",
            change: "+12%",
            trend: "up",
          },
        ]}
        mainContent={<div>Chart Analytics</div>}
        sideContent={<div>Urgent Low Stock</div>}
      />,
    );

    expect(screen.getByText("Executive Overview")).toBeDefined();
    expect(screen.getByText("Total Revenue")).toBeDefined();
    expect(screen.getByText("₹50,00,000")).toBeDefined();
    expect(screen.getByText("Chart Analytics")).toBeDefined();
    expect(screen.getByText("Urgent Low Stock")).toBeDefined();
  });
});

describe("Anime.js Micro-Interaction Components", () => {
  it("renders AnimeCheckIcon, AnimeMorphIcon, and AnimeMicroPress without crashing", () => {
    const { container } = render(
      <div>
        <AnimeCheckIcon checked={true} />
        <AnimeMorphIcon active={false} />
        <AnimeMicroPress>
          <span>Press Button</span>
        </AnimeMicroPress>
      </div>,
    );

    expect(container.querySelector("svg")).toBeDefined();
    expect(screen.getByText("Press Button")).toBeDefined();
  });
});
