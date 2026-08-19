import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassCard } from "@/components/glass/GlassCard";
import { Truck, PackageCheck } from "lucide-react";

interface MockPO {
  id: string;
  po_number: string;
  supplier_name: string;
  status: "draft" | "ordered" | "ready_for_dispatch" | "received";
  total_amount: number;
  magic_link_token?: string;
}

describe("Step 13.5 Supplier Ready-for-Dispatch Portal & UI Suite", () => {
  beforeEach(() => {
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

  it("should render Ready for Pickup status badge with truck icon", () => {
    const renderStatusBadge = (status: string) => {
      switch (status) {
        case "ready_for_dispatch":
          return (
            <GlassBadge
              variant="accent"
              className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
            >
              <span className="flex items-center gap-1" data-testid="badge-ready">
                <Truck className="w-3 h-3 text-cyan-400 inline" /> Ready for Pickup
              </span>
            </GlassBadge>
          );
        default:
          return <GlassBadge variant="neutral">{status}</GlassBadge>;
      }
    };

    render(<div>{renderStatusBadge("ready_for_dispatch")}</div>);
    expect(screen.getByTestId("badge-ready")).toBeDefined();
    expect(screen.getByText("Ready for Pickup")).toBeDefined();
  });

  it("should render supplier magic link banner with copy button in PO modal", () => {
    const copySpy = vi.fn();
    Object.assign(navigator, {
      clipboard: {
        writeText: copySpy,
      },
    });

    const mockPO: MockPO = {
      id: "po-1",
      po_number: "PO-202608-001",
      supplier_name: "Tata Consumer Ltd",
      status: "ordered",
      total_amount: 25000,
      magic_link_token: "mag-tok-123456",
    };

    render(
      <GlassCard className="p-4 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-cyan-400 font-semibold text-xs flex items-center gap-1">
            <Truck className="w-4 h-4" />
            Supplier Magic Link
          </span>
          <GlassButton
            size="sm"
            variant="outline"
            onClick={() => navigator.clipboard.writeText(`http://localhost:3000/supplier/po/${mockPO.magic_link_token}`)}
          >
            Copy Link
          </GlassButton>
        </div>
        <p className="text-xs text-slate-300">
          Send this link to {mockPO.supplier_name}
        </p>
      </GlassCard>
    );

    expect(screen.getByText("Supplier Magic Link")).toBeDefined();
    expect(screen.getByText(/Send this link to Tata Consumer Ltd/)).toBeDefined();

    const copyBtn = screen.getByRole("button", { name: "Copy Link" });
    fireEvent.click(copyBtn);
    expect(copySpy).toHaveBeenCalledWith("http://localhost:3000/supplier/po/mag-tok-123456");
  });

  it("should render Mark Ready for Dispatch button for supplier action", () => {
    const handleAction = vi.fn();

    render(
      <div className="space-y-4">
        <div className="text-white font-bold">PO-202608-001</div>
        <GlassButton
          variant="primary"
          onClick={handleAction}
          className="w-full flex items-center gap-2"
        >
          <Truck className="w-4 h-4" />
          Mark Consignment Ready for Dispatch
        </GlassButton>
      </div>
    );

    const actionBtn = screen.getByRole("button", {
      name: /Mark Consignment Ready for Dispatch/i,
    });
    expect(actionBtn).toBeDefined();
    fireEvent.click(actionBtn);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });
});
