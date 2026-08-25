"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { collection, onSnapshot, query, orderBy, limit as firestoreLimit } from "firebase/firestore";
import ThemeToggle from "./ThemeToggle";
import { GlassBadge } from "./glass";
import { apiClient } from "@/lib/api-client";
import { db } from "@/lib/firebase-client";
import { SearchCommandPalette } from "./SearchCommandPalette";
import { usePwa } from "./pwa/PwaProvider";
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
  Info,
  Search,
  WifiOff,
  Layers,
} from "lucide-react";

interface UserProfile {
  id: string;
  email: string;
  display_name?: string | null;
  role_name: string;
  permissions: string[];
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  time: string;
  type: "warning" | "success" | "accent" | "info" | "error";
  is_read?: boolean;
}

interface ToastItem {
  id: string;
  title: string;
  message: string;
  type: "warning" | "success" | "accent" | "info" | "error";
}

interface TopbarProps {
  onMenuClick?: () => void;
}

function formatRelativeTime(dateStr?: string | Date): string {
  if (!dateStr) return "just now";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "just now";
  const diffSec = Math.floor((Date.now() - d.getTime()) / 1000);
  if (diffSec < 60) return "just now";
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  return `${Math.floor(diffSec / 86400)}d ago`;
}

function mapNotificationType(rawType?: string): NotificationItem["type"] {
  if (!rawType) return "info";
  if (rawType.includes("warning") || rawType.includes("expiry") || rawType.includes("low_stock")) {
    return "warning";
  }
  if (rawType.includes("success") || rawType.includes("delivered") || rawType.includes("received")) {
    return "success";
  }
  if (rawType.includes("failed") || rawType.includes("cancel") || rawType.includes("recall")) {
    return "error";
  }
  return "accent";
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [notificationsListRef] = useAutoAnimate();
  const { isOffline, pendingCount, hasConflicts, openSyncQueue } = usePwa();
  const notifRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const [notifications, setNotifications] = useState<NotificationItem[]>([
    {
      id: "init-1",
      title: "Low Stock Alert: Basmati Export 25kg",
      message: "Warehouse 1 balance (120 bags) below reorder point (200).",
      time: "5m ago",
      type: "warning",
      is_read: false,
    },
  ]);
  const [unreadCount, setUnreadCount] = useState<number>(1);
  const [toast, setToast] = useState<ToastItem | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // Global Cmd+K / Ctrl+K search palette shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Fetch current user profile
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

  // Fetch initial notifications from API when profile is loaded
  useEffect(() => {
    if (!profile?.id) return;

    async function loadNotifications() {
      try {
        const data = await apiClient.get<{
          items: Array<{
            id: string;
            type: string;
            title: string;
            body: string;
            is_read: boolean;
            created_at: string;
          }>;
          unread_count: number;
        }>("/notifications?limit=20");

        if (data && Array.isArray(data.items)) {
          const mapped: NotificationItem[] = data.items.map((item) => ({
            id: item.id,
            title: item.title,
            message: item.body,
            time: formatRelativeTime(item.created_at),
            type: mapNotificationType(item.type),
            is_read: item.is_read,
          }));
          setNotifications(mapped);
          setUnreadCount(data.unread_count ?? mapped.filter((n) => !n.is_read).length);
        }
      } catch (err) {
        console.debug("Initial notifications load notice:", err);
      }
    }

    loadNotifications();
  }, [profile?.id]);

  // Real-time Firestore subscription for instant delivery without polling
  useEffect(() => {
    if (!profile?.id || !db) return;

    try {
      const q = query(
        collection(db, "notifications", profile.id, "items"),
        orderBy("created_at", "desc"),
        firestoreLimit(20)
      );

      const unsubscribe = onSnapshot(
        q,
        (snapshot) => {
          snapshot.docChanges().forEach((change) => {
            if (change.type === "added") {
              const docData = change.doc.data();
              const newItem: NotificationItem = {
                id: docData.id || change.doc.id,
                title: docData.title || "Notification",
                message: docData.body || "",
                time: formatRelativeTime(docData.created_at),
                type: mapNotificationType(docData.type),
                is_read: docData.is_read ?? false,
              };

              setNotifications((prev) => {
                if (prev.some((n) => n.id === newItem.id)) {
                  return prev;
                }
                return [newItem, ...prev];
              });

              if (!newItem.is_read) {
                setUnreadCount((prev) => prev + 1);
                // Trigger live floating toast
                setToast({
                  id: newItem.id,
                  title: newItem.title,
                  message: newItem.message,
                  type: newItem.type,
                });
              }
            }
          });
        },
        (err) => {
          console.debug("Firestore onSnapshot subscription notice:", err);
        }
      );

      return () => unsubscribe();
    } catch (err) {
      console.debug("Firestore listener initialization notice:", err);
    }
  }, [profile?.id]);

  // Auto-dismiss toast after 4.5 seconds
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => {
      setToast(null);
    }, 4500);
    return () => clearTimeout(timer);
  }, [toast]);

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

  const dismissNotification = async (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)).filter((n) => n.id !== id)
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
    try {
      await apiClient.patch(`/notifications/${id}/read`);
    } catch (err) {
      console.debug("Mark notification read notice:", err);
    }
  };

  const clearAllNotifications = async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
    try {
      await apiClient.patch("/notifications/read-all");
    } catch (err) {
      console.debug("Clear all notifications notice:", err);
    }
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
    <>
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

        {/* Middle: Global Search Trigger Button */}
        <div className="flex-1 max-w-sm lg:max-w-md mx-2 sm:mx-6">
          <button
            type="button"
            data-testid="global-search-trigger"
            onClick={() => setIsSearchOpen(true)}
            className="w-full flex items-center justify-between px-3 py-1.5 rounded-xl bg-[var(--surface)] hover:bg-[var(--surface-hover)] border border-[var(--border)] text-xs text-[var(--text-muted)] transition-all hover:border-[var(--accent-border)] group"
          >
            <div className="flex items-center gap-2">
              <Search className="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-[var(--accent)] transition-colors" />
              <span className="hidden sm:inline">Search across ERP (SKU, orders, invoices)...</span>
              <span className="sm:hidden">Search ERP...</span>
            </div>
            <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded border border-[var(--border)] bg-[var(--glass-bg)] text-[10px] font-mono font-semibold text-[var(--text-muted)] group-hover:text-[var(--accent)] group-hover:border-[var(--accent-border)]">
              ⌘K
            </kbd>
          </button>
        </div>

        {/* Right: Operational Status + Notifications + Theme + Profile Menu */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          {/* Live Operational Status */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--surface-hover)] border border-[var(--border)] text-[11px] text-[var(--text-muted)] font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>0.02s Settlement</span>
          </div>

          {/* Offline Sync Queue Trigger Button */}
          <button
            type="button"
            onClick={openSyncQueue}
            aria-label="Offline Sync Queue"
            data-testid="sync-queue-trigger"
            className={`relative p-2 rounded-xl transition-colors ${
              hasConflicts
                ? "text-rose-400 bg-rose-500/10 hover:bg-rose-500/20"
                : isOffline
                ? "text-amber-400 bg-amber-500/10 hover:bg-amber-500/20"
                : pendingCount > 0
                ? "text-cyan-400 bg-cyan-500/10 hover:bg-cyan-500/20"
                : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]"
            }`}
            title={
              hasConflicts
                ? "Sync Conflicts Require Attention"
                : isOffline
                ? "Offline Mode — Click to View Sync Queue"
                : `${pendingCount} item(s) in Sync Queue`
            }
          >
            {isOffline ? <WifiOff className="w-4 h-4" /> : <Layers className="w-4 h-4" />}
            {pendingCount > 0 && (
              <span
                data-testid="sync-queue-badge"
                className={`absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-[var(--surface)] shadow-sm animate-in zoom-in ${
                  hasConflicts ? "bg-rose-500" : isOffline ? "bg-amber-500" : "bg-cyan-500"
                }`}
              >
                {pendingCount > 99 ? "99+" : pendingCount}
              </span>
            )}
          </button>

          {/* Notification Bell Dropdown */}
          <div ref={notifRef} className="relative">
            <button
              type="button"
              onClick={() => setShowNotifications((prev) => !prev)}
              aria-label="Notifications"
              className="relative p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
            >
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <span
                  data-testid="unread-badge"
                  className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-[var(--accent)] text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-[var(--surface)] shadow-sm animate-in zoom-in"
                >
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-[var(--glass-bg-elevated)] border border-[var(--glass-border)] backdrop-blur-2xl shadow-2xl p-4 z-50 animate-in fade-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between pb-3 border-b border-[var(--border)]">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-[var(--text)]">Live Notifications</span>
                    {unreadCount > 0 && (
                      <GlassBadge variant="accent" className="text-[10px] py-0 px-1.5">
                        {unreadCount} unread
                      </GlassBadge>
                    )}
                  </div>
                  {notifications.length > 0 && (
                    <button
                      type="button"
                      onClick={clearAllNotifications}
                      className="text-[11px] text-[var(--text-muted)] hover:text-[var(--accent)] font-medium flex items-center gap-1 transition-colors"
                    >
                      <CheckCheck className="w-3 h-3" />
                      <span>Mark all read</span>
                    </button>
                  )}
                </div>

                {/* Notification List with AutoAnimate */}
                <div ref={notificationsListRef} className="mt-3 max-h-72 overflow-y-auto space-y-2">
                  {notifications.length === 0 ? (
                    <div className="py-8 text-center text-xs text-[var(--text-muted)]">
                      No notifications
                    </div>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`p-3 rounded-xl border transition-all flex items-start justify-between gap-2 text-xs ${
                          n.is_read
                            ? "bg-[var(--surface-hover)]/60 border-[var(--glass-border)]/50 opacity-75"
                            : "bg-[var(--surface-hover)] border-[var(--glass-border)]"
                        }`}
                      >
                        <div className="space-y-1">
                          <div className="font-semibold text-[var(--text)] text-[12px] flex items-center gap-1.5">
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                n.type === "warning"
                                  ? "bg-amber-400"
                                  : n.type === "success"
                                    ? "bg-emerald-400"
                                    : n.type === "error"
                                      ? "bg-rose-400"
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

      {/* Floating In-App Real-Time Toast Notification */}
      {toast && (
        <aside
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="fixed top-20 right-6 z-50 max-w-sm w-full p-4 rounded-2xl bg-[var(--glass-bg-elevated)] border border-[var(--glass-border)] backdrop-blur-2xl shadow-2xl animate-in slide-in-from-top-4 fade-in duration-300 flex items-start justify-between gap-3 text-xs"
        >
          <div className="flex items-start gap-2.5">
            <div className="p-1.5 rounded-lg bg-[var(--accent-subtle)] text-[var(--accent)] shrink-0 mt-0.5">
              <Info className="w-4 h-4" />
            </div>
            <div>
              <div className="font-bold text-[var(--text)] text-[13px]">{toast.title}</div>
              <p className="text-[var(--text-muted)] text-[12px] mt-0.5 leading-snug">
                {toast.message}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setToast(null)}
            aria-label="Close Alert"
            className="text-[var(--text-subtle)] hover:text-[var(--text)] p-1 rounded transition-colors shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </aside>
      )}

      {/* Global Admin Search Command Palette (Cmd+K) */}
      <SearchCommandPalette
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
      />
    </>
  );
}

export default Topbar;
