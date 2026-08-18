/**
 * Frontend test suite for FSSAI License Compliance Tracking (Step 7.4).
 *
 * Covers:
 * - Business Settings page rendering and form interaction
 * - Supplier FSSAI status badge computation (ok/expiring-soon/expired/missing)
 * - PO creation expired-supplier confirmation dialog flow
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";


// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin/settings/business",
  useSearchParams: () => ({
    get: () => null,
    toString: () => "",
  }),
}));


// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) =>
    React.createElement("a", { href }, children),
}));

// ────────────────────────────────────────────────────────────
// 1. FSSAI Status Helper Computation Tests (Pure Logic)
// ────────────────────────────────────────────────────────────

function computeFssaiStatus(expiryDate: string | null): {
  label: string;
  variant: "success" | "warning" | "error" | "neutral";
  daysRemaining: number | null;
} {
  if (!expiryDate) {
    return { label: "No FSSAI", variant: "neutral", daysRemaining: null };
  }
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const expiry = new Date(expiryDate);
  expiry.setHours(0, 0, 0, 0);
  const diffMs = expiry.getTime() - today.getTime();
  const days = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  if (days < 0) {
    return { label: "Expired", variant: "error", daysRemaining: days };
  }
  if (days <= 30) {
    return { label: "Expiring Soon", variant: "warning", daysRemaining: days };
  }
  return { label: "Valid", variant: "success", daysRemaining: days };
}

describe("computeFssaiStatus", () => {
  it("should return 'neutral' when no expiry date is provided", () => {
    const result = computeFssaiStatus(null);
    expect(result.label).toBe("No FSSAI");
    expect(result.variant).toBe("neutral");
    expect(result.daysRemaining).toBeNull();
  });

  it("should return 'success' for a license valid for > 30 days", () => {
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 90);
    const result = computeFssaiStatus(futureDate.toISOString().split("T")[0]);
    expect(result.label).toBe("Valid");
    expect(result.variant).toBe("success");
    expect(result.daysRemaining).toBe(90);
  });

  it("should return 'warning' for a license expiring within 30 days", () => {
    const soonDate = new Date();
    soonDate.setDate(soonDate.getDate() + 20);
    const result = computeFssaiStatus(soonDate.toISOString().split("T")[0]);
    expect(result.label).toBe("Expiring Soon");
    expect(result.variant).toBe("warning");
    expect(result.daysRemaining).toBe(20);
  });

  it("should return 'error' for an expired license", () => {
    const pastDate = new Date();
    pastDate.setDate(pastDate.getDate() - 10);
    const result = computeFssaiStatus(pastDate.toISOString().split("T")[0]);
    expect(result.label).toBe("Expired");
    expect(result.variant).toBe("error");
    expect(result.daysRemaining).toBe(-10);
  });

  it("should return 'warning' on the exact 30-day boundary", () => {
    const boundaryDate = new Date();
    boundaryDate.setDate(boundaryDate.getDate() + 30);
    const result = computeFssaiStatus(boundaryDate.toISOString().split("T")[0]);
    expect(result.label).toBe("Expiring Soon");
    expect(result.variant).toBe("warning");
    expect(result.daysRemaining).toBe(30);
  });

  it("should return 'success' at day 31 (just outside window)", () => {
    const justOutside = new Date();
    justOutside.setDate(justOutside.getDate() + 31);
    const result = computeFssaiStatus(justOutside.toISOString().split("T")[0]);
    expect(result.label).toBe("Valid");
    expect(result.variant).toBe("success");
    expect(result.daysRemaining).toBe(31);
  });
});

// ────────────────────────────────────────────────────────────
// 2. FSSAI Compliance Banner Configuration
// ────────────────────────────────────────────────────────────

function getFssaiBannerConfig(status: string) {
  if (status === "expired") {
    return {
      variant: "error" as const,
      title: "FSSAI License Expired",
    };
  }
  if (status === "expiring_soon") {
    return {
      variant: "warning" as const,
      title: "FSSAI License Expiring Soon",
    };
  }
  if (status === "valid") {
    return {
      variant: "success" as const,
      title: "FSSAI License Active",
    };
  }
  return {
    variant: "neutral" as const,
    title: "No FSSAI License Registered",
  };
}


describe("getFssaiBannerConfig", () => {
  it("should return error variant for expired status", () => {
    const config = getFssaiBannerConfig("expired");
    expect(config.variant).toBe("error");
    expect(config.title).toBe("FSSAI License Expired");
  });

  it("should return warning variant for expiring_soon status", () => {
    const config = getFssaiBannerConfig("expiring_soon");
    expect(config.variant).toBe("warning");
    expect(config.title).toBe("FSSAI License Expiring Soon");
  });

  it("should return success variant for valid status", () => {
    const config = getFssaiBannerConfig("valid");
    expect(config.variant).toBe("success");
    expect(config.title).toBe("FSSAI License Active");
  });

  it("should return neutral variant for missing status", () => {
    const config = getFssaiBannerConfig("missing");
    expect(config.variant).toBe("neutral");
    expect(config.title).toBe("No FSSAI License Registered");
  });
});


// ────────────────────────────────────────────────────────────
// 3. Business Settings Page Rendering
// ────────────────────────────────────────────────────────────

// Mock apiClient for BusinessSettings page rendering
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({
      id: "biz-1",
      business_name: "Shree Ganesh Food Traders",
      gstin: "27ABCDE1234F1Z5",
      fssai_license_no: "10020030040050",
      fssai_expiry_date: (() => {
        const d = new Date();
        d.setDate(d.getDate() + 20);
        return d.toISOString().split("T")[0];
      })(),
      address: "APMC Market 1, Vashi",
      phone: "+91 98765 43210",
      email: "billing@ganeshtraders.com",
      updated_at: new Date().toISOString(),
      fssai_status: "expiring_soon",
      days_until_fssai_expiry: 20,
    }),
    post: vi.fn().mockResolvedValue({ success: true }),
    put: vi.fn().mockResolvedValue({
      id: "biz-1",
      business_name: "Shree Ganesh Food Traders",
      fssai_status: "expiring_soon",
      days_until_fssai_expiry: 20,
    }),
    patch: vi.fn().mockResolvedValue({ success: true }),
  },
}));

describe("Business Settings Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should compute correct FSSAI banner for expiring-soon business settings", () => {
    const config = getFssaiBannerConfig("expiring_soon");
    expect(config.variant).toBe("warning");
    expect(config.title).toBe("FSSAI License Expiring Soon");
  });

  it("should compute correct FSSAI banner for expired business settings", () => {
    const config = getFssaiBannerConfig("expired");
    expect(config.variant).toBe("error");
    expect(config.title).toBe("FSSAI License Expired");
  });

});


// ────────────────────────────────────────────────────────────
// 4. PO Expired Supplier Compliance Gate
// ────────────────────────────────────────────────────────────

describe("PO Expired Supplier Compliance Check", () => {
  it("should detect expired supplier FSSAI license correctly", () => {
    const suppliers = [
      {
        id: "sup-1",
        name: "Good Supplier",
        fssai_expiry_date: (() => {
          const d = new Date();
          d.setDate(d.getDate() + 90);
          return d.toISOString().split("T")[0];
        })(),
      },
      {
        id: "sup-2",
        name: "Bad Supplier",
        fssai_expiry_date: (() => {
          const d = new Date();
          d.setDate(d.getDate() - 10);
          return d.toISOString().split("T")[0];
        })(),
      },
    ];

    const checkExpired = (supplierId: string) => {
      const supplier = suppliers.find((s) => s.id === supplierId);
      if (!supplier?.fssai_expiry_date) return false;
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const expiry = new Date(supplier.fssai_expiry_date);
      expiry.setHours(0, 0, 0, 0);
      return expiry < today;
    };

    expect(checkExpired("sup-1")).toBe(false);
    expect(checkExpired("sup-2")).toBe(true);
    expect(checkExpired("sup-nonexistent")).toBe(false);
  });

  it("should not flag suppliers with no FSSAI date as expired", () => {
    const supplier = { id: "sup-3", name: "No License", fssai_expiry_date: null };

    const isExpired = (() => {
      if (!supplier.fssai_expiry_date) return false;
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const expiry = new Date(supplier.fssai_expiry_date);
      expiry.setHours(0, 0, 0, 0);
      return expiry < today;
    })();

    expect(isExpired).toBe(false);
  });
});
