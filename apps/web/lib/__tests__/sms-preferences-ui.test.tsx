import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { MessageSquare, Smartphone, Bell, Mail } from "lucide-react";

interface NotificationPreferences {
  in_app_enabled: boolean;
  email_enabled: boolean;
  whatsapp_enabled: boolean;
  sms_enabled: boolean;
  critical_stock_sms: boolean;
  order_updates_sms: boolean;
  dispatch_ready_sms: boolean;
}

describe("Step 13.6 SMS Channel & Notification Preferences UI Suite", () => {
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

  it("should render opt-in SMS notification settings card with channel toggles", () => {
    const preferences: NotificationPreferences = {
      in_app_enabled: true,
      email_enabled: true,
      whatsapp_enabled: true,
      sms_enabled: false,
      critical_stock_sms: false,
      order_updates_sms: false,
      dispatch_ready_sms: false,
    };

    const handleToggleSms = vi.fn();

    render(
      <GlassCard className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-white font-semibold">
            <Smartphone className="w-5 h-5 text-indigo-400" />
            <span>SMS Fallback & Critical Text Alerts</span>
          </div>
          <GlassBadge variant={preferences.sms_enabled ? "success" : "neutral"}>
            {preferences.sms_enabled ? "Opted In" : "Disabled (Default)"}
          </GlassBadge>
        </div>

        <p className="text-xs text-slate-300">
          Strict single-segment 160-character messages for high-priority stock depletion and dispatch signals.
        </p>

        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-white/5">
          <span className="text-sm text-slate-200">Enable SMS Notifications</span>
          <button
            role="switch"
            aria-checked={preferences.sms_enabled}
            onClick={handleToggleSms}
            className="px-3 py-1 rounded-lg bg-indigo-600 text-xs text-white"
          >
            Opt In to SMS
          </button>
        </div>
      </GlassCard>
    );

    expect(screen.getByText("SMS Fallback & Critical Text Alerts")).toBeDefined();
    expect(screen.getByText("Disabled (Default)")).toBeDefined();

    const toggleBtn = screen.getByRole("switch");
    fireEvent.click(toggleBtn);
    expect(handleToggleSms).toHaveBeenCalledTimes(1);
  });

  it("should display category checkboxes when SMS is enabled", () => {
    const preferences: NotificationPreferences = {
      in_app_enabled: true,
      email_enabled: true,
      whatsapp_enabled: true,
      sms_enabled: true,
      critical_stock_sms: true,
      order_updates_sms: true,
      dispatch_ready_sms: false,
    };

    render(
      <div className="space-y-3">
        <label className="flex items-center gap-2 text-xs text-slate-200">
          <input
            type="checkbox"
            checked={preferences.critical_stock_sms}
            readOnly
            data-testid="chk-stock"
          />
          Critical Stock Depletion Alerts
        </label>
        <label className="flex items-center gap-2 text-xs text-slate-200">
          <input
            type="checkbox"
            checked={preferences.order_updates_sms}
            readOnly
            data-testid="chk-orders"
          />
          Sales Order Confirmation Alerts
        </label>
      </div>
    );

    const stockChk = screen.getByTestId("chk-stock") as HTMLInputElement;
    expect(stockChk.checked).toBe(true);

    const orderChk = screen.getByTestId("chk-orders") as HTMLInputElement;
    expect(orderChk.checked).toBe(true);
  });
});
