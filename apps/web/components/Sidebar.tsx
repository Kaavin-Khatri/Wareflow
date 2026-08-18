"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { apiClient } from "@/lib/api-client";
import { filterNavSections, NAVIGATION_SECTIONS, NavSection } from "@/lib/nav";
import { SPRING_PRESETS } from "./motion/MotionProvider";
import { LogOut, X } from "lucide-react";

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

export function Sidebar({ mobileOpen = false, onMobileClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [filteredSections, setFilteredSections] = useState<NavSection[]>([]);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    async function loadUser() {
      try {
        const data = await apiClient.get<UserProfile>("/me");
        setProfile(data);
        const sections = filterNavSections(NAVIGATION_SECTIONS, data.permissions, data.role_name);
        setFilteredSections(sections);
      } catch (err) {
        console.warn("Failed to load user profile in sidebar:", err);
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, []);

  // Close mobile drawer on route change
  useEffect(() => {
    if (onMobileClose) {
      onMobileClose();
    }
  }, [pathname, onMobileClose]);

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await fetch("/api/auth/session", { method: "DELETE" });
      router.push("/login");
      router.refresh();
    } catch {
      router.push("/login");
    }
  };

  const navContent = (
    <div className="flex flex-col h-full select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-[var(--glass-border)] flex items-center justify-between">
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
            className="lg:hidden p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {loading ? (
          <div className="space-y-3 px-2">
            <div className="h-3 bg-[var(--surface-hover)] rounded animate-pulse w-20 mb-3" />
            <div className="h-8 bg-[var(--surface-hover)] rounded-xl animate-pulse" />
            <div className="h-8 bg-[var(--surface-hover)] rounded-xl animate-pulse" />
            <div className="h-8 bg-[var(--surface-hover)] rounded-xl animate-pulse" />
          </div>
        ) : (
          filteredSections.map((section) => (
            <div key={section.title} className="space-y-1">
              <h3 className="px-3 text-[10px] font-bold text-[var(--text-subtle)] uppercase tracking-wider mb-2 font-mono">
                {section.title}
              </h3>
              {section.items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/dashboard" && pathname.startsWith(item.href));

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`relative flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                      isActive
                        ? "text-white font-semibold"
                        : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]"
                    }`}
                  >
                    {/* Motion Active Background Indicator Pill */}
                    {isActive && (
                      <motion.div
                        layoutId="active-sidebar-pill"
                        transition={SPRING_PRESETS.snappy}
                        className="absolute inset-0 rounded-xl bg-gradient-to-r from-[var(--accent)] to-[var(--accent-hover)] shadow-[0_0_16px_-2px_var(--accent-glow)] z-0"
                      />
                    )}

                    <span className="relative z-10">{item.name}</span>

                    {item.badge && (
                      <span
                        className={`relative z-10 text-[10px] px-1.5 py-0.5 rounded-md font-mono ${
                          isActive
                            ? "bg-white/20 text-white"
                            : "bg-[var(--surface-hover)] text-[var(--text-muted)] border border-[var(--border)]"
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          ))
        )}
      </div>

      {/* Footer Profile & Logout Bar */}
      <div className="p-3 border-t border-[var(--glass-border)] bg-[var(--surface-overlay)]">
        {profile ? (
          <div className="flex items-center justify-between gap-2 p-2 rounded-xl bg-[var(--glass-bg)] border border-[var(--glass-border)]">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] text-white font-bold text-xs flex items-center justify-center shrink-0">
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
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-rose-400 hover:bg-rose-500/10 transition-colors shrink-0"
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
