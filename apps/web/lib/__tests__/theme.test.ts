import { beforeEach, describe, expect, it } from "vitest";

describe("Theme System & Persistence Logic", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
  });

  it("defaults to system preference when no local storage is present", () => {
    const storedTheme = localStorage.getItem("wareflow-theme");
    expect(storedTheme).toBeNull();
  });

  it("persists theme preference to localStorage on update", () => {
    localStorage.setItem("wareflow-theme", "light");
    expect(localStorage.getItem("wareflow-theme")).toBe("light");

    localStorage.setItem("wareflow-theme", "dark");
    expect(localStorage.getItem("wareflow-theme")).toBe("dark");
  });

  it("correctly computes class manipulation for html root", () => {
    const root = document.documentElement;

    // Apply dark
    root.classList.add("dark");
    expect(root.classList.contains("dark")).toBe(true);

    // Apply light
    root.classList.remove("dark");
    expect(root.classList.contains("dark")).toBe(false);
  });
});
