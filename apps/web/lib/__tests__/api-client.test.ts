import { afterEach, describe, expect, it, vi } from "vitest";
import { apiClient, ApiError } from "../api-client";

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

describe("apiClient", () => {
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
