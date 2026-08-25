import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { CustomCursor } from "@/components/motion/CustomCursor";
import { SkeletonCatalogGrid, SkeletonTable, SkeletonCard } from "@/components/SkeletonPrimitives";
import { StaggerContainer, StaggerItem, FadeIn, ScaleOnHover } from "@/components/motion/GlassMotion";

describe("Motion Layer & Interaction Choreography", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("CustomCursor treatment", () => {
    it("renders custom cursor on desktop fine pointer devices", () => {
      // Mock matchMedia for fine desktop pointer
      window.matchMedia = vi.fn().mockImplementation((query: string) => {
        if (query === "(hover: hover) and (pointer: fine)") {
          return { matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() };
        }
        if (query === "(prefers-reduced-motion: reduce)") {
          return { matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() };
        }
        return { matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() };
      });

      render(<CustomCursor />);
      expect(screen.getByTestId("custom-cursor")).toBeDefined();
    });

    it("does NOT render custom cursor on touch/mobile devices", () => {
      // Mock matchMedia returning false for fine pointer (touch device)
      window.matchMedia = vi.fn().mockImplementation((query: string) => {
        if (query === "(hover: hover) and (pointer: fine)") {
          return { matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() };
        }
        return { matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() };
      });

      render(<CustomCursor />);
      expect(screen.queryByTestId("custom-cursor")).toBeNull();
    });

    it("does NOT render custom cursor when prefers-reduced-motion is true", () => {
      window.matchMedia = vi.fn().mockImplementation((query: string) => {
        if (query === "(hover: hover) and (pointer: fine)") {
          return { matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() };
        }
        if (query === "(prefers-reduced-motion: reduce)") {
          return { matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() };
        }
        return { matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() };
      });

      render(<CustomCursor />);
      expect(screen.queryByTestId("custom-cursor")).toBeNull();
    });
  });

  describe("Loading Skeletons", () => {
    it("renders SkeletonCatalogGrid with 4 item placeholders", () => {
      const { container } = render(<SkeletonCatalogGrid count={4} />);
      const cards = container.querySelectorAll(".p-5.rounded-3xl");
      expect(cards.length).toBe(4);
    });

    it("renders SkeletonTable with specified row and column counts", () => {
      const { container } = render(<SkeletonTable rows={3} cols={4} />);
      const rows = container.querySelectorAll(".divide-y > div");
      expect(rows.length).toBe(3);
    });

    it("renders SkeletonCard in kpi and detail variants", () => {
      const { container: kpiContainer } = render(<SkeletonCard variant="kpi" />);
      expect(kpiContainer.querySelector(".rounded-2xl")).not.toBeNull();

      const { container: detailContainer } = render(<SkeletonCard variant="detail" />);
      expect(detailContainer.querySelector(".space-y-4")).not.toBeNull();
    });
  });

  describe("Page-Load Motion Primitives", () => {
    it("renders StaggerContainer and StaggerItem children", () => {
      render(
        <StaggerContainer>
          <StaggerItem>
            <div data-testid="item-1">Card 1</div>
          </StaggerItem>
          <StaggerItem>
            <div data-testid="item-2">Card 2</div>
          </StaggerItem>
        </StaggerContainer>,
      );

      expect(screen.getByTestId("item-1")).toBeDefined();
      expect(screen.getByTestId("item-2")).toBeDefined();
    });

    it("renders FadeIn and ScaleOnHover containers", () => {
      render(
        <FadeIn>
          <ScaleOnHover>
            <button data-testid="spring-btn">Click Me</button>
          </ScaleOnHover>
        </FadeIn>,
      );

      expect(screen.getByTestId("spring-btn")).toBeDefined();
    });
  });
});
