import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient, ApiError, isTwoFactorVerified, setTwoFactorVerified } from "../api-client";

describe("ApiError", () => {
  it("should correctly store status, server message, and data", () => {
    const error = new ApiError(404, "Product not found", { code: "NOT_FOUND" });
    expect(error.name).toBe("ApiError");
    expect(error.status).toBe(404);
    expect(error.serverMessage).toBe("Product not found");
    expect(error.data).toEqual({ code: "NOT_FOUND" });
    expect(error.message).toContain("API Error 404: Product not found");
  });
});

describe("Two-Factor Verification State Helpers", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("should return false when no 2FA state is stored", () => {
    expect(isTwoFactorVerified()).toBe(false);
  });

  it("should return true when setTwoFactorVerified(true) is called", () => {
    setTwoFactorVerified(true);
    expect(isTwoFactorVerified()).toBe(true);
  });

  it("should return false after setTwoFactorVerified(false) is called", () => {
    setTwoFactorVerified(true);
    expect(isTwoFactorVerified()).toBe(true);
    setTwoFactorVerified(false);
    expect(isTwoFactorVerified()).toBe(false);
  });
});

describe("apiClient", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should perform GET and parse response JSON on success", async () => {
    const mockData = { status: "ok" };
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => mockData,
    } as Response);

    const result = await apiClient.get<{ status: string }>("/health");
    expect(result).toEqual({ status: "ok" });
  });

  it("should inject X-2FA-Verified header when 2FA is verified", async () => {
    setTwoFactorVerified(true);
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => ({ status: "verified_ok" }),
    } as Response);

    await apiClient.post("/categories", { name: "Snacks" });
    expect(fetchSpy).toHaveBeenCalled();
    const calledHeaders = fetchSpy.mock.calls[0][1]?.headers as Headers;
    expect(calledHeaders.get("X-2FA-Verified")).toBe("true");
  });

  it("should dispatch wareflow:2fa-required when receiving 403 2FA error", async () => {
    setTwoFactorVerified(true);
    const eventSpy = vi.fn();
    window.addEventListener("wareflow:2fa-required", eventSpy);

    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      json: async () => ({ detail: "Two-factor authentication required for sensitive operations." }),
    } as Response);

    await expect(apiClient.post("/categories", { name: "Test" })).rejects.toThrow(ApiError);
    expect(eventSpy).toHaveBeenCalledTimes(1);
    expect(isTwoFactorVerified()).toBe(false);

    window.removeEventListener("wareflow:2fa-required", eventSpy);
  });

  it("should throw ApiError with detail message when API responds with error status", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({ detail: "Entity not found in database" }),
    } as Response);

    await expect(apiClient.get("/invalid-path")).rejects.toThrow(ApiError);

    try {
      await apiClient.get("/invalid-path");
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      if (err instanceof ApiError) {
        expect(err.status).toBe(404);
        expect(err.serverMessage).toBe("Entity not found in database");
      }
    }
  });
});
