"use client";

import React, { useSyncExternalStore } from "react";
import dynamic from "next/dynamic";
import { Hero3DFallback } from "./Hero3DFallback";

// Dynamic import with SSR disabled for optimal performance & zero hydration flash
const Hero3DCanvas = dynamic(() => import("./Hero3DCanvas"), {
  ssr: false,
  loading: () => <Hero3DFallback />,
});

function subscribe(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  mediaQuery.addEventListener("change", callback);
  return () => mediaQuery.removeEventListener("change", callback);
}

function getSnapshot() {
  if (typeof window === "undefined") return true;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function getServerSnapshot() {
  return true;
}

export function HeroScene() {
  const prefersReducedMotion = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  if (prefersReducedMotion) {
    return <Hero3DFallback />;
  }

  return <Hero3DCanvas />;
}

export default HeroScene;
