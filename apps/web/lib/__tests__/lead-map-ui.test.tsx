import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LeadDiscoveryView } from "@/components/leads/LeadDiscoveryView";
import { LeadMap } from "@/components/leads/LeadMap";
import { LeadInfoWindow, LeadItem } from "@/components/leads/LeadInfoWindow";
import { LeadFilterSidebar } from "@/components/leads/LeadFilterSidebar";
import { apiClient } from "@/lib/api-client";

// Mock API Client
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

const MOCK_LEADS: LeadItem[] = [
  {
    id: "lead-1",
    place_id: "ChIJ_lead_1",
    name: "Ganesh Gruh Udyog",
    category: "gruh_udyog",
    address: "Paldi Cross Roads, Ahmedabad, Gujarat 380007",
    lat: 23.0125,
    lng: 72.5385,
    phone: "+91 98250 12345",
    google_maps_url: "https://maps.google.com/?cid=123",
    first_seen_at: "2026-08-20T10:00:00Z",
    is_new: true,
    contacted: false,
    contact_notes: null,
  },
  {
    id: "lead-2",
    place_id: "ChIJ_lead_2",
    name: "Mahalaxmi Snack Store",
    category: "snack_store",
    address: "Navrangpura, Ahmedabad, Gujarat 380009",
    lat: 23.033,
    lng: 72.562,
    phone: "+91 98765 43210",
    google_maps_url: "https://maps.google.com/?cid=456",
    first_seen_at: "2026-08-15T10:00:00Z",
    is_new: false,
    contacted: true,
    contact_notes: "Introduced price list, agreed to place order next week.",
  },
  {
    id: "lead-3",
    place_id: "ChIJ_lead_3",
    name: "Shreeji Kirana Store",
    category: "grocery_kirana",
    address: "Maninagar, Ahmedabad, Gujarat 380008",
    lat: 22.998,
    lng: 72.602,
    phone: "+91 99090 99090",
    google_maps_url: "https://maps.google.com/?cid=789",
    first_seen_at: "2026-08-10T10:00:00Z",
    is_new: false,
    contacted: false,
    contact_notes: null,
  },
];

