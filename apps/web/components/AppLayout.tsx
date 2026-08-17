"use client";

import React from "react";
import Sidebar from "./Sidebar";
import ThemeToggle from "./ThemeToggle";

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex h-screen w-full text-[var(--text)] antialiased overflow-hidden font-sans relative">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Modern Glass Topbar */}
        <header className="h-16 shrink-0 border-b border-[var(--border)] px-8 flex items-center justify-between glass-panel z-10">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
              <span className="font-semibold text-[var(--text)]">WareFlow</span>
              <span>/</span>
              <span className="font-mono text-[11px] px-2 py-0.5 rounded-md bg-[var(--accent-subtle)] text-[var(--accent)] font-medium border border-[var(--accent-border)]">
                v0.1.0 • Liquid Glass
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick Link / Status */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl glass-panel text-xs text-[var(--text-muted)]">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Operational</span>
            </div>

            {/* Theme Toggle Button */}
            <ThemeToggle />
          </div>
        </header>

        {/* Scrollable Page Body */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-7xl mx-auto">{children}</div>
        </div>
      </main>
    </div>
  );
}
