import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { Hero3DFallback } from "@/components/marketing/Hero3DFallback";
import { HeroScene } from "@/components/marketing/HeroScene";
import { BentoGrid } from "@/components/marketing/BentoGrid";
import { MarketingNav } from "@/components/marketing/MarketingNav";
import { MarketingFooter } from "@/components/marketing/MarketingFooter";
import { ThemeProvider } from "@/components/ThemeProvider";

// Mock GSAP to prevent canvas/DOM errors in jsdom
vi.mock("gsap", () => ({
  gsap: {
    registerPlugin: vi.fn(),
    context: vi.fn((fn: () => void) => {
      fn();
      return { revert: vi.fn() };
    }),
    from: vi.fn(),
  },
}));

vi.mock("gsap/ScrollTrigger", () => ({
  ScrollTrigger: {},
}));

describe("Marketing Landing Page Suite", () => {
  beforeEach(() => {
    // Default matchMedia mock
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

  it("should render Hero3DFallback with accessible aria label and status indicator", () => {
    render(<Hero3DFallback />);
    expect(screen.getByLabelText("Abstract Wholesale Inventory 3D Illustration")).toBeDefined();
    expect(screen.getByText("Real-Time Node Telemetry Active")).toBeDefined();
  });

  it("should render fallback in HeroScene when prefers-reduced-motion is active", () => {
    window.matchMedia = vi.fn().mockImplementation((query) => ({
      matches: query === "(prefers-reduced-motion: reduce)",
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<HeroScene />);
    expect(screen.getByLabelText("Abstract Wholesale Inventory 3D Illustration")).toBeDefined();
  });

  it("should render all 5 core bento-grid feature cells", () => {
    render(<BentoGrid />);
    expect(screen.getByText("Predictive Reordering & Low-Stock Alerts")).toBeDefined();
    expect(screen.getByText("Seasonal Demand Forecast")).toBeDefined();
    expect(screen.getByText("WhatsApp B2B Dispatches")).toBeDefined();
    expect(screen.getByText("GST & FSSAI Guardrails")).toBeDefined();
    expect(screen.getByText("APMC Wholesale Map")).toBeDefined();
  });

  it("should render MarketingNav with brand logo and Enter Workspace CTA link", () => {
    render(
      <ThemeProvider>
        <MarketingNav />
      </ThemeProvider>,
    );
    expect(screen.getByText("WareFlow")).toBeDefined();
    const loginLink = screen.getByRole("link", { name: /Enter Workspace/i });
    expect(loginLink.getAttribute("href")).toBe("/login");
  });

  it("should render MarketingFooter with links and copyright telemetry", () => {
    render(<MarketingFooter />);
    expect(screen.getByText("WareFlow ERP")).toBeDefined();
    expect(screen.getByRole("link", { name: /Sign In/i }).getAttribute("href")).toBe("/login");
  });
});
