/**
 * Unit test suite for TwoFactorChallengeModal.
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { TwoFactorChallengeModal } from "@/components/TwoFactorChallengeModal";
import { isTwoFactorVerified } from "@/lib/api-client";

// Mock firebase client
vi.mock("@/lib/firebase-client", () => ({
  auth: {
    currentUser: {
      getIdToken: vi.fn().mockResolvedValue("mock-firebase-token"),
    },
    authStateReady: vi.fn().mockResolvedValue(true),
  },
}));

describe("TwoFactorChallengeModal", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("should initially be closed and not render modal content", () => {
    render(<TwoFactorChallengeModal />);
    expect(screen.queryByText("Two-Factor Verification Required")).toBeNull();
  });

  it("should open when 'wareflow:2fa-required' window event is triggered", async () => {
    render(<TwoFactorChallengeModal />);

    window.dispatchEvent(
      new CustomEvent("wareflow:2fa-required", {
        detail: { endpoint: "/categories" },
      })
    );

    expect(await screen.findByText("Two-Factor Verification Required")).toBeTruthy();
    expect(screen.getByText("Confirm & Save")).toBeTruthy();
  });

  it("should verify TOTP code successfully and update 2FA state", async () => {
    render(<TwoFactorChallengeModal />);

    // Trigger open
    window.dispatchEvent(new CustomEvent("wareflow:2fa-required"));
    expect(await screen.findByText("Two-Factor Verification Required")).toBeTruthy();

    const fetchSpy = vi.spyOn(global, "fetch").mockImplementation(async (url) => {
      const urlStr = String(url);
      if (urlStr.includes("/auth/2fa/verify")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ verified: true, message: "OK" }),
        } as Response;
      }
      if (urlStr.includes("/api/auth/session")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ status: "2fa_verified" }),
        } as Response;
      }
      return { ok: true, status: 200, json: async () => ({}) } as Response;
    });

    const inputs = screen.getAllByRole("textbox");
    expect(inputs.length).toBe(6);

    // Paste 6 digits
    fireEvent.paste(inputs[0], {
      clipboardData: {
        getData: () => "123456",
      },
    });

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalled();
    });

    expect(isTwoFactorVerified()).toBe(true);
  });
});
