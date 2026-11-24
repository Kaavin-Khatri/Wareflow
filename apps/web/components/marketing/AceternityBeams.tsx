"use client";

import React from "react";

export function AceternityBeams() {
  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 pointer-events-none -z-10 select-none flex items-center justify-center overflow-visible"
    >
      {/* Soft, fully-feathered radial ambient aura with zero rectangular box edges */}
      <div
        className="absolute top-8 w-[85vw] max-w-[700px] h-[360px] rounded-full opacity-20 dark:opacity-25 blur-[100px] pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at center, var(--accent) 0%, rgba(168, 85, 247, 0.35) 45%, transparent 70%)",
        }}
      />
    </div>
  );
}

export default AceternityBeams;