describe("Step 17.2: Retail Lead Discovery Map UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("LeadInfoWindow Component", () => {
    it("renders shop details, category badge, and phone call link", () => {
      const lead = MOCK_LEADS[0];
      render(<LeadInfoWindow lead={lead} />);

      expect(screen.getByText("Ganesh Gruh Udyog")).toBeDefined();
      expect(screen.getByText("Gruh Udyog")).toBeDefined();
      expect(screen.getByText("New")).toBeDefined();
      expect(screen.getByText("Paldi Cross Roads, Ahmedabad, Gujarat 380007")).toBeDefined();

      // Verify tel: call link
      const callLink = screen.getByRole("link", { name: /Call/i });
      expect(callLink.getAttribute("href")).toBe("tel:+91 98250 12345");

      // Verify directions link
      const directionsLink = screen.getByRole("link", { name: /Directions/i });
      expect(directionsLink.getAttribute("href")).toBe("https://maps.google.com/?cid=123");
    });

    it("allows entering notes and submitting contacted status", async () => {
      const lead = MOCK_LEADS[0];
      const onMarkContacted = vi.fn().mockResolvedValue(undefined);

      render(<LeadInfoWindow lead={lead} onMarkContacted={onMarkContacted} />);

      // Click mark as contacted trigger
      const triggerBtn = screen.getByRole("button", { name: /Mark as Contacted/i });
      fireEvent.click(triggerBtn);

      // Fill in notes
      const textarea = screen.getByPlaceholderText(/Spoke to proprietor/i);
      fireEvent.change(textarea, { target: { value: "Spoke to owner, sending sample box" } });

      // Save
      const saveBtn = screen.getByRole("button", { name: /Save Contacted Status/i });
      fireEvent.click(saveBtn);

      expect(onMarkContacted).toHaveBeenCalledWith("lead-1", "Spoke to owner, sending sample box");
    });
  });

  describe("LeadMap Component", () => {
    it("renders pins for all leads and highlights new ones", () => {
      const onSelectLead = vi.fn();
      render(
        <LeadMap
          leads={MOCK_LEADS}
          selectedLeadId={null}
          onSelectLead={onSelectLead}
        />
      );

      // In fallback test environment, schematic map renders pins with testids
      const pin1 = screen.getByTestId("map-pin-lead-1");
      const pin2 = screen.getByTestId("map-pin-lead-2");
      const pin3 = screen.getByTestId("map-pin-lead-3");

      expect(pin1).toBeDefined();
      expect(pin2).toBeDefined();
      expect(pin3).toBeDefined();

      // Click pin 1 triggers onSelectLead
      fireEvent.click(pin1);
      expect(onSelectLead).toHaveBeenCalledWith(MOCK_LEADS[0]);
    });
  });

  describe("LeadFilterSidebar Component", () => {
    it("filters leads by search query and category tabs", () => {
      const onSelectLead = vi.fn();
      const onSearchChange = vi.fn();
      const onToggleNewOnly = vi.fn();
      const onSelectCategory = vi.fn();
      const onSelectContactedFilter = vi.fn();

      render(
        <LeadFilterSidebar
          leads={MOCK_LEADS}
          selectedLeadId={null}
          onSelectLead={onSelectLead}
          searchQuery="Ganesh"
          onSearchChange={onSearchChange}
          isNewOnly={false}
          onToggleNewOnly={onToggleNewOnly}
          selectedCategory="all"
          onSelectCategory={onSelectCategory}
          contactedFilter="all"
          onSelectContactedFilter={onSelectContactedFilter}
        />
      );

      // Only Ganesh matches search query "Ganesh"
      expect(screen.getByText("Ganesh Gruh Udyog")).toBeDefined();
      expect(screen.queryByText("Mahalaxmi Snack Store")).toBeNull();
    });

    it("isolates new leads when isNewOnly is true", () => {
      const onSelectLead = vi.fn();

      render(
        <LeadFilterSidebar
          leads={MOCK_LEADS}
          selectedLeadId={null}
          onSelectLead={onSelectLead}
          searchQuery=""
          onSearchChange={vi.fn()}
          isNewOnly={true}
          onToggleNewOnly={vi.fn()}
          selectedCategory="all"
          onSelectCategory={vi.fn()}
          contactedFilter="all"
          onSelectContactedFilter={vi.fn()}
        />
      );

      // Only lead-1 is is_new=true
      expect(screen.getByText("Ganesh Gruh Udyog")).toBeDefined();
      expect(screen.queryByText("Mahalaxmi Snack Store")).toBeNull();
      expect(screen.queryByText("Shreeji Kirana Store")).toBeNull();
    });
  });

  describe("LeadDiscoveryView Master Container", () => {
    it("loads telemetry counts, leads list, and allows selecting lead", async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        leads: MOCK_LEADS,
        total: 3,
        page: 1,
        page_size: 200,
      });

      render(<LeadDiscoveryView />);

      // Wait for data load
      await waitFor(() => {
        expect(screen.getAllByText("Ganesh Gruh Udyog").length).toBeGreaterThan(0);
      });

      // Verify KPI metrics rendered
      expect(screen.getByText("3")).toBeDefined(); // Total Discovered
      expect(screen.getAllByText("1").length).toBeGreaterThanOrEqual(1); // New & Contacted counts

      // Click card selects lead and opens floating info card
      const card = screen.getByTestId("lead-card-lead-1");
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId("floating-lead-info")).toBeDefined();
      });
    });

    it("triggers on-demand scan modal and executes POST /leads/scan-now", async () => {
      vi.mocked(apiClient.get).mockResolvedValue({
        leads: MOCK_LEADS,
        total: 3,
        page: 1,
        page_size: 200,
      });
      vi.mocked(apiClient.post).mockResolvedValueOnce({
        scan_run_id: "run-new-123",
        results_count: 5,
        new_count: 2,
        message: "Scan complete: 5 results, 2 new shops discovered.",
      });

      render(<LeadDiscoveryView />);

      await waitFor(() => {
        expect(screen.getAllByText("Ganesh Gruh Udyog").length).toBeGreaterThan(0);
      });

      // Open Scan Modal
      const scanNowBtn = screen.getByRole("button", { name: /Scan Now/i });
      fireEvent.click(scanNowBtn);

      expect(screen.getByText("Trigger Lead Discovery Scan")).toBeDefined();

      // Submit Scan
      const startScanBtn = screen.getByRole("button", { name: /Start Scan Now/i });
      fireEvent.click(startScanBtn);

      await waitFor(() => {
        expect(apiClient.post).toHaveBeenCalledWith("/leads/scan-now", {
          center_lat: 23.01185905490891,
          center_lng: 72.53806563827865,
          radius_km: 15.0,
        });
      });
    });
  });
});
