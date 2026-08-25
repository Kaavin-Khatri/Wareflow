"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  X,
  Package,
  ShoppingCart,
  Truck,
  Receipt,
  Store,
  Building2,
  CornerDownLeft,
  Loader2,
  ExternalLink,
  ArrowUpDown,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { GlassBadge } from "./glass";

export interface SearchResultItem {
  id: string;
  kind: "product" | "sales_order" | "purchase_order" | "retailer" | "supplier" | "invoice" | string;
  title: string;
  subtitle?: string | null;
  badge?: string | null;
  url: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResultItem[];
}

interface SearchCommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

function getKindIcon(kind: string) {
  switch (kind) {
    case "product":
      return <Package className="w-4 h-4 text-emerald-400" />;
    case "sales_order":
      return <ShoppingCart className="w-4 h-4 text-cyan-400" />;
    case "purchase_order":
      return <Truck className="w-4 h-4 text-amber-400" />;
    case "invoice":
      return <Receipt className="w-4 h-4 text-purple-400" />;
    case "retailer":
      return <Store className="w-4 h-4 text-blue-400" />;
    case "supplier":
      return <Building2 className="w-4 h-4 text-rose-400" />;
    default:
      return <Search className="w-4 h-4 text-zinc-400" />;
  }
}

function getKindBadgeVariant(kind: string): "accent" | "success" | "warning" | "error" | "neutral" {
  switch (kind) {
    case "product":
      return "success";
    case "sales_order":
      return "accent";
    case "purchase_order":
      return "warning";
    case "invoice":
      return "neutral";
    case "retailer":
      return "accent";
    case "supplier":
      return "error";
    default:
      return "neutral";
  }
}

