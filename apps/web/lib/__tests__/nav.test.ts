import { describe, expect, it } from "vitest";
import { filterNavSections, NAVIGATION_SECTIONS } from "../nav";

describe("Dynamic Navigation & RBAC Filtering", () => {
  it("Owner role can see all navigation sections and items", () => {
    const visible = filterNavSections(NAVIGATION_SECTIONS, [], "Owner");
    expect(visible.length).toBe(NAVIGATION_SECTIONS.length);
    const allItemsCount = visible.reduce((sum, s) => sum + s.items.length, 0);
    const originalCount = NAVIGATION_SECTIONS.reduce((sum, s) => sum + s.items.length, 0);
    expect(allItemsCount).toBe(originalCount);
  });

  it("Warehouse Staff only sees Dashboard and permitted Inventory/Orders items", () => {
    const warehousePerms = ["inventory:view", "orders:view"];
    const visible = filterNavSections(NAVIGATION_SECTIONS, warehousePerms, "Warehouse Staff");

    // Organization & Admin section and Finance & Billing section should be omitted
    const sectionTitles = visible.map((s) => s.title);
    expect(sectionTitles).toContain("Overview");
    expect(sectionTitles).toContain("Inventory & Catalog");
    expect(sectionTitles).toContain("Sales & CRM");
    expect(sectionTitles).not.toContain("Organization & Admin");
    expect(sectionTitles).not.toContain("Finance & Billing");

    // Inside Inventory & Catalog, Inventory & Stock appears
    const invSection = visible.find((s) => s.title === "Inventory & Catalog");
    const invItems = invSection?.items.map((i) => i.name);
    expect(invItems).toContain("Inventory & Stock");

    // Inside Sales & CRM, Orders & Dispatch appears
    const salesSection = visible.find((s) => s.title === "Sales & CRM");
    const salesItems = salesSection?.items.map((i) => i.name);
    expect(salesItems).toContain("Orders & Dispatch");
  });

  it("User with zero permissions only sees the public Dashboard", () => {
    const visible = filterNavSections(NAVIGATION_SECTIONS, [], "Guest Staff");
    expect(visible.length).toBe(1);
    expect(visible[0].title).toBe("Overview");
    expect(visible[0].items[0].name).toBe("Dashboard");
  });
});
