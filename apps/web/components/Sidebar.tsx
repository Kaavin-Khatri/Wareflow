"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { apiClient, getAuthToken, clearAuthSession } from "@/lib/api-client";
import { filterNavSections, NAVIGATION_SECTIONS, NavItem, NavSection } from "@/lib/nav";
import { SPRING_PRESETS } from "./motion/MotionProvider";
import {
  Activity,
  AlertOctagon,
  ArrowLeftRight,
  BarChart3,
  Boxes,
  Building2,
  ChevronDown,
  Clock,
  Compass,
  FileSpreadsheet,
  HelpCircle,
  History,
  KeyRound,
  LayoutDashboard,
  LogOut,
  MapPin,
  Package,
  Palette,
  ReceiptText,
  RotateCcw,
  Search,
  ShieldAlert,
  ShieldCheck,
  ShoppingBag,
  SlidersHorizontal,
  Sparkles,
  Store,
  Tags,
  TrendingUp,
  Truck,
  Undo2,
  UserCheck,
  Users,
  X,
} from "lucide-react";

interface UserProfile {
  id: string;
  email: string;
  display_name?: string | null;
  role_name: string;
  permissions: string[];
}

export interface SidebarProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

// Icon resolver for navigation items
const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  LayoutDashboard,
  Package,
  Tags,
  Boxes,
  History,
  SlidersHorizontal,
  ArrowLeftRight,
  ShieldAlert,
  Truck,
  Store,
  UserCheck,
  MapPin,
  FileSpreadsheet,
  Undo2,
  BarChart3,
  TrendingUp,
  Activity,
  ShoppingBag,
  ReceiptText,
  Clock,
  RotateCcw,
  HelpCircle,
  Building2,
  AlertOctagon,
  Users,
  ShieldCheck,
  KeyRound,
  Sparkles,
  Palette,
};

// Section category icons
const SECTION_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Overview: LayoutDashboard,
  "Inventory & Catalog": Boxes,
  "Purchasing & Inward": Truck,
  "Sales & CRM": ShoppingBag,
  "Finance & Billing": ReceiptText,
  "Analytics & Intelligence": BarChart3,
  "Organization & Admin": ShieldCheck,
};

function renderNavIcon(iconName?: string, className = "w-4 h-4 shrink-0") {
  if (!iconName) return <Compass className={className} />;
  const IconComp = ICON_MAP[iconName] || Compass;
  return <IconComp className={className} />;
}

