"use client";

import React from "react";
import Link from "next/link";
import { GlassCard } from "@/components/glass/GlassCard";
import { GlassButton } from "@/components/glass/GlassButton";
import { FadeIn } from "@/components/motion/GlassMotion";
import { Search, Home, Package, ArrowLeft } from "lucide-react";

export default function NotFoundPage() {
  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <FadeIn className="w-full max-w-lg">
        <GlassCard className="p-8 sm:p-10 text-center space-y-6 relative overflow-hidden border-[var(--border-strong)] shadow-2xl">
          {/* Ambient Glow Pill */}
          <div className="mx-auto inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--surface-hover)] border border-[var(--border)] text-xs font-mono font-semibold text-[var(--accent)] shadow-sm">
            <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
            HTTP 404 · ROUTE NOT FOUND
          </div>

          {/* Large Frosted Number Illustration */}
          <div className="relative py-4">
            <span className="text-7xl sm:text-8xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-[var(--text)] to-[var(--text-muted)] opacity-80 font-mono select-none">
              404
            </span>
          </div>

          {/* Heading and Domain-Rich Explanation */}
          <div className="space-y-2 max-w-sm mx-auto">
            <h1 className="text-xl sm:text-2xl font-bold text-[var(--text)] tracking-tight">
              Warehouse Bin Not Found
            </h1>
            <p className="text-xs sm:text-sm text-[var(--text-muted)] leading-relaxed">
              The catalog SKU, document route, or warehouse bin you requested does not exist or has been relocated in the system of record.
            </p>
          </div>

          {/* Navigation Action Buttons */}
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/dashboard" className="w-full sm:w-auto">
              <GlassButton variant="primary" className="w-full gap-2">
                <Home className="w-4 h-4" />
                <span>Return to Dashboard</span>
              </GlassButton>
            </Link>

            <Link href="/admin/products" className="w-full sm:w-auto">
              <GlassButton variant="secondary" className="w-full gap-2">
                <Package className="w-4 h-4" />
                <span>Browse Products</span>
              </GlassButton>
            </Link>
          </div>
        </GlassCard>
      </FadeIn>
    </div>
  );
}
