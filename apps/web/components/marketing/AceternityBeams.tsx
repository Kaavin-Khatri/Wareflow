"use client";

import React from "react";

export function AceternityBeams() {
  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 overflow-hidden pointer-events-none -z-10 select-none"
    >
      {/* 1. Animated Spotlight Cone from Top Center */}
      <div
        className="absolute -top-[30%] left-1/2 -translate-x-1/2 w-[80vw] max-w-[1200px] h-[700px] opacity-30 dark:opacity-20 blur-[90px] will-change-transform"
        style={{
          background:
            "conic-gradient(from 90deg at 50% 0%, var(--accent) 0deg, rgba(168, 85, 247, 0.4) 60deg, transparent 120deg, transparent 240deg, rgba(168, 85, 247, 0.4) 300deg, var(--accent) 360deg)",
        }}
      />

      {/* 2. Radiant Luminous Grid Lines */}
      <div
        className="absolute inset-0 opacity-[0.07] dark:opacity-[0.12]"
        style={{
          backgroundImage: `
            linear-gradient(to right, var(--accent-border) 1px, transparent 1px),
            linear-gradient(to bottom, var(--accent-border) 1px, transparent 1px)
          `,
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse 65% 50% at 50% 30%, #000 30%, transparent 85%)",
          WebkitMaskImage: "radial-gradient(ellipse 65% 50% at 50% 30%, #000 30%, transparent 85%)",
        }}
      />

      {/* 3. Horizontal Drifting Scanning Laser Beam */}
      <div
        className="absolute top-[28%] left-0 right-0 h-[1px] opacity-40 dark:opacity-30 animate-pulse"
        style={{
          background: "linear-gradient(90deg, transparent 0%, var(--accent) 50%, transparent 100%)",
        }}
      />
    </div>
  );
}

export default AceternityBeams;