export function SearchCommandPalette({ isOpen, onClose }: SearchCommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Focus input whenever opened
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setResults([]);
      setSelectedIndex(0);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  }, [isOpen]);

  // Debounced search query handler
  useEffect(() => {
    if (!isOpen) return;
    const cleanQ = query.trim();
    if (!cleanQ) {
      setResults([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    const timeoutId = setTimeout(async () => {
      try {
        const data = await apiClient.get<SearchResponse>(
          `/search?q=${encodeURIComponent(cleanQ)}&limit=25`,
        );
        setResults(data?.results || []);
        setSelectedIndex(0);
      } catch (err) {
        console.error("Global search error:", err);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 150);

    return () => clearTimeout(timeoutId);
  }, [query, isOpen]);

  // Selection navigation handler
  const handleSelect = useCallback(
    (item: SearchResultItem) => {
      onClose();
      router.push(item.url);
    },
    [onClose, router],
  );

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (results.length > 0) {
        setSelectedIndex((prev) => (prev + 1) % results.length);
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (results.length > 0) {
        setSelectedIndex((prev) => (prev - 1 + results.length) % results.length);
      }
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (results.length > 0 && results[selectedIndex]) {
        handleSelect(results[selectedIndex]);
      }
    }
  };

  // Scroll active item into view
  useEffect(() => {
    if (listRef.current) {
      const activeEl = listRef.current.children[selectedIndex] as HTMLElement;
      if (activeEl && typeof activeEl.scrollIntoView === "function") {
        activeEl.scrollIntoView({ block: "nearest" });
      }
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  return (
    <div
      data-testid="search-command-palette-backdrop"
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        data-testid="search-command-palette-modal"
        className="w-full max-w-2xl rounded-2xl bg-[var(--glass-bg-elevated)] border border-[var(--glass-border)] shadow-2xl overflow-hidden backdrop-blur-2xl animate-in zoom-in-95 duration-150 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-[var(--border)] gap-3 bg-[var(--surface)]/50">
          <Search className="w-5 h-5 text-[var(--accent)] shrink-0" />
          <input
            ref={inputRef}
            data-testid="global-search-input"
            type="text"
            placeholder="Search products, orders, invoices, retailers, suppliers (SKU, names, codes)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-transparent text-sm sm:text-base font-medium text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none"
          />
          {isLoading ? (
            <Loader2 className="w-4 h-4 text-[var(--text-muted)] animate-spin shrink-0" />
          ) : query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="p-1 rounded-md text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          ) : (
            <kbd className="hidden sm:inline-flex items-center gap-0.5 px-2 py-0.5 rounded border border-[var(--border)] bg-[var(--surface-hover)] text-[10px] font-mono text-[var(--text-muted)]">
              ESC
            </kbd>
          )}
        </div>

        {/* Results List View */}
        <div
          ref={listRef}
          data-testid="search-results-list"
          className="max-h-96 overflow-y-auto p-2 space-y-1 divide-y divide-transparent"
        >
          {query.trim() === "" ? (
            <div className="py-12 px-6 text-center text-xs text-[var(--text-muted)] space-y-2">
              <p className="font-medium text-[var(--text)]">Global ERP Search</p>
              <p>
                Type an SKU (e.g.{" "}
                <span className="font-mono text-[var(--accent)]">RIC-BAS-001</span>), Order Number (
                <span className="font-mono text-[var(--accent)]">SO-2026-0001</span>), Invoice
                Number (<span className="font-mono text-[var(--accent)]">INV/2026-27/...</span>), or
                Retailer/Supplier name.
              </p>
            </div>
          ) : results.length === 0 && !isLoading ? (
            <div className="py-12 px-6 text-center text-xs text-[var(--text-muted)] space-y-1">
              <p className="font-semibold text-sm text-[var(--text)]">No matches found</p>
              <p>No products, orders, invoices, or parties matched &ldquo;{query}&rdquo;.</p>
            </div>
          ) : (
            results.map((item, index) => {
              const isSelected = index === selectedIndex;
              return (
                <div
                  key={`${item.kind}-${item.id}`}
                  data-testid={`search-result-item-${index}`}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`px-3.5 py-2.5 rounded-xl cursor-pointer flex items-center justify-between gap-3 transition-all ${
                    isSelected
                      ? "bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--text)] shadow-sm"
                      : "hover:bg-[var(--surface-hover)] border border-transparent text-[var(--text-muted)]"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`p-2 rounded-lg border shrink-0 ${
                        isSelected
                          ? "bg-[var(--glass-bg-elevated)] border-[var(--accent-border)] text-[var(--accent)]"
                          : "bg-[var(--surface)] border-[var(--border)]"
                      }`}
                    >
                      {getKindIcon(item.kind)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs sm:text-sm text-[var(--text)] truncate">
                          {item.title}
                        </span>
                        {item.badge && (
                          <GlassBadge
                            variant={getKindBadgeVariant(item.kind)}
                            className="text-[9px] uppercase px-1.5 py-0 shrink-0"
                          >
                            {item.badge}
                          </GlassBadge>
                        )}
                      </div>
                      {item.subtitle && (
                        <p className="text-[11px] text-[var(--text-muted)] truncate mt-0.5">
                          {item.subtitle}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {isSelected && (
                      <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-mono text-[var(--accent)] font-medium">
                        <span>Open</span>
                        <CornerDownLeft className="w-3 h-3" />
                      </span>
                    )}
                    <ExternalLink className="w-3.5 h-3.5 text-[var(--text-muted)] opacity-50" />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Hint Bar */}
        <div className="px-4 py-2 bg-[var(--surface)]/80 border-t border-[var(--border)] flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono">
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 rounded border border-[var(--border)] bg-[var(--surface)]">
                ↑
              </kbd>
              <kbd className="px-1.5 py-0.5 rounded border border-[var(--border)] bg-[var(--surface)]">
                ↓
              </kbd>
              <span>Navigate</span>
            </span>
            <span className="inline-flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 rounded border border-[var(--border)] bg-[var(--surface)]">
                ↵
              </kbd>
              <span>Select</span>
            </span>
          </div>
          <span className="inline-flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 rounded border border-[var(--border)] bg-[var(--surface)]">
              ESC
            </kbd>
            <span>Close</span>
          </span>
        </div>
      </div>
    </div>
  );
}
