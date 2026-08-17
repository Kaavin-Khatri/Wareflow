import { describe, expect, it } from "vitest";

describe("Firebase Client Configuration", () => {
  it("initializes auth instance without crashing", async () => {
    const { auth, googleProvider } = await import("../firebase-client");
    expect(auth).toBeDefined();
    expect(googleProvider).toBeDefined();
  });
});
