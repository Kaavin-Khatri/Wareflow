"use client";

import React, { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { LeadItem, LeadInfoWindow } from "./LeadInfoWindow";
import { LeadMap } from "./LeadMap";
import { LeadFilterSidebar } from "./LeadFilterSidebar";
import { ConvertToRetailerModal } from "./ConvertToRetailerModal";
import { GlassButton } from "@/components/glass/GlassButton";
import { GlassBadge } from "@/components/glass/GlassBadge";
import { GlassCard } from "@/components/glass/GlassCard";
import {
  Radar,
  Sparkles,
  Store,
  CheckCircle2,
  MapPin,
  RefreshCw,
  SlidersHorizontal,
  Compass,
  AlertCircle,
  UserCheck,
} from "lucide-react";

interface LeadListApiResponse {
  leads: LeadItem[];
  total: number;
  page: number;
  page_size: number;
}

interface ScanNowApiResponse {
  scan_run_id: string;
  results_count: number;
  new_count: number;
  message: string;
}

interface ScanRunItem {
  id: string;
  run_at?: string;
  center_lat: number;
  center_lng: number;
  radius_m: number;
  results_count: number;
  new_count: number;
}

interface ScanRunListApiResponse {
  runs: ScanRunItem[];
  total: number;
}

export function LeadDiscoveryView() {
  const [leads, setLeads] = useState<LeadItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [isNewOnly, setIsNewOnly] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [contactedFilter, setContactedFilter] = useState<
    "all" | "uncontacted" | "contacted" | "converted"
  >("all");

  // Selection state
  const [selectedLead, setSelectedLead] = useState<LeadItem | null>(null);

  // Conversion Modal state
  const [convertModalLead, setConvertModalLead] = useState<LeadItem | null>(null);

  // Scan state
  const [isScanning, setIsScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [showScanModal, setShowScanModal] = useState(false);

  // Mobile View Switcher (Map vs List)
  const [mobileTab, setMobileTab] = useState<"map" | "list">("map");

  // Fetch leads
  const fetchLeads = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<LeadListApiResponse>("/leads?page=1&page_size=200");
      setLeads(data.leads || []);
      // If a lead was selected, update its reference
      if (selectedLead) {
        const refreshed = data.leads.find((l) => l.id === selectedLead.id);
        if (refreshed) setSelectedLead(refreshed);
      }
    } catch (err: any) {
      console.error("Failed to load discovered leads:", err);
      setError(err?.message || "Failed to load discovered retail leads.");
    } finally {
      setLoading(false);
    }
  }, [selectedLead]);

  useEffect(() => {
    fetchLeads();
  }, []);

  // Handle Mark Contacted
  const handleMarkContacted = async (leadId: string, notes?: string) => {
    try {
      const updated = await apiClient.patch<LeadItem>(`/leads/${leadId}/contacted`, {
        notes: notes || null,
      });

      setLeads((prev) => prev.map((l) => (l.id === leadId ? updated : l)));
      if (selectedLead?.id === leadId) {
        setSelectedLead(updated);
      }
    } catch (err: any) {
      console.error("Failed to mark lead contacted:", err);
      alert(err?.message || "Failed to update lead status.");
    }
  };

  // Trigger On-Demand Scan
  const handleTriggerScan = async () => {
    setIsScanning(true);
    setScanMessage(null);
    try {
      const res = await apiClient.post<ScanNowApiResponse>("/leads/scan-now", {
        center_lat: 23.01185905490891,
        center_lng: 72.53806563827865,
        radius_km: 15.0,
      });
      setScanMessage(res.message);
      await fetchLeads();
      setTimeout(() => setShowScanModal(false), 2000);
    } catch (err: any) {
      console.error("Failed to execute scan:", err);
      setScanMessage(err?.message || "Scan failed. Verify API key and network.");
    } finally {
      setIsScanning(false);
    }
  };

  // Handle Convert to Retailer Success
  const handleConvertSuccess = (updatedLead: LeadItem, createdRetailer: any) => {
    setLeads((prev) => prev.map((l) => (l.id === updatedLead.id ? updatedLead : l)));
    if (selectedLead?.id === updatedLead.id) {
      setSelectedLead(updatedLead);
    }
  };

  // KPI calculations
  const totalLeads = leads.length;
  const newLeadsCount = leads.filter((l) => l.is_new && !l.contacted).length;
  const convertedCount = leads.filter((l) => Boolean(l.converted_retailer_id)).length;
  const contactedCount = leads.filter((l) => l.contacted).length;
  const pendingCount = totalLeads - contactedCount;

  return (
    <div className="space-y-6">
      {/* Top Telemetry KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <GlassCard className="p-4 relative overflow-hidden">
          <div className="flex items-center justify-between text-[var(--text-muted)] text-xs mb-1">
            <span>Total Discovered</span>
            <Store className="w-4 h-4 text-[var(--accent)]" />
          </div>
          <div className="text-2xl font-black tracking-tight text-[var(--text)]">{totalLeads}</div>
          <span className="text-[10px] text-[var(--text-subtle)] font-mono mt-1 block">
            Across 15km Territory
          </span>
        </GlassCard>

        <GlassCard className="p-4 relative overflow-hidden border-amber-500/30 bg-amber-500/5">
          <div className="flex items-center justify-between text-amber-400 text-xs mb-1">
            <span className="font-bold flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" />
              New Shops Found
            </span>
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
          </div>
          <div className="text-2xl font-black tracking-tight text-amber-300">{newLeadsCount}</div>
          <span className="text-[10px] text-amber-400/80 font-mono mt-1 block">
            Uncontacted leads
          </span>
        </GlassCard>

        <GlassCard className="p-4 relative overflow-hidden">
          <div className="flex items-center justify-between text-[var(--text-muted)] text-xs mb-1">
            <span>Outreach Contacted</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black tracking-tight text-[var(--text)]">
            {contactedCount}
          </div>
          <span className="text-[10px] text-[var(--text-subtle)] font-mono mt-1 block">
            {totalLeads > 0 ? Math.round((contactedCount / totalLeads) * 100) : 0}% contacted
          </span>
        </GlassCard>

        <GlassCard className="p-4 relative overflow-hidden border-cyan-500/30 bg-cyan-500/5">
          <div className="flex items-center justify-between text-cyan-400 text-xs mb-1">
            <span className="font-bold flex items-center gap-1">
              <UserCheck className="w-3.5 h-3.5" />
              Converted Retailers
            </span>
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
          </div>
          <div className="text-2xl font-black tracking-tight text-cyan-300">{convertedCount}</div>
          <span className="text-[10px] text-cyan-400/80 font-mono mt-1 block">
            Active wholesale accounts
          </span>
        </GlassCard>
      </div>

      {/* Action Strip: Scan Trigger & Mobile Switcher */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-[var(--text-muted)] flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-[var(--accent)]" />
            Center: Ahmedabad Hub (23.0119° N, 72.5381° E) • 15 km Radius
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Mobile View Toggle */}
          <div className="flex sm:hidden p-1 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)]">
            <button
              type="button"
              onClick={() => setMobileTab("map")}
              className={`px-3 py-1 text-xs rounded-lg font-medium transition-colors ${
                mobileTab === "map" ? "bg-[var(--accent)] text-white" : "text-[var(--text-muted)]"
              }`}
            >
              Map
            </button>
            <button
              type="button"
              onClick={() => setMobileTab("list")}
              className={`px-3 py-1 text-xs rounded-lg font-medium transition-colors ${
                mobileTab === "list" ? "bg-[var(--accent)] text-white" : "text-[var(--text-muted)]"
              }`}
            >
              List ({leads.length})
            </button>
          </div>

          <GlassButton
            size="sm"
            variant="secondary"
            onClick={fetchLeads}
            disabled={loading}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </GlassButton>

          <GlassButton
            size="sm"
            variant="primary"
            onClick={() => setShowScanModal(true)}
            className="flex items-center gap-1.5 font-bold"
          >
            <Radar className="w-3.5 h-3.5" />
            <span>Scan Now</span>
          </GlassButton>
        </div>
      </div>

      {/* Main Interactive Map & Sidebar Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-[600px] h-[calc(100vh-280px)]">
        {/* Map Column (7 cols on lg, full on mobile when active) */}
        <div
          className={`lg:col-span-8 relative h-full rounded-2xl overflow-hidden ${
            mobileTab === "list" ? "hidden sm:block" : "block"
          }`}
        >
          <LeadMap
            leads={leads}
            selectedLeadId={selectedLead?.id}
            onSelectLead={(lead) => setSelectedLead(lead)}
            center={{ lat: 23.01185905490891, lng: 72.53806563827865 }}
            radiusKm={15}
            className="h-full w-full"
          />

          {/* Floating Selected Lead Info Window Overlay */}
          {selectedLead && (
            <div
              data-testid="floating-lead-info"
              className="absolute top-4 right-4 z-30 max-w-sm w-full animate-in fade-in zoom-in-95 duration-200"
            >
              <LeadInfoWindow
                lead={selectedLead}
                onClose={() => setSelectedLead(null)}
                onMarkContacted={handleMarkContacted}
                onOpenConvertModal={(lead) => setConvertModalLead(lead)}
                isCompact
              />
            </div>
          )}
        </div>

        {/* Sidebar Column (4 cols on lg, full on mobile when active) */}
        <div
          className={`lg:col-span-4 h-full overflow-hidden ${
            mobileTab === "map" ? "hidden sm:block" : "block"
          }`}
        >
          <LeadFilterSidebar
            leads={leads}
            selectedLeadId={selectedLead?.id ?? null}
            onSelectLead={(lead) => {
              setSelectedLead(lead);
              setMobileTab("map");
            }}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            isNewOnly={isNewOnly}
            onToggleNewOnly={setIsNewOnly}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            contactedFilter={contactedFilter}
            onSelectContactedFilter={setContactedFilter}
            loading={loading}
          />
        </div>
      </div>

      {/* On-Demand Scan Modal */}
      {showScanModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-2xl bg-[var(--surface-overlay)] border border-[var(--glass-border)] p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-white shadow-lg">
                <Radar className="w-5 h-5 animate-spin" />
              </div>
              <div>
                <h3 className="font-bold text-base text-[var(--text)]">
                  Trigger Lead Discovery Scan
                </h3>
                <p className="text-xs text-[var(--text-muted)]">
                  Scan Google Places for retail grocery, snack, and gruh udyog shops
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)] text-xs space-y-2 font-mono text-[var(--text-muted)]">
              <div className="flex justify-between">
                <span>Center Location:</span>
                <span className="text-[var(--text)] font-semibold">Ahmedabad Hub</span>
              </div>
              <div className="flex justify-between">
                <span>Search Radius:</span>
                <span className="text-[var(--text)] font-semibold">15 Kilometers</span>
              </div>
              <div className="flex justify-between">
                <span>Target Keywords:</span>
                <span className="text-[var(--text)] font-semibold">Gruh Udyog, Kirana, Snacks</span>
              </div>
            </div>

            {scanMessage && (
              <div className="p-3 rounded-xl bg-violet-500/10 border border-violet-500/20 text-xs text-violet-300 font-medium animate-in fade-in">
                {scanMessage}
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowScanModal(false)}
                disabled={isScanning}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text)]"
              >
                Close
              </button>
              <GlassButton
                variant="primary"
                onClick={handleTriggerScan}
                disabled={isScanning}
                className="flex items-center gap-1.5"
              >
                <Radar className={`w-4 h-4 ${isScanning ? "animate-spin" : ""}`} />
                <span>{isScanning ? "Scanning Google Places..." : "Start Scan Now"}</span>
              </GlassButton>
            </div>
          </div>
        </div>
      )}

      {/* Convert Lead to Retailer Modal */}
      {convertModalLead && (
        <ConvertToRetailerModal
          isOpen={Boolean(convertModalLead)}
          lead={convertModalLead}
          onClose={() => setConvertModalLead(null)}
          onSuccess={handleConvertSuccess}
        />
      )}
    </div>
  );
}
