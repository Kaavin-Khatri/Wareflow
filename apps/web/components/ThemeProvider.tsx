"use client";

import React, { createContext, useContext, useEffect, useSyncExternalStore } from "react";
import { AccentId, ACCENT_SWATCHES, ACCENT_LIST, AccentSwatch } from "@/lib/theme-accents";
import {
  BackdropStyleId,
  BACKDROP_PRESETS,
  BACKDROP_LIST,
  BackdropPreset,
  WallpaperId,
  WALLPAPER_PRESETS,
  WALLPAPER_LIST,
  WallpaperPreset,
} from "@/lib/theme-backdrops";
import { apiClient, getAuthToken } from "@/lib/api-client";
import { isLowPowerDevice } from "@/lib/device-performance";

type Theme = "light" | "dark" | "system";
type ResolvedTheme = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  accent: AccentId;
  currentSwatch: AccentSwatch;
  availableAccents: AccentSwatch[];
  backdropStyle: BackdropStyleId;
  currentBackdrop: BackdropPreset;
  availableBackdrops: BackdropPreset[];
  wallpaper: WallpaperId;
  wallpaperOpacity: number;
  currentWallpaper: WallpaperPreset;
  availableWallpapers: WallpaperPreset[];
  isLowPower: boolean;
  setTheme: (theme: Theme) => void;
  setAccent: (accent: AccentId) => void;
  setBackdropStyle: (backdrop: BackdropStyleId) => void;
  setWallpaper: (wallpaper: WallpaperId) => void;
  setWallpaperOpacity: (opacity: number) => void;
  toggleTheme: () => void;
  toggleLowPower: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = "wareflow-theme";
const ACCENT_STORAGE_KEY = "wareflow-accent";
const BACKDROP_STORAGE_KEY = "wareflow-backdrop";
const WALLPAPER_STORAGE_KEY = "wareflow-wallpaper";
const WALLPAPER_OPACITY_STORAGE_KEY = "wareflow-wallpaper-opacity";
const LOW_POWER_STORAGE_KEY = "wareflow-low-power";

// Helper for subscribing to localStorage and system media queries
function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  const colorSchemeMq = window.matchMedia("(prefers-color-scheme: dark)");
  const transparencyMq = window.matchMedia("(prefers-reduced-transparency: reduce)");

  colorSchemeMq.addEventListener("change", callback);
  transparencyMq.addEventListener("change", callback);

  return () => {
    window.removeEventListener("storage", callback);
    colorSchemeMq.removeEventListener("change", callback);
    transparencyMq.removeEventListener("change", callback);
  };
}

function getStoredTheme(): Theme {
  if (typeof window === "undefined") return "system";
  try {
    return (localStorage.getItem(THEME_STORAGE_KEY) as Theme) || "system";
  } catch {
    return "system";
  }
}

function getStoredAccent(): AccentId {
  if (typeof window === "undefined") return "violet";
  try {
    const saved = localStorage.getItem(ACCENT_STORAGE_KEY) as AccentId;
    return saved && ACCENT_SWATCHES[saved] ? saved : "violet";
  } catch {
    return "violet";
  }
}

function getStoredBackdrop(): BackdropStyleId {
  if (typeof window === "undefined") return "midnight";
  try {
    const saved = localStorage.getItem(BACKDROP_STORAGE_KEY) as BackdropStyleId;
    return saved && BACKDROP_PRESETS[saved] ? saved : "midnight";
  } catch {
    return "midnight";
  }
}

function getStoredWallpaper(): WallpaperId {
  if (typeof window === "undefined") return "none";
  try {
    const saved = localStorage.getItem(WALLPAPER_STORAGE_KEY) as WallpaperId;
    return saved && WALLPAPER_PRESETS[saved] ? saved : "none";
  } catch {
    return "none";
  }
}

function getStoredWallpaperOpacity(): number {
  if (typeof window === "undefined") return 35;
  try {
    const saved = localStorage.getItem(WALLPAPER_OPACITY_STORAGE_KEY);
    if (saved !== null) {
      const parsed = Number(saved);
      if (!isNaN(parsed) && parsed >= 0 && parsed <= 100) return parsed;
    }
    return 35;
  } catch {
    return 35;
  }
}

function getStoredLowPower(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const saved = localStorage.getItem(LOW_POWER_STORAGE_KEY);
    if (saved !== null) return saved === "true";
    return isLowPowerDevice();
  } catch {
    return false;
  }
}

