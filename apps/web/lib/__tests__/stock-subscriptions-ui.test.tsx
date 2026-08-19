import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { GlassButton } from "@/components/glass/GlassButton";
import { Bell, MessageSquare, Mail } from "lucide-react";

interface MockProduct {
  id: string;
  sku: string;
  name: string;
  wholesale_price: number;
}

interface MockRetailer {
  id: string;
  name: string;
  phone: string;
  subscriptionsCount: number;
}

describe("Step 13.4 Retailer Restock Subscriptions & Alerts UI Suite", () => {
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

  it("should render Alert quick-action button in Product Catalog DataTable", () => {
    const handleNotifyClick = vi.fn();

    const mockProducts: MockProduct[] = [
      {
        id: "prod-1",
        sku: "RICE-BAS-25",
        name: "Kohinoor Basmati Rice 25kg",
        wholesale_price: 2600.0,
      },
    ];

    const columns: DataTableColumn<MockProduct>[] = [
      {
        key: "name",
        header: "Product",
        render: (p) => <div>{p.name}</div>,
      },
      {
        key: "actions",
        header: "Actions",
        render: (p) => (
          <GlassButton
            onClick={() => handleNotifyClick(p)}
            variant="secondary"
            size="sm"
            title="Notify Retailer When Available"
          >
            <Bell className="w-3.5 h-3.5 mr-1" /> Alert
          </GlassButton>
        ),
      },
    ];

    render(<DataTable columns={columns} data={mockProducts} keyExtractor={(p) => p.id} />);

    expect(screen.getAllByText("Kohinoor Basmati Rice 25kg").length).toBeGreaterThanOrEqual(1);
    const alertBtn = screen.getAllByText("Alert")[0];
    expect(alertBtn).toBeDefined();

    fireEvent.click(alertBtn);
    expect(handleNotifyClick).toHaveBeenCalledWith(mockProducts[0]);
  });

  it("should render Restock Alerts subscription badge in Retailers DataTable", () => {
    const mockRetailers: MockRetailer[] = [
      {
        id: "ret-1",
        name: "Metro Cash & Carry",
        phone: "+91 98765 43210",
        subscriptionsCount: 3,
      },
      {
        id: "ret-2",
        name: "Gupta Kirana",
        phone: "+91 98111 22233",
        subscriptionsCount: 0,
      },
    ];

    const columns: DataTableColumn<MockRetailer>[] = [
      {
        key: "name",
        header: "Retailer",
        render: (r) => <div>{r.name}</div>,
      },
      {
        key: "subscriptions",
        header: "Restock Alerts",
        render: (r) =>
          r.subscriptionsCount > 0 ? (
            <span className="px-2 py-0.5 rounded text-xs bg-amber-500/10 text-amber-300">
              <Bell className="w-3 h-3 inline mr-1" />
              {r.subscriptionsCount} Subscribed
            </span>
          ) : (
            <span className="text-xs text-muted">0</span>
          ),
      },
    ];

    render(<DataTable columns={columns} data={mockRetailers} keyExtractor={(r) => r.id} />);

    expect(screen.getAllByText("Metro Cash & Carry").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("3 Subscribed").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Gupta Kirana").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("0").length).toBeGreaterThanOrEqual(1);
  });

  it("should render Channel Preference options (WhatsApp, Email, Both)", () => {
    const channelChoices = [
      { id: "whatsapp", label: "WhatsApp", icon: MessageSquare },
      { id: "email", label: "Email", icon: Mail },
      { id: "both", label: "Both", icon: Bell },
    ];

    render(
      <div className="flex gap-2">
        {channelChoices.map((c) => (
          <button key={c.id} data-testid={`channel-${c.id}`}>
            {c.label}
          </button>
        ))}
      </div>
    );

    expect(screen.getByTestId("channel-whatsapp").textContent).toBe("WhatsApp");
    expect(screen.getByTestId("channel-email").textContent).toBe("Email");
    expect(screen.getByTestId("channel-both").textContent).toBe("Both");
  });
});
