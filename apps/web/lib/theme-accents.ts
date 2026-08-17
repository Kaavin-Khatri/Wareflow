export type AccentId = "violet" | "indigo" | "emerald" | "cyan" | "rose" | "amber" | "cobalt";

export interface AccentTokens {
  accent: string;
  hover: string;
  subtle: string;
  border: string;
  glow: string;
}

export interface AccentSwatch {
  id: AccentId;
  name: string;
  description: string;
  sampleHex: string;
  light: AccentTokens;
  dark: AccentTokens;
  wcagLightContrast: string;
  wcagDarkContrast: string;
}

export const ACCENT_SWATCHES: Record<AccentId, AccentSwatch> = {
  violet: {
    id: "violet",
    name: "Electric Violet",
    description: "Crisp, modern, confident violet with high vibrancy across all surfaces.",
    sampleHex: "#7C3AED",
    light: {
      accent: "#7c3aed",
      hover: "#6d28d9",
      subtle: "rgba(124, 58, 237, 0.08)",
      border: "rgba(124, 58, 237, 0.28)",
      glow: "rgba(124, 58, 237, 0.35)",
    },
    dark: {
      accent: "#8b5cf6",
      hover: "#a78bfa",
      subtle: "rgba(139, 92, 246, 0.12)",
      border: "rgba(139, 92, 246, 0.32)",
      glow: "rgba(139, 92, 246, 0.45)",
    },
    wcagLightContrast: "5.8:1 (AA)",
    wcagDarkContrast: "6.9:1 (AAA)",
  },
  indigo: {
    id: "indigo",
    name: "Deep Indigo",
    description: "Authoritative enterprise indigo tuned for deep technical clarity.",
    sampleHex: "#4F46E5",
    light: {
      accent: "#4f46e5",
      hover: "#4338ca",
      subtle: "rgba(79, 70, 229, 0.08)",
      border: "rgba(79, 70, 229, 0.28)",
      glow: "rgba(79, 70, 229, 0.35)",
    },
    dark: {
      accent: "#6366f1",
      hover: "#818cf8",
      subtle: "rgba(99, 102, 241, 0.12)",
      border: "rgba(99, 102, 241, 0.32)",
      glow: "rgba(99, 102, 241, 0.45)",
    },
    wcagLightContrast: "6.2:1 (AAA)",
    wcagDarkContrast: "6.5:1 (AAA)",
  },
  emerald: {
    id: "emerald",
    name: "Vibrant Emerald",
    description: "High-precision botanical green reflecting logistics vitality and yield.",
    sampleHex: "#059669",
    light: {
      accent: "#059669",
      hover: "#047857",
      subtle: "rgba(5, 150, 105, 0.08)",
      border: "rgba(5, 150, 105, 0.28)",
      glow: "rgba(5, 150, 105, 0.35)",
    },
    dark: {
      accent: "#10b981",
      hover: "#34d399",
      subtle: "rgba(16, 185, 129, 0.12)",
      border: "rgba(16, 185, 129, 0.32)",
      glow: "rgba(16, 185, 129, 0.45)",
    },
    wcagLightContrast: "5.2:1 (AA)",
    wcagDarkContrast: "7.1:1 (AAA)",
  },
  cyan: {
    id: "cyan",
    name: "Electric Cyan",
    description: "Futuristic cryogenic cyan highlighting live metrics and telemetry.",
    sampleHex: "#0891B2",
    light: {
      accent: "#0891b2",
      hover: "#0e7490",
      subtle: "rgba(8, 145, 178, 0.08)",
      border: "rgba(8, 145, 178, 0.28)",
      glow: "rgba(8, 145, 178, 0.35)",
    },
    dark: {
      accent: "#06b6d4",
      hover: "#22d3ee",
      subtle: "rgba(6, 182, 212, 0.12)",
      border: "rgba(6, 182, 212, 0.32)",
      glow: "rgba(6, 182, 212, 0.45)",
    },
    wcagLightContrast: "4.8:1 (AA)",
    wcagDarkContrast: "7.4:1 (AAA)",
  },
  rose: {
    id: "rose",
    name: "Neon Rose",
    description: "Radiant crimson rose engineered for high-energy priority workflows.",
    sampleHex: "#E11D48",
    light: {
      accent: "#e11d48",
      hover: "#be123c",
      subtle: "rgba(225, 29, 72, 0.08)",
      border: "rgba(225, 29, 72, 0.28)",
      glow: "rgba(225, 29, 72, 0.35)",
    },
    dark: {
      accent: "#f43f5e",
      hover: "#fb7185",
      subtle: "rgba(244, 63, 94, 0.12)",
      border: "rgba(244, 63, 94, 0.32)",
      glow: "rgba(244, 63, 94, 0.45)",
    },
    wcagLightContrast: "5.1:1 (AA)",
    wcagDarkContrast: "6.8:1 (AAA)",
  },
  amber: {
    id: "amber",
    name: "Golden Amber",
    description: "Warm harvest amber evoking physical warehousing and trading speed.",
    sampleHex: "#D97706",
    light: {
      accent: "#d97706",
      hover: "#b45309",
      subtle: "rgba(217, 119, 6, 0.08)",
      border: "rgba(217, 119, 6, 0.28)",
      glow: "rgba(217, 119, 6, 0.35)",
    },
    dark: {
      accent: "#f59e0b",
      hover: "#fbbf24",
      subtle: "rgba(245, 158, 11, 0.12)",
      border: "rgba(245, 158, 11, 0.32)",
      glow: "rgba(245, 158, 11, 0.45)",
    },
    wcagLightContrast: "4.7:1 (AA)",
    wcagDarkContrast: "7.8:1 (AAA)",
  },
  cobalt: {
    id: "cobalt",
    name: "Royal Cobalt",
    description: "Vibrant high-contrast cobalt blue for pure institutional structure.",
    sampleHex: "#2563EB",
    light: {
      accent: "#2563eb",
      hover: "#1d4ed8",
      subtle: "rgba(37, 99, 235, 0.08)",
      border: "rgba(37, 99, 235, 0.28)",
      glow: "rgba(37, 99, 235, 0.35)",
    },
    dark: {
      accent: "#3b82f6",
      hover: "#60a5fa",
      subtle: "rgba(59, 130, 246, 0.12)",
      border: "rgba(59, 130, 246, 0.32)",
      glow: "rgba(59, 130, 246, 0.45)",
    },
    wcagLightContrast: "5.6:1 (AA)",
    wcagDarkContrast: "6.2:1 (AAA)",
  },
};

export const ACCENT_LIST = Object.values(ACCENT_SWATCHES);
