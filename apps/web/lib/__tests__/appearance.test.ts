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

import { BACKDROP_PRESETS, BACKDROP_LIST } from "../theme-backdrops";

describe("Atmospheric Backdrop Preset System", () => {
  it("provides 7 smooth, cozy, and relaxing atmospheric backdrop presets", () => {
    expect(BACKDROP_LIST).toHaveLength(7);
    const ids = BACKDROP_LIST.map((b) => b.id);
    expect(ids).toContain("midnight");
    expect(ids).toContain("cozy-amber");
    expect(ids).toContain("nordic-aurora");
    expect(ids).toContain("lavender-dusk");
    expect(ids).toContain("ocean-calm");
    expect(ids).toContain("warm-cafe");
    expect(ids).toContain("minimal-pure");
  });

  it("ensures every backdrop preset has defined dark and light orb gradient configurations", () => {
    BACKDROP_LIST.forEach((preset) => {
      expect(preset.name).toBeDefined();
      expect(preset.moodTag).toBeDefined();
      expect(preset.previewGradient).toBeDefined();
      expect(preset.darkOrbs.orb1).toBeDefined();
      expect(preset.darkOrbs.orb2).toBeDefined();
      expect(preset.darkOrbs.orb3).toBeDefined();
      expect(preset.darkOrbs.orb4).toBeDefined();
      expect(preset.lightOrbs.orb1).toBeDefined();
      expect(preset.lightOrbs.orb2).toBeDefined();
      expect(preset.lightOrbs.orb3).toBeDefined();
      expect(preset.lightOrbs.orb4).toBeDefined();
    });
  });

  it("ensures default backdrop is Midnight Aurora", () => {
    const defaultBackdrop = BACKDROP_PRESETS.midnight;
    expect(defaultBackdrop.name).toBe("Midnight Aurora");
    expect(defaultBackdrop.moodTag).toBe("Signature");
  });
});

import { WALLPAPER_PRESETS, WALLPAPER_LIST } from "../theme-backdrops";

describe("Cozy Environment and Nature Wallpaper System", () => {
  it("provides 6 curated wallpapers including cozy environments and tranquil nature", () => {
    expect(WALLPAPER_LIST).toHaveLength(6);
    const ids = WALLPAPER_LIST.map((w) => w.id);
    expect(ids).toContain("none");
    expect(ids).toContain("cozy-cabin");
    expect(ids).toContain("misty-forest");
    expect(ids).toContain("rainy-lofi");
    expect(ids).toContain("zen-garden");
    expect(ids).toContain("aurora-lake");
  });

  it("ensures all photo wallpapers specify valid image paths and descriptive categories", () => {
    WALLPAPER_LIST.forEach((wp) => {
      expect(wp.name).toBeDefined();
      expect(wp.category).toBeDefined();
      expect(wp.description).toBeDefined();
      if (wp.id !== "none") {
        expect(wp.imageSrc).toMatch(/^\/backgrounds\/.*\.jpg$/);
        expect(wp.defaultOverlayOpacity).toBeGreaterThan(0);
      }
    });
  });

  it("ensures default wallpaper is none (ambient atmosphere only)", () => {
    expect(WALLPAPER_PRESETS.none.name).toBe("None (Ambient Atmosphere Only)");
  });
});

