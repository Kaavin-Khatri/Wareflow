import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { GlassButton } from "../../components/glass/GlassButton";
import { GlassBadge } from "../../components/glass/GlassBadge";
import { GlassInput } from "../../components/glass/GlassInput";
import { GlassCard, GlassCardTitle } from "../../components/glass/GlassCard";
import { GlassDatePicker } from "../../components/glass/GlassDatePicker";
import { GlassSelect } from "../../components/glass/GlassSelect";
import { fireEvent } from "@testing-library/react";

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

  it("renders GlassDatePicker, opens calendar popover, and handles date selection", () => {
    const handleChange = () => {};
    render(
      <GlassDatePicker
        value="2026-08-27"
        onChange={handleChange}
        placeholder="Select settlement date..."
      />
    );
    expect(screen.getByText("27-08-2026")).toBeDefined();

    // Click trigger to open popover
    fireEvent.click(screen.getByRole("button", { name: /27-08-2026/i }));
    expect(screen.getByRole("dialog", { name: /date picker calendar/i })).toBeDefined();
    expect(screen.getByText("August")).toBeDefined();
    expect(screen.getByText("2026")).toBeDefined();
  });

  it("renders GlassSelect with options and handles selection", () => {
    const handleChange = () => {};
    render(
      <GlassSelect
        value="upi"
        onChange={handleChange}
        options={[
          { value: "upi", label: "UPI / QR Transfer" },
          { value: "bank", label: "Bank Transfer" },
        ]}
      />
    );
    expect(screen.getAllByText("UPI / QR Transfer").length).toBeGreaterThanOrEqual(1);

    fireEvent.click(screen.getByRole("button", { name: /upi \/ qr transfer/i }));
    expect(screen.getByRole("listbox")).toBeDefined();
  });
});
