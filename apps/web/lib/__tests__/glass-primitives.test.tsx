import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { GlassButton } from "../../components/glass/GlassButton";
import { GlassBadge } from "../../components/glass/GlassBadge";
import { GlassInput } from "../../components/glass/GlassInput";
import { GlassCard, GlassCardTitle } from "../../components/glass/GlassCard";

describe("Glass Component Primitives", () => {
  it("renders GlassButton with primary variant and specular sheen", () => {
    render(<GlassButton variant="primary">Submit Order</GlassButton>);
    const button = screen.getByRole("button", { name: /submit order/i });
    expect(button).toBeDefined();
    expect(button.className).toContain("from-[var(--accent)]");
  });

  it("renders GlassButton with secondary variant and glass tokens", () => {
    render(<GlassButton variant="secondary">Cancel</GlassButton>);
    const button = screen.getByRole("button", { name: /cancel/i });
    expect(button.className).toContain("bg-[var(--glass-bg)]");
  });

  it("renders GlassBadge with status variants and dot", () => {
    render(
      <GlassBadge variant="success" dot>
        In Stock
      </GlassBadge>,
    );
    const badge = screen.getByText("In Stock");
    expect(badge).toBeDefined();
    expect(badge.className).toContain("text-emerald-400");
  });

  it("renders GlassInput with placeholder and value", () => {
    render(<GlassInput placeholder="Search SKU..." defaultValue="BASMATI-01" />);
    const input = screen.getByPlaceholderText("Search SKU...");
    expect(input).toBeDefined();
    expect((input as HTMLInputElement).value).toBe("BASMATI-01");
  });

  it("renders GlassCard with title and hoverable properties", () => {
    render(
      <GlassCard hoverable glow>
        <GlassCardTitle>Batch FIFO</GlassCardTitle>
      </GlassCard>,
    );
    const title = screen.getByText("Batch FIFO");
    expect(title).toBeDefined();
  });
});
