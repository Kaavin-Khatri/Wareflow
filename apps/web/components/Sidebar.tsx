"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { apiClient, getAuthToken, clearAuthSession } from "@/lib/api-client";
import { filterNavSections, NAVIGATION_SECTIONS, NavItem, NavSection } from "@/lib/nav";
import { SPRING_PRESETS } from "./motion/MotionProvider";
import { cn } from "@/lib/utils";
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
  PanelLeftClose,
  PanelLeftOpen,
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
  collapsed?: boolean;
  onToggleCollapse?: () => void;
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

export function Sidebar({
  mobileOpen = false,
  onMobileClose,
  collapsed = false,
  onToggleCollapse,
}: SidebarProps) {
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
        setLoading(true);
        const token = await getAuthToken();
        if (!token) {
          setLoading(false);
          return;
        }
        const data = await apiClient.get<UserProfile>("/me");
        setProfile(data);
        const sections = filterNavSections(NAVIGATION_SECTIONS, data.permissions, data.role_name);
        setFilteredSections(sections);
      } catch {
        // Fallback gracefully — keep default navigation items visible
      } finally {
        setLoading(false);
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

  const navContent = (isMini: boolean) => (
    <div className="flex flex-col h-full select-none justify-between">
      {/* Brand Header */}
      {isMini ? (
        <div className="p-3 border-b border-[var(--glass-border)] flex flex-col items-center gap-3">
          <Link href="/dashboard" className="group">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] flex items-center justify-center text-white font-black text-sm shadow-[0_0_20px_-2px_var(--accent-glow)] group-hover:scale-105 transition-transform shrink-0">
              W
            </div>
          </Link>
          {onToggleCollapse && (
            <button
              type="button"
              onClick={onToggleCollapse}
              aria-label="Expand Sidebar (Ctrl+B)"
              title="Expand Sidebar (Ctrl+B)"
              className="flex items-center justify-center w-8 h-8 rounded-xl bg-[var(--surface-hover)] hover:bg-[var(--accent)] hover:text-white text-[var(--text)] border border-[var(--glass-border)] transition-all cursor-pointer shadow-sm hover:scale-105"
            >
              <PanelLeftOpen className="w-4 h-4" />
            </button>
          )}
        </div>
      ) : (
        <div className="p-4 border-b border-[var(--glass-border)] flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-3 group min-w-0">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] flex items-center justify-center text-white font-black text-sm shadow-[0_0_20px_-2px_var(--accent-glow)] group-hover:scale-105 transition-transform shrink-0">
              W
            </div>
            <div className="min-w-0">
              <span className="font-extrabold text-sm tracking-tight text-[var(--text)] block truncate">
                WareFlow
              </span>
              <span className="text-[10px] text-[var(--text-muted)] block font-mono font-medium truncate">
                Wholesale ERP
              </span>
            </div>
          </Link>

          {/* Desktop Collapse Toggle */}
          {onToggleCollapse && (
            <button
              type="button"
              onClick={onToggleCollapse}
              aria-label="Collapse Sidebar (Ctrl+B)"
              title="Collapse Sidebar (Ctrl+B)"
              className="flex items-center justify-center w-8 h-8 rounded-xl bg-[var(--surface-hover)] hover:bg-[var(--surface)] border border-[var(--glass-border)] text-[var(--text-muted)] hover:text-[var(--text)] transition-all cursor-pointer shadow-sm hover:scale-105"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          )}

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
      )}

      {/* Quick Search Filter (Only in expanded mode) */}
      {!isMini && (
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
      )}

      {/* Navigation List */}
      <div className={cn("flex-1 overflow-y-auto py-3 custom-scrollbar space-y-3", isMini ? "px-2 space-y-4" : "px-2.5")}>
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

            if (isMini) {
              return (
                <div key={section.title} className="space-y-1 border-t border-[var(--glass-border)]/40 pt-2 first:border-0 first:pt-0">
                  {section.items.map((item: NavItem) => {
                    const isActive =
                      pathname === item.href ||
                      (item.href !== "/dashboard" && pathname.startsWith(item.href));

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        title={item.name}
                        className={cn(
                          "group relative flex items-center justify-center w-10 h-10 mx-auto rounded-xl transition-all",
                          isActive
                            ? "text-white bg-[var(--accent)] shadow-[0_0_16px_-2px_var(--accent-glow)] font-bold"
                            : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]",
                        )}
                      >
                        {renderNavIcon(item.icon, "w-5 h-5")}

                        {/* Floating Tooltip Bubble */}
                        <div className="fixed left-[76px] px-3 py-1.5 rounded-xl bg-[var(--surface-elevated)]/95 backdrop-blur-2xl border border-[var(--glass-border)] shadow-2xl text-xs font-semibold text-[var(--text)] pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity z-50 whitespace-nowrap flex items-center gap-2">
                          <span>{item.name}</span>
                          {item.badge && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded-md font-mono bg-[var(--accent)] text-white">
                              {item.badge}
                            </span>
                          )}
                        </div>
                      </Link>
                    );
                  })}
                </div>
              );
            }

            return (
              <div key={section.title} className="space-y-1">
                {/* Section Header Accordion Toggle */}
                <button
                  type="button"
                  onClick={() => toggleSection(section.title)}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider font-mono transition-colors group cursor-pointer ${
                    hasActiveItem
                      ? "text-[var(--accent)]"
                      : "text-[var(--text-muted)] hover:text-[var(--text)]"
                  }`}
                >
                  <span className="flex items-center gap-2 truncate">
                    <SectionIcon className="w-3.5 h-3.5 shrink-0 opacity-75 group-hover:opacity-100" />
                    <span className="truncate">{section.title}</span>
                  </span>

                  <span className="flex items-center gap-1 shrink-0 ml-1">
                    {isCollapsed && (
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-[var(--surface-hover)] text-[var(--text-muted)]">
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
          <div className={cn("flex items-center justify-between gap-2 p-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--glass-border)]", isMini && "justify-center p-1.5")}>
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-sm">
                {profile.display_name ? profile.display_name.charAt(0).toUpperCase() : "U"}
              </div>
              {!isMini && (
                <div className="min-w-0">
                  <div className="text-xs font-bold text-[var(--text)] truncate">
                    {profile.display_name || "User"}
                  </div>
                  <div className="text-[10px] text-[var(--text-muted)] font-mono truncate">
                    {profile.role_name}
                  </div>
                </div>
              )}
            </div>

            {!isMini ? (
              <button
                type="button"
                onClick={handleLogout}
                disabled={loggingOut}
                aria-label="Log Out"
                className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-rose-400 hover:bg-rose-500/10 transition-colors shrink-0 cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleLogout}
                disabled={loggingOut}
                aria-label="Log Out"
                title="Log Out"
                className="hidden"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        ) : (
          <div className="h-10 bg-[var(--surface-hover)] rounded-xl animate-pulse" />
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Collapsible Persistent Sidebar with Liquid Frosted Glass */}
      <aside
        className={cn(
          "hidden lg:flex flex-col h-screen select-none z-20 shrink-0 border-r border-[var(--glass-border)] bg-[var(--surface-elevated)]/65 dark:bg-[#09090b]/75 backdrop-blur-2xl backdrop-saturate-150 shadow-[var(--glass-shadow)] transition-all duration-300 ease-in-out relative",
          collapsed ? "w-[72px]" : "w-64",
        )}
      >
        {/* Specular Top Sheen */}
        <div
          aria-hidden="true"
          className="absolute inset-x-0 top-0 h-[1px] bg-[var(--glass-highlight)] pointer-events-none z-10"
        />

        {navContent(collapsed)}
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
              {navContent(false)}
            </motion.aside>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

export default Sidebar;