export function Sidebar({ mobileOpen = false, onMobileClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [filteredSections, setFilteredSections] = useState<NavSection[]>(() =>
    filterNavSections(NAVIGATION_SECTIONS, ["*"], "Owner"),
  );
  const [loggingOut, setLoggingOut] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});

  useEffect(() => {
    async function loadUser() {
      try {
        const token = await getAuthToken();
        if (!token) {
          return;
        }
        const data = await apiClient.get<UserProfile>("/me");
        setProfile(data);
        const sections = filterNavSections(NAVIGATION_SECTIONS, data.permissions, data.role_name);
        setFilteredSections(sections);
      } catch {
        // Fallback gracefully — keep default navigation items visible
      }
    }
    loadUser();
  }, []);

  // Ensure active section is automatically uncollapsed on navigation
  useEffect(() => {
    if (!pathname || filteredSections.length === 0) return;
    const activeSection = filteredSections.find((sec) =>
      sec.items.some(
        (it) => pathname === it.href || (it.href !== "/dashboard" && pathname.startsWith(it.href)),
      ),
    );
    if (activeSection && collapsedSections[activeSection.title]) {
      setCollapsedSections((prev) => ({
        ...prev,
        [activeSection.title]: false,
      }));
    }
  }, [pathname, filteredSections, collapsedSections]);

  // Close mobile drawer on route change
  useEffect(() => {
    if (onMobileClose) {
      onMobileClose();
    }
  }, [pathname, onMobileClose]);

  const toggleSection = (title: string) => {
    setCollapsedSections((prev) => ({
      ...prev,
      [title]: !prev[title],
    }));
  };

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      clearAuthSession();
      await fetch("/api/auth/session", { method: "DELETE" });
      router.push("/login");
      router.refresh();
    } catch {
      clearAuthSession();
      router.push("/login");
    }
  };

  // Filter sections by search query if user types in search box
  const displayedSections = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return filteredSections;

    const terms = q.split(/\s+/).filter(Boolean);

    return filteredSections
      .map((section) => ({
        ...section,
        items: section.items.filter((item) => {
          const haystack = `${item.name} ${section.title} ${item.href}`.toLowerCase();
          return terms.every((term) => haystack.includes(term));
        }),
      }))
      .filter((section) => section.items.length > 0);
  }, [filteredSections, searchQuery]);

  const totalMatchingItems = useMemo(() => {
    return displayedSections.reduce((acc, s) => acc + s.items.length, 0);
  }, [displayedSections]);

  const navContent = (
    <div className="flex flex-col h-full select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-[var(--glass-border)] flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] flex items-center justify-center text-white font-black text-sm shadow-[0_0_16px_-2px_var(--accent-glow)] group-hover:scale-105 transition-transform">
            W
          </div>
          <div>
            <span className="font-extrabold text-sm tracking-tight text-[var(--text)] block">
              WareFlow
            </span>
            <span className="text-[10px] text-[var(--text-muted)] block font-mono font-medium">
              Wholesale ERP
            </span>
          </div>
        </Link>

        {/* Mobile Close Button */}
        {onMobileClose && (
          <button
            type="button"
            onClick={onMobileClose}
            aria-label="Close Sidebar"
            className="lg:hidden p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Quick Search Filter */}
      <div className="px-3 pt-3 pb-1">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tools & modules..."
            className="w-full pl-8 pr-7 py-1.5 rounded-xl bg-[var(--surface-hover)] border border-[var(--border)] text-xs text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] transition shadow-inner"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              aria-label="Clear Search"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text)] p-0.5"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-3 custom-scrollbar">
        {loading ? (
          <div className="space-y-3 px-2">
            <div className="h-3 bg-[var(--surface-hover)] rounded animate-pulse w-20 mb-3" />
            <div className="h-8 bg-[var(--surface-hover)] rounded-xl animate-pulse" />
            <div className="h-8 bg-[var(--surface-hover)] rounded-xl animate-pulse" />
            <div className="h-8 bg-[var(--surface-hover)] rounded-xl animate-pulse" />
          </div>
        ) : displayedSections.length === 0 ? (
          <div className="p-4 text-center text-xs text-[var(--text-muted)]">
            No modules matching &quot;{searchQuery}&quot;
          </div>
        ) : (
          displayedSections.map((section) => {
            const isSearching = Boolean(searchQuery.trim());
            const isCollapsed = !isSearching && Boolean(collapsedSections[section.title]);
            const SectionIcon = SECTION_ICONS[section.title] || Boxes;
            const hasActiveItem = section.items.some(
              (item) =>
                pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(item.href)),
            );

            return (
              <div key={section.title} className="space-y-1">
                {/* Section Header Accordion Toggle */}
                <button
                  type="button"
                  onClick={() => toggleSection(section.title)}
                  className={`w-full flex items-center justify-between px-2 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider font-mono transition-colors group cursor-pointer ${
                    hasActiveItem
                      ? "text-[var(--accent)]"
                      : "text-[var(--text-muted)] hover:text-[var(--text)]"
                  }`}
                >
                  <span className="flex items-center gap-1.5 truncate">
                    <SectionIcon className="w-3 h-3 shrink-0 opacity-70 group-hover:opacity-100" />
                    <span className="truncate">{section.title}</span>
                  </span>

                  <span className="flex items-center gap-1 shrink-0 ml-1">
                    {isCollapsed && (
                      <span className="text-[9px] px-1 py-0.2 rounded bg-[var(--surface-hover)] text-[var(--text-muted)]">
                        {section.items.length}
                      </span>
                    )}
                    <ChevronDown
                      className={`w-3 h-3 text-[var(--text-muted)] transition-transform duration-200 ${
                        isCollapsed ? "-rotate-90" : "rotate-0"
                      }`}
                    />
                  </span>
                </button>

                {/* Collapsible Nav Items */}
                <AnimatePresence initial={false}>
                  {!isCollapsed && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.18, ease: "easeInOut" }}
                      className="space-y-0.5 overflow-hidden pl-1"
                    >
                      {section.items.map((item: NavItem) => {
                        const isActive =
                          pathname === item.href ||
                          (item.href !== "/dashboard" && pathname.startsWith(item.href));

                        return (
                          <Link
                            key={item.href}
                            href={item.href}
                            className={`group relative flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs font-medium transition-all ${
                              isActive
                                ? "text-white font-semibold bg-gradient-to-r from-[var(--accent-subtle)] via-[var(--surface-hover)] to-transparent border border-[var(--accent-border)] shadow-[0_0_12px_-3px_var(--accent-glow)]"
                                : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]"
                            }`}
                          >
                            <span className="relative z-10 flex items-center gap-2.5 min-w-0">
                              <span
                                className={`transition-colors shrink-0 ${
                                  isActive
                                    ? "text-[var(--accent)]"
                                    : "text-[var(--text-muted)] group-hover:text-[var(--text)]"
                                }`}
                              >
                                {renderNavIcon(item.icon, "w-4 h-4")}
                              </span>
                              <span className="truncate">{item.name}</span>
                            </span>

                            {item.badge && (
                              <span
                                className={`relative z-10 text-[9px] px-1.5 py-0.5 rounded-md font-mono shrink-0 ml-1 ${
                                  isActive
                                    ? "bg-[var(--accent)] text-white"
                                    : "bg-[var(--surface-hover)] text-[var(--text-muted)] border border-[var(--border)]"
                                }`}
                              >
                                {item.badge}
                              </span>
                            )}
                          </Link>
                        );
                      })}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Profile & Logout Bar */}
      <div className="p-3 border-t border-[var(--glass-border)] bg-[var(--surface-overlay)]">
        {profile ? (
          <div className="flex items-center justify-between gap-2 p-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--glass-border)]">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-sm">
                {profile.display_name ? profile.display_name.charAt(0).toUpperCase() : "U"}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-bold text-[var(--text)] truncate">
                  {profile.display_name || "User"}
                </div>
                <div className="text-[10px] text-[var(--text-muted)] font-mono truncate">
                  {profile.role_name}
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              disabled={loggingOut}
              aria-label="Log Out"
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-rose-400 hover:bg-rose-500/10 transition-colors shrink-0 cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <div className="h-10 bg-[var(--surface-hover)] rounded-xl animate-pulse" />
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden lg:flex w-64 border-r border-[var(--glass-border)] bg-[var(--glass-bg)] backdrop-blur-2xl flex-col h-screen select-none z-20 shrink-0 shadow-[var(--glass-shadow)]">
        {navContent}
      </aside>

      {/* Mobile Slide-Over Sheet / Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <div className="fixed inset-0 z-50 lg:hidden flex">
            {/* Backdrop Blur Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={onMobileClose}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm"
              aria-hidden="true"
            />

            {/* Slide-in Drawer Container */}
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={SPRING_PRESETS.snappy}
              className="relative w-72 max-w-[85vw] h-full bg-[var(--glass-bg-elevated)] backdrop-blur-2xl border-r border-[var(--glass-border)] shadow-2xl z-10 flex flex-col"
            >
              {navContent}
            </motion.aside>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

export default Sidebar;
