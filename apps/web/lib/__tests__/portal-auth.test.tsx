/**
 * Frontend Unit Tests for Retailer Portal Auth & Scoped Layout (Step 11.1).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import PortalLoginPage from "@/app/portal/login/page";
import PortalLayout from "@/app/portal/layout";

// Mock next/navigation
const mockPush = vi.fn();
let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, refresh: vi.fn() }),
  usePathname: () => "/portal/catalog",
  useSearchParams: () => mockSearchParams,
}));

// Mock firebase/auth
vi.mock("firebase/auth", () => ({
  signInWithEmailAndPassword: vi.fn(),
  createUserWithEmailAndPassword: vi.fn(),
  signInWithPopup: vi.fn(),
  onAuthStateChanged: vi.fn((auth, cb) => {
    cb({
      uid: "uid_ret_alice",
      email: "alice@alphamart.com",
      getIdToken: () => Promise.resolve("mock_id_token"),
    });
    return () => {};
  }),
  signOut: vi.fn(),
}));

vi.mock("@/lib/firebase-client", () => ({
  auth: {},
  googleProvider: {},
}));

describe("Retailer Portal Authentication & Scoped Shell (Step 11.1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams();
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "uid_ret_alice",
        email: "alice@alphamart.com",
        retailer_id: "ret-aaa",
        retailer_name: "Alpha Mart Wholesale",
        pricing_tier: "silver",
        credit_limit: 500000.0,
        credit_balance: 50000.0,
      }),
    });
  });

  it("renders Retailer Portal login page with mode switcher", () => {
    render(<PortalLoginPage />);

    expect(screen.getByRole("heading", { name: /Retailer Portal/i })).toBeDefined();
    expect(screen.getByRole("button", { name: /^Sign In$/i })).toBeDefined();
    expect(screen.getByRole("button", { name: /Accept Invite \/ Sign Up/i })).toBeDefined();
    expect(screen.getByPlaceholderText(/retailer@business.com/i)).toBeDefined();
  });

  it("switches to invitation acceptance mode and displays Invite Token input", async () => {
    render(<PortalLoginPage />);

    const signUpTab = screen.getByRole("button", { name: /Accept Invite \/ Sign Up/i });
    fireEvent.click(signUpTab);

    expect(screen.getByPlaceholderText(/e\.g\. inv_ab12cd34/i)).toBeDefined();
    expect(screen.getByRole("button", { name: /Complete Account Setup/i })).toBeDefined();
  });

  it("renders PortalLayout navbar with scoped retailer navigation links", async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: "uid_ret_alice",
        email: "alice@alphamart.com",
        retailer_id: "ret-aaa",
        retailer_name: "Alpha Mart Wholesale",
        pricing_tier: "silver",
        credit_limit: 500000.0,
        credit_balance: 50000.0,
      }),
    } as unknown as Response);

    render(
      <PortalLayout>
        <div data-testid="portal-content">Catalog View</div>
      </PortalLayout>
    );

    await waitFor(() => {
      expect(screen.getByText("Retailer Portal")).toBeDefined();
      expect(screen.getByText("Alpha Mart Wholesale")).toBeDefined();
      expect(screen.getByText("silver")).toBeDefined();
      expect(screen.getByRole("link", { name: /Catalog/i })).toBeDefined();
      expect(screen.getByRole("link", { name: /My Orders/i })).toBeDefined();
      expect(screen.getByRole("link", { name: /Invoices & Ledger/i })).toBeDefined();
      expect(screen.getByTestId("portal-content")).toBeDefined();
    });
  });
});
