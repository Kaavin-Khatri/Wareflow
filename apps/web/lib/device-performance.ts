"use client";

import { useSyncExternalStore, useEffect } from "react";

interface ExtendedNavigator extends Navigator {
  deviceMemory?: number;
}

/**
 * Checks whether the client environment should downgrade heavy specular refraction
 * and backdrop blurs to lightweight flat translucency.
 *
 * Triggers on:
 * 1. OS-level `prefers-reduced-transparency: reduce`
 * 2. Device memory < 4 GB (budget mobile hardware)
 * 3. CPU hardware concurrency <= 4 cores
 */
export function isLowPowerDevice(): boolean {
  if (typeof window === "undefined") return false;

  const prefersReducedTransparency = window.matchMedia(
    "(prefers-reduced-transparency: reduce)",
  ).matches;

  const nav = navigator as ExtendedNavigator;
  const lowMemory = typeof nav.deviceMemory === "number" && nav.deviceMemory < 4;
  const lowCores = typeof nav.hardwareConcurrency === "number" && nav.hardwareConcurrency <= 4;

  return prefersReducedTransparency || lowMemory || lowCores;
}

function subscribe(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("storage", callback);
  const mq = window.matchMedia("(prefers-reduced-transparency: reduce)");
  if (mq.addEventListener) {
    mq.addEventListener("change", callback);
    return () => {
      window.removeEventListener("storage", callback);
      mq.removeEventListener("change", callback);
    };
  }
  return () => {
    window.removeEventListener("storage", callback);
  };
}

export function useLowPowerGlass(): boolean {
  const isLowPower = useSyncExternalStore(subscribe, isLowPowerDevice, () => false);

  useEffect(() => {
    if (isLowPower) {
      document.documentElement.classList.add("low-power-glass");
    } else {
      document.documentElement.classList.remove("low-power-glass");
    }
  }, [isLowPower]);

  return isLowPower;
}
