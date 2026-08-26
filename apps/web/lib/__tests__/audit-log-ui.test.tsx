import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import AdminAuditLogPage from "@/app/admin/audit/page";
import { apiClient } from "@/lib/api-client";
import { ThemeProvider } from "@/components/ThemeProvider";

// Mock Next Navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/audit",
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
  }),
}));

// Mock API client
vi.mock("@/lib/api-client", () => ({
  getAuthToken: async () => "mock_token",
  setTwoFactorVerified: vi.fn(),
  isTwoFactorVerified: vi.fn().mockReturnValue(true),
  apiClient: {
    get: vi.fn(),
  },
}));

describe("Admin Action Audit Log UI Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
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

  it("should render audit log page header, timeline items, and diff inspection modal", async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      items: [
        {
          id: "log-1",
          actor_id: "u-1",
          actor_email: "admin@wareflow.internal",
          actor_name: "Admin User",
          action: "update_product_price",
          entity_type: "product",
          entity_id: "prod-101",
          description: "Updated wholesale tier pricing for SKU-PROD-101",
          before_value: { wholesale_price: 150 },
          after_value: { wholesale_price: 175 },
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
      page: 1,
      page_size: 25,
      total_pages: 1,
    });

    await act(async () => {
      render(
        <ThemeProvider>
          <AdminAuditLogPage />
        </ThemeProvider>,
      );
    });

    expect(screen.getByText("General Admin Action Audit Log")).toBeDefined();
    expect(screen.getByText("Updated wholesale tier pricing for SKU-PROD-101")).toBeDefined();
    expect(screen.getByText("Inspect Diff")).toBeDefined();

    // Open Diff Modal
    const inspectBtn = screen.getByText("Inspect Diff");
    await act(async () => {
      fireEvent.click(inspectBtn);
    });

    expect(screen.getByText("Audit Event Details")).toBeDefined();
    expect(screen.getByText("Before State")).toBeDefined();
    expect(screen.getByText("After State")).toBeDefined();
  });

  it("should render 2FA challenge banner when 403 two-factor error is returned", async () => {
    vi.mocked(apiClient.get).mockRejectedValueOnce(
      new Error("API Error 403: Two-factor authentication required for sensitive operations."),
    );

    await act(async () => {
      render(
        <ThemeProvider>
          <AdminAuditLogPage />
        </ThemeProvider>,
      );
    });

    expect(screen.getByText("Two-Factor Authentication Required")).toBeDefined();
    expect(screen.getByText("Verify 2FA Now")).toBeDefined();

    // Click Verify 2FA Now should emit wareflow:2fa-required
    const eventSpy = vi.spyOn(window, "dispatchEvent");
    const verifyBtn = screen.getByText("Verify 2FA Now");
    await act(async () => {
      fireEvent.click(verifyBtn);
    });

    expect(eventSpy).toHaveBeenCalled();
  });
});
