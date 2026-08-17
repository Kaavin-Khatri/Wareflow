"use client";

import React, { createContext, useContext } from "react";
import type { Transition } from "motion/react";

export interface MotionPresets {
  snappy: Transition;
  gentle: Transition;
  bouncy: Transition;
  glassMorph: Transition;
  smoothFade: Transition;
}

export const SPRING_PRESETS: MotionPresets = {
  snappy: { type: "spring", stiffness: 450, damping: 30 },
  gentle: { type: "spring", stiffness: 220, damping: 24 },
  bouncy: { type: "spring", stiffness: 550, damping: 18 },
  glassMorph: { type: "spring", stiffness: 380, damping: 26, mass: 0.8 },
  smoothFade: { duration: 0.25, ease: [0.16, 1, 0.3, 1] },
};

const MotionContext = createContext<MotionPresets>(SPRING_PRESETS);

export function MotionProvider({ children }: { children: React.ReactNode }) {
  return <MotionContext.Provider value={SPRING_PRESETS}>{children}</MotionContext.Provider>;
}

export function useMotionPresets(): MotionPresets {
  return useContext(MotionContext);
}
