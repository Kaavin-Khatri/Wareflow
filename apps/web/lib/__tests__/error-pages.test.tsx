import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import NotFoundPage from "@/app/not-found";
import GlobalError from "@/app/error";

describe("Error & 404 Handlers (Award-Benchmark Polish)", () => {
  it("renders 404 Not Found page with domain copy and navigation links", () => {
    render(<NotFoundPage />);
    expect(screen.getByText("404")).toBeDefined();
    expect(screen.getByText("Warehouse Bin Not Found")).toBeDefined();
    expect(screen.getByText("Return to Dashboard")).toBeDefined();
    expect(screen.getByText("Browse Products")).toBeDefined();
  });

  it("renders Global Error boundary with exception details and retry trigger", () => {
    const mockReset = vi.fn();
    const testError = new Error("Connection timed out while fetching stock ledger");

    render(<GlobalError error={testError} reset={mockReset} />);

    expect(screen.getByText("Warehouse Processing Interrupted")).toBeDefined();
    expect(screen.getByText("Connection timed out while fetching stock ledger")).toBeDefined();

    const retryBtn = screen.getByText("Retry Operation");
    expect(retryBtn).toBeDefined();

    fireEvent.click(retryBtn);
    expect(mockReset).toHaveBeenCalledTimes(1);
  });
});
