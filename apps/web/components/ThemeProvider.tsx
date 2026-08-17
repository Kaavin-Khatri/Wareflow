"use client";

import React, { createContext, useContext, useEffect, useSyncExternalStore } from "react";
import { AccentId, ACCENT_SWATCHES, ACCENT_LIST, AccentSwatch } from "@/lib/theme-accents";
import { apiClient } from "@/lib/api-client";

type Theme = "light" | "dark" | "system";
type ResolvedTheme = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  accent: AccentId;
  currentSwatch: AccentSwatch;
  availableAccents: AccentSwatch[];
  setTheme: (theme: Theme) => void;
  setAccent: (accent: AccentId) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = "wareflow-theme";
const ACCENT_STORAGE_KEY = "wareflow-accent";

// Helper for subscribing to localStorage and system media queries
function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  mediaQuery.addEventListener("change", callback);
  return () => {
    window.removeEventListener("storage", callback);
    mediaQuery.removeEventListener("change", callback);
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

function getSystemPrefersDark(): boolean {
  if (typeof window === "undefined") return true;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useSyncExternalStore(subscribe, getStoredTheme, () => "system" as Theme);
  const accent = useSyncExternalStore(subscribe, getStoredAccent, () => "violet" as AccentId);
  const systemDark = useSyncExternalStore(subscribe, getSystemPrefersDark, () => true);

  const resolvedTheme: ResolvedTheme = theme === "system" ? (systemDark ? "dark" : "light") : theme;

  const currentSwatch = ACCENT_SWATCHES[accent] || ACCENT_SWATCHES.violet;

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

  const toggleTheme = () => {
    const next = resolvedTheme === "dark" ? "light" : "dark";
    setTheme(next);
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        resolvedTheme,
        accent,
        currentSwatch,
        availableAccents: ACCENT_LIST,
        setTheme,
        setAccent,
        toggleTheme,
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