function getSystemPrefersDark(): boolean {
  if (typeof window === "undefined") return true;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useSyncExternalStore(subscribe, getStoredTheme, () => "system" as Theme);
  const accent = useSyncExternalStore(subscribe, getStoredAccent, () => "violet" as AccentId);
  const backdropStyle = useSyncExternalStore(
    subscribe,
    getStoredBackdrop,
    () => "midnight" as BackdropStyleId
  );
  const wallpaper = useSyncExternalStore(
    subscribe,
    getStoredWallpaper,
    () => "none" as WallpaperId
  );
  const wallpaperOpacity = useSyncExternalStore(
    subscribe,
    getStoredWallpaperOpacity,
    () => 35
  );
  const systemDark = useSyncExternalStore(subscribe, getSystemPrefersDark, () => true);
  const isLowPower = useSyncExternalStore(subscribe, getStoredLowPower, () => false);

  const resolvedTheme: ResolvedTheme = theme === "system" ? (systemDark ? "dark" : "light") : theme;

  const currentSwatch = ACCENT_SWATCHES[accent] || ACCENT_SWATCHES.violet;
  const currentBackdrop = BACKDROP_PRESETS[backdropStyle] || BACKDROP_PRESETS.midnight;
  const currentWallpaper = WALLPAPER_PRESETS[wallpaper] || WALLPAPER_PRESETS.none;

  // Synchronize low-power class on root DOM
  useEffect(() => {
    if (isLowPower) {
      document.documentElement.classList.add("low-power-glass");
    } else {
      document.documentElement.classList.remove("low-power-glass");
    }
  }, [isLowPower]);

  // Apply dark/light class and colorScheme to root DOM
  useEffect(() => {
    const root = document.documentElement;
    if (resolvedTheme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    root.style.colorScheme = resolvedTheme;
  }, [resolvedTheme]);

  // Apply dynamic accent CSS custom properties to root DOM
  useEffect(() => {
    const root = document.documentElement;
    const tokens = resolvedTheme === "dark" ? currentSwatch.dark : currentSwatch.light;

    root.style.setProperty("--accent", tokens.accent);
    root.style.setProperty("--accent-hover", tokens.hover);
    root.style.setProperty("--accent-subtle", tokens.subtle);
    root.style.setProperty("--accent-border", tokens.border);
    root.style.setProperty("--accent-glow", tokens.glow);
  }, [resolvedTheme, currentSwatch]);

  const syncBackendPreferences = async (newTheme: Theme, newAccent: AccentId) => {
    if (!(await getAuthToken())) return;
    try {
      await apiClient.patch("/profiles/preferences", {
        theme_preference: newTheme,
        accent_color: newAccent,
      });
    } catch {
      // Gracefully silent if user is unauthenticated
    }
  };

  const setTheme = (newTheme: Theme) => {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, newTheme);
      window.dispatchEvent(new Event("storage"));
      void syncBackendPreferences(newTheme, accent);
    } catch {
      // LocalStorage access may fail in sandboxed iframes
    }
  };

  const setAccent = (newAccent: AccentId) => {
    try {
      localStorage.setItem(ACCENT_STORAGE_KEY, newAccent);
      window.dispatchEvent(new Event("storage"));
      void syncBackendPreferences(theme, newAccent);
    } catch {
      // LocalStorage access may fail in sandboxed iframes
    }
  };

  const setBackdropStyle = (newBackdrop: BackdropStyleId) => {
    try {
      localStorage.setItem(BACKDROP_STORAGE_KEY, newBackdrop);
      window.dispatchEvent(new Event("storage"));
    } catch {
      // LocalStorage access fallback
    }
  };

  const setWallpaper = (newWallpaper: WallpaperId) => {
    try {
      localStorage.setItem(WALLPAPER_STORAGE_KEY, newWallpaper);
      window.dispatchEvent(new Event("storage"));
    } catch {
      // LocalStorage access fallback
    }
  };

  const setWallpaperOpacity = (newOpacity: number) => {
    try {
      const clamped = Math.max(0, Math.min(100, Math.round(newOpacity)));
      localStorage.setItem(WALLPAPER_OPACITY_STORAGE_KEY, String(clamped));
      window.dispatchEvent(new Event("storage"));
    } catch {
      // LocalStorage access fallback
    }
  };

  const toggleTheme = () => {
    const next = resolvedTheme === "dark" ? "light" : "dark";
    setTheme(next);
  };

  const toggleLowPower = () => {
    try {
      const next = !isLowPower;
      localStorage.setItem(LOW_POWER_STORAGE_KEY, String(next));
      window.dispatchEvent(new Event("storage"));
    } catch {
      // LocalStorage access fallback
    }
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        resolvedTheme,
        accent,
        currentSwatch,
        availableAccents: ACCENT_LIST,
        backdropStyle,
        currentBackdrop,
        availableBackdrops: BACKDROP_LIST,
        wallpaper,
        wallpaperOpacity,
        currentWallpaper,
        availableWallpapers: WALLPAPER_LIST,
        isLowPower,
        setTheme,
        setAccent,
        setBackdropStyle,
        setWallpaper,
        setWallpaperOpacity,
        toggleTheme,
        toggleLowPower,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

export default ThemeProvider;
