"use client";

import React, { useState, useEffect, useCallback } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence } from "motion/react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { PageTransition } from "./motion/GlassMotion";
import { TwoFactorChallengeModal } from "./TwoFactorChallengeModal";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const pathname = usePathname();

  // Load saved sidebar collapsed state on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("wareflow-sidebar-collapsed");
      if (saved !== null) {
        setIsSidebarCollapsed(saved === "true");
      }
    } catch {
      // Ignore storage errors in restricted contexts
    }
  }, []);

  const handleToggleSidebar = useCallback(() => {
    setIsSidebarCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("wareflow-sidebar-collapsed", String(next));
      } catch {
        // Ignore storage errors
      }
      return next;
    });
  }, []);

  // Global Keyboard Shortcut: Ctrl+B or Cmd+B to toggle sidebar
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
        // Only trigger if not actively typing inside an input/textarea
        const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
        if (tag === "input" || tag === "textarea" || (e.target as HTMLElement)?.isContentEditable) {
          return;
        }
        e.preventDefault();
        handleToggleSidebar();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleToggleSidebar]);

  return (
    <div className="flex h-screen w-full text-[var(--text)] antialiased overflow-hidden font-sans relative selection:bg-[var(--accent)] selection:text-white">
      {/* Expandable & Retractable Liquid Glass Sidebar Navigation */}
      <Sidebar
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
        collapsed={isSidebarCollapsed}
        onToggleCollapse={handleToggleSidebar}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        {/* Modern Liquid Glass Topbar */}
        <Topbar
          onMenuClick={() => setMobileMenuOpen(true)}
          onToggleSidebar={handleToggleSidebar}
          isSidebarCollapsed={isSidebarCollapsed}
        />

        {/* Scrollable Page Body with Generous Padding & Motion Transition */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-5 sm:p-7 lg:p-9 relative z-10 custom-scrollbar">
          <div className="max-w-7xl mx-auto w-full space-y-6">
            <AnimatePresence mode="wait">
              <PageTransition key={pathname}>{children}</PageTransition>
            </AnimatePresence>
          </div>
        </main>
      </div>

      {/* Global Two-Factor Authentication Interactive Challenge Modal */}
      <TwoFactorChallengeModal />
    </div>
  );
}

export default AppLayout;
