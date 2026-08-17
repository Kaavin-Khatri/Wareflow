import { describe, expect, it } from "vitest";
import { ACCENT_SWATCHES, ACCENT_LIST } from "../theme-accents";

describe("Theme Accent Customization System", () => {
  it("provides 7 curated, pre-tested accent swatches", () => {
    expect(ACCENT_LIST).toHaveLength(7);
    const ids = ACCENT_LIST.map((s) => s.id);
    expect(ids).toContain("violet");
    expect(ids).toContain("indigo");
    expect(ids).toContain("emerald");
    expect(ids).toContain("cyan");
    expect(ids).toContain("rose");
    expect(ids).toContain("amber");
    expect(ids).toContain("cobalt");
  });

  it("ensures default accent is Electric Violet", () => {
    const defaultSwatch = ACCENT_SWATCHES.violet;
    expect(defaultSwatch.name).toBe("Electric Violet");
    expect(defaultSwatch.sampleHex).toBe("#7C3AED");
  });

  it("verifies every swatch defines complete token sets for both light and dark modes", () => {
    ACCENT_LIST.forEach((swatch) => {
      // Light Mode Tokens
      expect(swatch.light.accent).toBeDefined();
      expect(swatch.light.hover).toBeDefined();
      expect(swatch.light.subtle).toBeDefined();
      expect(swatch.light.border).toBeDefined();
      expect(swatch.light.glow).toBeDefined();

      // Dark Mode Tokens (Lifted luminance)
      expect(swatch.dark.accent).toBeDefined();
      expect(swatch.dark.hover).toBeDefined();
      expect(swatch.dark.subtle).toBeDefined();
      expect(swatch.dark.border).toBeDefined();
      expect(swatch.dark.glow).toBeDefined();

      // WCAG Compliance
      expect(swatch.wcagLightContrast).toContain("AA");
      expect(swatch.wcagDarkContrast).toContain("AA");
    });
  });
});
