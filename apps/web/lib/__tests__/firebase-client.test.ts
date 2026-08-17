import { describe, expect, it } from "vitest";

describe("Firebase Client Configuration", () => {
  it("initializes auth instance and OAuth providers without crashing", async () => {
    const { auth, googleProvider, appleProvider } = await import("../firebase-client");
    expect(auth).toBeDefined();
    expect(googleProvider).toBeDefined();
    expect(appleProvider).toBeDefined();
  });
});
