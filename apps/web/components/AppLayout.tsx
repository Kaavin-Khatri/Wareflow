"use client";

import React, { useState } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence } from "motion/react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { PageTransition } from "./motion/GlassMotion";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="flex h-screen w-full text-[var(--text)] antialiased overflow-hidden font-sans relative">
      {/* Sidebar Navigation (Desktop Persistent + Mobile Slide-Over Sheet) */}
      <Sidebar mobileOpen={mobileMenuOpen} onMobileClose={() => setMobileMenuOpen(false)} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        {/* Modern Frosted Glass Topbar */}
        <Topbar onMenuClick={() => setMobileMenuOpen(true)} />

        {/* Scrollable Page Body with Motion Page Transition */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto w-full">
            <AnimatePresence mode="wait">
              <PageTransition key={pathname}>{children}</PageTransition>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
