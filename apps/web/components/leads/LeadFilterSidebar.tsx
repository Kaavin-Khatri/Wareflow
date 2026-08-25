"use client";

import React, { useMemo, useRef, useEffect } from "react";
import {
  Search,
  X,
  Sparkles,
  Phone,
  CheckCircle2,
  Filter,
  MapPin,
  Clock,
  Building2,
} from "lucide-react";
import { LeadItem, getCategoryMetadata } from "./LeadInfoWindow";

export interface LeadFilterSidebarProps {
  leads: LeadItem[];
  selectedLeadId: string | null;
  onSelectLead: (lead: LeadItem) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  isNewOnly: boolean;
  onToggleNewOnly: (newOnly: boolean) => void;
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  contactedFilter: "all" | "uncontacted" | "contacted";
  onSelectContactedFilter: (filter: "all" | "uncontacted" | "contacted") => void;
  loading?: boolean;
}

const CATEGORY_TABS = [
  { id: "all", label: "All Categories" },
  { id: "gruh_udyog", label: "Gruh Udyog" },
  { id: "snack_store", label: "Snack / Namkeen" },
  { id: "grocery_kirana", label: "Kirana / Grocery" },
];

export function LeadFilterSidebar({
  leads,
  selectedLeadId,
  onSelectLead,
  searchQuery,
  onSearchChange,
  isNewOnly,
  onToggleNewOnly,
  selectedCategory,
  onSelectCategory,
  contactedFilter,
  onSelectContactedFilter,
  loading = false,
}: LeadFilterSidebarProps) {
  const listContainerRef = useRef<HTMLDivElement>(null);
  const activeCardRef = useRef<HTMLDivElement>(null);

  // Counts for filters
  const newCount = useMemo(() => leads.filter((l) => l.is_new).length, [leads]);
  const contactedCount = useMemo(() => leads.filter((l) => l.contacted).length, [leads]);

  // Filtered leads
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      // 1. Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = lead.name.toLowerCase().includes(q);
        const matchAddress = lead.address?.toLowerCase().includes(q) ?? false;
        if (!matchName && !matchAddress) return false;
      }

      // 2. New Only filter
      if (isNewOnly && !lead.is_new) {
        return false;
      }

      // 3. Category Filter
      if (selectedCategory !== "all" && lead.category !== selectedCategory) {
        return false;
      }

      // 4. Contacted Filter
      if (contactedFilter === "contacted" && !lead.contacted) {
        return false;
      }
      if (contactedFilter === "uncontacted" && lead.contacted) {
        return false;
      }

      return true;
    });
  }, [leads, searchQuery, isNewOnly, selectedCategory, contactedFilter]);

  // Auto-scroll selected card into view
  useEffect(() => {
    if (selectedLeadId && activeCardRef.current && listContainerRef.current) {
      if (typeof activeCardRef.current.scrollIntoView === "function") {
        activeCardRef.current.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }
    }
  }, [selectedLeadId]);

  return (
    <div className="flex flex-col h-full rounded-2xl bg-[var(--surface-overlay)] border border-[var(--glass-border)] backdrop-blur-xl overflow-hidden shadow-xl select-none">
      {/* Search and Filters Header */}
      <div className="p-4 border-b border-[var(--glass-border)] space-y-3 shrink-0">
        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            data-testid="leads-search-input"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search leads by name or locality..."
            className="w-full text-xs pl-9 pr-8 py-2.5 rounded-xl bg-[var(--glass-bg)] border border-[var(--border)] text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] transition-colors"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange("")}
              aria-label="Clear search"
              className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 rounded-md text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* New Leads Isolation Switch */}
        <div className="flex items-center justify-between p-2 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)]">
          <div className="flex items-center gap-2">
            <div
              className={`w-6 h-6 rounded-lg flex items-center justify-center ${
                isNewOnly
                  ? "bg-amber-500 text-black shadow-[0_0_12px_rgba(245,158,11,0.5)]"
                  : "bg-[var(--glass-bg)] text-amber-400"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <div>
              <span className="text-xs font-bold text-[var(--text)] block leading-none">
                New Shops Only
              </span>
              <span className="text-[10px] text-[var(--text-muted)]">
                Highlight never-seen leads
              </span>
            </div>
          </div>

          <button
            type="button"
            data-testid="toggle-new-leads"
            onClick={() => onToggleNewOnly(!isNewOnly)}
            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              isNewOnly ? "bg-amber-500" : "bg-slate-700"
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                isNewOnly ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        {/* Category Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {CATEGORY_TABS.map((tab) => {
            const isSelected = selectedCategory === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                data-testid={`category-tab-${tab.id}`}
                onClick={() => onSelectCategory(tab.id)}
                className={`text-[11px] px-2.5 py-1 rounded-lg font-medium whitespace-nowrap transition-colors ${
                  isSelected
                    ? "bg-[var(--accent)] text-white font-semibold shadow-sm"
                    : "bg-[var(--surface-hover)] text-[var(--text-muted)] hover:text-[var(--text)] border border-[var(--border)]"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Contacted Filter & Result Count Bar */}
        <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono pt-1">
          <span>
            {filteredLeads.length} of {leads.length} leads
          </span>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => onSelectContactedFilter("all")}
              className={`px-1.5 py-0.5 rounded ${
                contactedFilter === "all"
                  ? "text-[var(--text)] font-bold bg-[var(--surface-hover)]"
                  : "hover:text-[var(--text)]"
              }`}
            >
              All
            </button>
            <span>•</span>
            <button
              type="button"
              onClick={() => onSelectContactedFilter("uncontacted")}
              className={`px-1.5 py-0.5 rounded ${
                contactedFilter === "uncontacted"
                  ? "text-[var(--text)] font-bold bg-[var(--surface-hover)]"
                  : "hover:text-[var(--text)]"
              }`}
            >
              Pending
            </button>
            <span>•</span>
            <button
              type="button"
              onClick={() => onSelectContactedFilter("contacted")}
              className={`px-1.5 py-0.5 rounded ${
                contactedFilter === "contacted"
                  ? "text-emerald-400 font-bold bg-emerald-500/10"
                  : "hover:text-emerald-400"
              }`}
            >
              Contacted ({contactedCount})
            </button>
          </div>
        </div>
      </div>

      {/* Leads List */}
      <div
        ref={listContainerRef}
        data-testid="leads-sidebar-list"
        className="flex-1 overflow-y-auto p-3 space-y-2.5 divide-y divide-[var(--glass-border)]"
      >
        {loading ? (
          <div className="space-y-3 p-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 bg-[var(--surface-hover)] rounded-xl animate-pulse" />
            ))}
          </div>
        ) : filteredLeads.length === 0 ? (
          <div className="py-12 text-center text-xs text-[var(--text-muted)] space-y-2">
            <Building2 className="w-8 h-8 mx-auto text-[var(--text-subtle)] opacity-40" />
            <p className="font-medium">No leads match the selected filters.</p>
            <button
              type="button"
              onClick={() => {
                onSearchChange("");
                onToggleNewOnly(false);
                onSelectCategory("all");
                onSelectContactedFilter("all");
              }}
              className="text-[var(--accent)] hover:underline text-[11px]"
            >
              Reset all filters
            </button>
          </div>
        ) : (
          filteredLeads.map((lead) => {
            const isSelected = lead.id === selectedLeadId;
            const catMeta = getCategoryMetadata(lead.category);

            return (
              <div
                key={lead.id}
                ref={isSelected ? activeCardRef : null}
                data-testid={`lead-card-${lead.id}`}
                onClick={() => onSelectLead(lead)}
                className={`pt-2.5 first:pt-0 group cursor-pointer transition-all`}
              >
                <div
                  className={`p-3 rounded-xl border transition-all ${
                    isSelected
                      ? "bg-[var(--surface-active)] border-[var(--accent)] shadow-[0_0_16px_-4px_var(--accent-glow)] ring-1 ring-[var(--accent)]"
                      : "bg-[var(--glass-bg)] border-[var(--border)] hover:border-[var(--glass-border)] hover:bg-[var(--surface-hover)]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-1.5 flex-wrap min-w-0">
                      <h4 className="text-xs font-bold text-[var(--text)] truncate">
                        {lead.name}
                      </h4>
                      {lead.is_new && (
                        <span className="inline-flex items-center gap-0.5 px-1.5 py-0.2 rounded-full text-[9px] font-black uppercase tracking-wider bg-amber-500 text-black shrink-0">
                          <Sparkles className="w-2.5 h-2.5" />
                          New
                        </span>
                      )}
                    </div>

                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-medium shrink-0 border ${catMeta.bgClass}`}
                    >
                      {catMeta.label}
                    </span>
                  </div>

                  {lead.address && (
                    <div className="flex items-center gap-1 text-[11px] text-[var(--text-muted)] line-clamp-1 mb-1.5">
                      <MapPin className="w-3 h-3 text-[var(--text-subtle)] shrink-0" />
                      <span className="truncate">{lead.address}</span>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-1 text-[10px] text-[var(--text-subtle)] font-mono">
                    {lead.phone ? (
                      <a
                        href={`tel:${lead.phone}`}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-emerald-400 hover:underline"
                      >
                        <Phone className="w-2.5 h-2.5" />
                        <span>{lead.phone}</span>
                      </a>
                    ) : (
                      <span>No phone listed</span>
                    )}

                    {lead.contacted ? (
                      <span className="inline-flex items-center gap-0.5 text-emerald-400 font-sans font-medium">
                        <CheckCircle2 className="w-3 h-3" />
                        Contacted
                      </span>
                    ) : (
                      <span className="text-[var(--text-subtle)] font-sans">Pending</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
