"use client";

import React from "react";

export default function GradientBackdrop() {
  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none -z-10 overflow-hidden select-none transition-opacity duration-700"
    >
      {/* Base Solid Tint */}
      <div className="absolute inset-0 bg-[var(--bg)] transition-colors duration-500" />

      {/* Ambient Orb 1 — Top Left Primary Bloom */}
      <div
        className="absolute -top-[20%] -left-[10%] w-[65vw] h-[65vw] max-w-[900px] max-h-[900px] rounded-full blur-[100px] sm:blur-[140px] opacity-70 dark:opacity-40 animate-ambient-1 transition-all duration-700 will-change-transform"
        style={{
          background:
            "radial-gradient(circle, var(--accent) 0%, rgba(124, 58, 237, 0.15) 50%, transparent 75%)",
        }}
      />

      {/* Ambient Orb 2 — Top Right Secondary Bloom */}
      <div
        className="absolute top-[10%] -right-[15%] w-[55vw] h-[55vw] max-w-[750px] max-h-[750px] rounded-full blur-[90px] sm:blur-[130px] opacity-50 dark:opacity-30 animate-ambient-2 transition-all duration-700 will-change-transform"
        style={{
          background:
            "radial-gradient(circle, rgba(168, 85, 247, 0.8) 0%, rgba(147, 51, 234, 0.12) 45%, transparent 70%)",
        }}
      />

      {/* Ambient Orb 3 — Bottom Center Subtle Horizon Bloom */}
      <div
        className="absolute -bottom-[25%] left-[20%] w-[70vw] h-[50vw] max-w-[1000px] max-h-[600px] rounded-full blur-[110px] sm:blur-[160px] opacity-40 dark:opacity-25 animate-ambient-3 transition-all duration-700 will-change-transform"
        style={{
          background:
            "radial-gradient(ellipse, var(--accent) 0%, rgba(124, 58, 237, 0.08) 55%, transparent 80%)",
        }}
      />

      {/* Subtle Noise / Grain Overlay for Physical Depth & Anti-Banding */}
      <div
        className="absolute inset-0 opacity-[0.025] dark:opacity-[0.035] mix-blend-overlay pointer-events-none"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />
    </div>
  );
}
