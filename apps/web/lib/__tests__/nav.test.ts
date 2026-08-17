import { describe, expect, it } from "vitest";
import { filterNavSections, NAVIGATION_SECTIONS } from "../nav";

describe("Dynamic Navigation & RBAC Filtering", () => {
  it("Owner role can see all navigation sections and items", () => {
    const visible = filterNavSections(NAVIGATION_SECTIONS, [], "Owner");
    expect(visible.length).toBe(3);
    const allItemsCount = visible.reduce((sum, s) => sum + s.items.length, 0);
    const originalCount = NAVIGATION_SECTIONS.reduce((sum, s) => sum + s.items.length, 0);
    expect(allItemsCount).toBe(originalCount);
  });

  it("Warehouse Staff only sees Dashboard and permitted Inventory/Orders items", () => {
    const warehousePerms = ["inventory:view", "orders:view"];
    const visible = filterNavSections(NAVIGATION_SECTIONS, warehousePerms, "Warehouse Staff");

    // Organization & Admin section should be completely omitted because no admin perms are held
    const sectionTitles = visible.map((s) => s.title);
    expect(sectionTitles).toContain("Overview");
    expect(sectionTitles).toContain("Wholesale Operations");
    expect(sectionTitles).not.toContain("Organization & Admin");

    // Inside Wholesale Operations, GST Invoices (invoices:view) should not appear
    const opsSection = visible.find((s) => s.title === "Wholesale Operations");
    const itemNames = opsSection?.items.map((i) => i.name);
    expect(itemNames).toContain("Inventory & Stock");
    expect(itemNames).toContain("Orders & Dispatch");
    expect(itemNames).not.toContain("GST Invoices");
  });

  it("User with zero permissions only sees the public Dashboard", () => {
    const visible = filterNavSections(NAVIGATION_SECTIONS, [], "Guest Staff");
    expect(visible.length).toBe(1);
    expect(visible[0].title).toBe("Overview");
    expect(visible[0].items[0].name).toBe("Dashboard");
  });
});
