"use client";

import React from "react";
import { useTheme } from "./ThemeProvider";

export default function GradientBackdrop() {
  const { currentBackdrop, resolvedTheme, wallpaper, wallpaperOpacity, currentWallpaper, isLowPower } =
    useTheme();

  const orbs = resolvedTheme === "dark" ? currentBackdrop.darkOrbs : currentBackdrop.lightOrbs;
  const hasWallpaper = wallpaper !== "none" && !!currentWallpaper.imageSrc;

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none -z-10 overflow-hidden select-none transition-opacity duration-700"
    >
      {/* Base Solid Tint */}
      <div
        className="absolute inset-0 bg-[var(--bg)] transition-colors duration-500"
        style={{
          backgroundColor: resolvedTheme === "dark" ? orbs.baseTintDark : orbs.baseTintLight,
        }}
      />

      {/* Photographic Wallpaper Layer (Cozy Environments & Nature) */}
      {hasWallpaper && (
        <div className="absolute inset-0 overflow-hidden transition-opacity duration-700">
          <div
            className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-all duration-700 scale-105"
            style={{
              backgroundImage: `url(${currentWallpaper.imageSrc})`,
              opacity: (wallpaperOpacity || 35) / 100,
              filter: resolvedTheme === "dark" ? "brightness(0.85) contrast(1.05)" : "brightness(0.95)",
            }}
          />
          {/* Tint Overlay to maintain WCAG text legibility & smooth liquid glass specular contrast */}
          <div
            className={`absolute inset-0 transition-colors duration-500 ${
              resolvedTheme === "dark"
                ? "bg-gradient-to-b from-[#09090b]/40 via-[#09090b]/60 to-[#09090b]/80 mix-blend-multiply"
                : "bg-gradient-to-b from-white/50 via-white/70 to-white/85"
            }`}
          />
        </div>
      )}

      {/* Ambient Orb 1 — Top Left Primary Bloom */}
      <div
        className={`absolute -top-[20%] -left-[10%] w-[65vw] h-[65vw] max-w-[900px] max-h-[900px] rounded-full blur-[100px] sm:blur-[140px] animate-ambient-1 transition-all duration-700 will-change-transform ${
          hasWallpaper ? "opacity-40 dark:opacity-25" : "opacity-70 dark:opacity-40"
        }`}
        style={{
          background: orbs.orb1,
        }}
      />

      {/* Ambient Orb 2 — Top Right Secondary Bloom */}
      <div
        className={`absolute top-[10%] -right-[15%] w-[55vw] h-[55vw] max-w-[750px] max-h-[750px] rounded-full blur-[90px] sm:blur-[130px] animate-ambient-2 transition-all duration-700 will-change-transform ${
          hasWallpaper ? "opacity-30 dark:opacity-20" : "opacity-50 dark:opacity-30"
        }`}
        style={{
          background: orbs.orb2,
        }}
      />

      {/* Ambient Orb 3 — Bottom Center Horizon Bloom */}
      <div
        className={`absolute -bottom-[25%] left-[20%] w-[70vw] h-[50vw] max-w-[1000px] max-h-[600px] rounded-full blur-[110px] sm:blur-[160px] animate-ambient-3 transition-all duration-700 will-change-transform ${
          hasWallpaper ? "opacity-25 dark:opacity-18" : "opacity-45 dark:opacity-28"
        }`}
        style={{
          background: orbs.orb3,
        }}
      />

      {/* Ambient Orb 4 — Mid-Screen Dynamic Drifting Core */}
      {!isLowPower && (
        <div
          className={`absolute top-[45%] left-[10%] w-[40vw] h-[40vw] max-w-[500px] max-h-[500px] rounded-full blur-[100px] sm:blur-[140px] animate-ambient-2 transition-all duration-700 will-change-transform ${
            hasWallpaper ? "opacity-20 dark:opacity-12" : "opacity-35 dark:opacity-20"
          }`}
          style={{
            background: orbs.orb4,
          }}
        />
      )}

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
