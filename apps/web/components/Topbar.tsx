"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import ThemeToggle from "./ThemeToggle";
import { GlassBadge } from "./glass";
import { apiClient } from "@/lib/api-client";
import {
  Menu,
  Bell,
  CheckCheck,
  X,
  Shield,
  Palette,
  FileText,
  LogOut,
  ChevronDown,
  Sparkles,
} from "lucide-react";

interface UserProfile {
  id: string;
  email: string;
  display_name?: string | null;
  role_name: string;
  permissions: string[];
}

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  time: string;
  type: "warning" | "success" | "accent";
}

interface TopbarProps {
  onMenuClick?: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [notificationsListRef] = useAutoAnimate();
  const notifRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const [notifications, setNotifications] = useState<NotificationItem[]>([
    {
      id: "n1",
      title: "Low Stock Alert: Basmati Export 25kg",
      message: "Warehouse 1 balance (120 bags) below reorder point (200).",
      time: "5m ago",
      type: "warning",
    },
    {
      id: "n2",
      title: "GRN Received: PO-2026-089",
      message: "500 bags confirmed from Royal Agro Foods.",
      time: "25m ago",
      type: "success",
    },
    {
      id: "n3",
      title: "New Retailer Onboarded",
      message: "Vashi APMC Wholesale Traders KYC approved.",
      time: "1h ago",
      type: "accent",
    },
  ]);

  useEffect(() => {
    async function fetchUser() {
      try {
        const data = await apiClient.get<UserProfile>("/me");
        setProfile(data);
      } catch (err) {
        console.warn("Failed to fetch user in Topbar:", err);
      }
    }
    fetchUser();
  }, []);

  // Click outside to dismiss popovers
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const dismissNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/session", { method: "DELETE" });
      router.push("/login");
      router.refresh();
    } catch {
      router.push("/login");
    }
  };

  return (
    <header className="h-16 shrink-0 border-b border-[var(--border)] px-4 sm:px-8 flex items-center justify-between glass-panel z-30 select-none">
      {/* Left: Mobile Menu Trigger + Workspace Title */}
      <div className="flex items-center gap-3">
        {onMenuClick && (
          <button
            type="button"
            onClick={onMenuClick}
            aria-label="Open Navigation Menu"
            className="lg:hidden p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
          <span className="font-bold text-[var(--text)] tracking-tight">WareFlow</span>
          <span className="text-[var(--text-subtle)]">/</span>
          <span className="font-mono text-[11px] px-2 py-0.5 rounded-md bg-[var(--accent-subtle)] text-[var(--accent)] font-semibold border border-[var(--accent-border)] hidden sm:inline-block">
            Wholesale ERP
          </span>
        </div>
      </div>

      {/* Right: Operational Status + Notifications + Theme + Profile Menu */}
      <div className="flex items-center gap-2.5 sm:gap-3">
        {/* Live Operational Status */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--surface-hover)] border border-[var(--border)] text-[11px] text-[var(--text-muted)] font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>0.02s Settlement</span>
        </div>

        {/* Notification Bell Dropdown */}
        <div ref={notifRef} className="relative">
          <button
            type="button"
            onClick={() => setShowNotifications((prev) => !prev)}
            aria-label="Notifications"
            className="relative p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
          >
            <Bell className="w-4 h-4" />
            {notifications.length > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[var(--accent)] ring-2 ring-[var(--surface)]" />
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-[var(--glass-bg-elevated)] border border-[var(--glass-border)] backdrop-blur-2xl shadow-2xl p-4 z-50 animate-in fade-in zoom-in-95 duration-200">
              <div className="flex items-center justify-between pb-3 border-b border-[var(--border)]">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-xs text-[var(--text)]">Live Notifications</span>
                  <GlassBadge variant="accent" className="text-[10px] py-0 px-1.5">
                    {notifications.length}
                  </GlassBadge>
                </div>
                {notifications.length > 0 && (
                  <button
                    type="button"
                    onClick={clearAllNotifications}
                    className="text-[11px] text-[var(--text-muted)] hover:text-[var(--accent)] font-medium flex items-center gap-1 transition-colors"
                  >
                    <CheckCheck className="w-3 h-3" />
                    <span>Clear all</span>
                  </button>
                )}
              </div>

              {/* Notification List with AutoAnimate */}
              <div ref={notificationsListRef} className="mt-3 max-h-72 overflow-y-auto space-y-2">
                {notifications.length === 0 ? (
                  <div className="py-8 text-center text-xs text-[var(--text-muted)]">
                    No new notifications
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className="p-3 rounded-xl bg-[var(--surface-hover)] border border-[var(--glass-border)] flex items-start justify-between gap-2 text-xs"
                    >
                      <div className="space-y-1">
                        <div className="font-semibold text-[var(--text)] text-[12px] flex items-center gap-1.5">
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              n.type === "warning"
                                ? "bg-amber-400"
                                : n.type === "success"
                                  ? "bg-emerald-400"
                                  : "bg-[var(--accent)]"
                            }`}
                          />
                          {n.title}
                        </div>
                        <p className="text-[11px] text-[var(--text-muted)] leading-tight">
                          {n.message}
                        </p>
                        <span className="text-[10px] text-[var(--text-subtle)] font-mono block">
                          {n.time}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => dismissNotification(n.id)}
                        aria-label="Dismiss Notification"
                        className="text-[var(--text-subtle)] hover:text-[var(--text)] p-1 rounded transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* User Profile Menu */}
        <div ref={userMenuRef} className="relative">
          <button
            type="button"
            onClick={() => setShowUserMenu((prev) => !prev)}
            aria-label="User menu"
            className="flex items-center gap-2 p-1.5 rounded-xl hover:bg-[var(--surface-hover)] border border-transparent hover:border-[var(--glass-border)] transition-all"
          >
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] text-white font-bold text-xs flex items-center justify-center shadow-sm">
              {profile?.display_name ? profile.display_name.charAt(0).toUpperCase() : "U"}
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[var(--text-muted)] hidden sm:block" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-[var(--glass-bg-elevated)] border border-[var(--glass-border)] backdrop-blur-2xl shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95 duration-200 text-xs">
              <div className="p-3 border-b border-[var(--border)] mb-1">
                <div className="font-bold text-[var(--text)] truncate">
                  {profile?.display_name || "Authorized User"}
                </div>
                <div className="text-[11px] text-[var(--text-muted)] truncate font-mono">
                  {profile?.email || "user@wareflow.internal"}
                </div>
                {profile?.role_name && (
                  <div className="mt-2">
                    <GlassBadge variant="accent" className="text-[10px] py-0">
                      {profile.role_name}
                    </GlassBadge>
                  </div>
                )}
              </div>

              <div className="space-y-0.5">
                <Link
                  href="/admin/settings/appearance"
                  onClick={() => setShowUserMenu(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
                >
                  <Palette className="w-3.5 h-3.5 text-[var(--accent)]" />
                  <span>Theme & Accent</span>
                </Link>

                <Link
                  href="/admin/settings/security"
                  onClick={() => setShowUserMenu(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
                >
                  <Shield className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Security & 2FA</span>
                </Link>

                <Link
                  href="/admin/audit"
                  onClick={() => setShowUserMenu(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
                >
                  <FileText className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Admin Audit Log</span>
                </Link>

                <Link
                  href="/styleguide"
                  onClick={() => setShowUserMenu(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span>Design Styleguide</span>
                </Link>
              </div>

              <div className="pt-1 mt-1 border-t border-[var(--border)]">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-rose-400 hover:bg-rose-500/10 transition-colors font-medium text-left"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Topbar;
