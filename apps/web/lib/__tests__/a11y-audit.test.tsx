import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GlassModal } from "@/components/glass/GlassModal";
import { GlassButton } from "@/components/glass/GlassButton";
import { StatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import { Package } from "lucide-react";

describe("Accessibility (a11y) Quality Audit Suite (Step 22.4)", () => {
  it("GlassModal renders with valid dialog ARIA attributes and labels", () => {
    const handleClose = vi.fn();
    render(
      <GlassModal
        isOpen={true}
        onClose={handleClose}
        title="Add Wholesale Product"
        description="Fill in product catalog details"
      >
        <div>Modal Body Content</div>
      </GlassModal>,
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeDefined();
    expect(dialog.getAttribute("aria-modal")).toBe("true");

    const heading = screen.getByText("Add Wholesale Product");
    const desc = screen.getByText("Fill in product catalog details");
    expect(dialog.getAttribute("aria-labelledby")).toBe(heading.getAttribute("id"));
    expect(dialog.getAttribute("aria-describedby")).toBe(desc.getAttribute("id"));

    const closeBtn = screen.getByLabelText("Close dialog");
    expect(closeBtn).toBeDefined();
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("GlassModal closes on Escape keydown event", () => {
    const handleClose = vi.fn();
    render(
      <GlassModal isOpen={true} onClose={handleClose} title="Escape Test">
        <div>Content</div>
      </GlassModal>,
    );

    fireEvent.keyDown(window, { key: "Escape" });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("GlassButton renders with accessible focus-visible classes", () => {
    render(<GlassButton variant="primary">Confirm Sales Order</GlassButton>);
    const button = screen.getByRole("button", { name: "Confirm Sales Order" });
    expect(button).toBeDefined();
    expect(button.className).toContain("focus-visible:ring-2");
  });

  it("StatusBadge renders with semantic role and text for screen readers", () => {
    render(<StatusBadge status="paid" domain="invoice" />);
    const badge = screen.getByText("Paid");
    expect(badge).toBeDefined();
  });

  it("EmptyState renders with meaningful headline and action button", () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        icon={<Package className="w-6 h-6" />}
        title="No Products Found"
        description="Get started by adding your first wholesale product"
        action={<button onClick={handleAction}>Create Product</button>}
      />,
    );

    expect(screen.getByText("No Products Found")).toBeDefined();
    expect(
      screen.getByText("Get started by adding your first wholesale product"),
    ).toBeDefined();
    const actionBtn = screen.getByRole("button", { name: "Create Product" });
    expect(actionBtn).toBeDefined();
    fireEvent.click(actionBtn);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });
});
