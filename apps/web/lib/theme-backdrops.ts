export type BackdropStyleId =
  | "midnight"
  | "cozy-amber"
  | "nordic-aurora"
  | "lavender-dusk"
  | "ocean-calm"
  | "warm-cafe"
  | "minimal-pure";

export interface BackdropOrbConfig {
  orb1: string; // Top Left Primary Bloom
  orb2: string; // Top Right Secondary Bloom
  orb3: string; // Bottom Center Horizon Bloom
  orb4: string; // Mid-Screen Drifting Core
  baseTintDark?: string;
  baseTintLight?: string;
}

export interface BackdropPreset {
  id: BackdropStyleId;
  name: string;
  moodTag: "Signature" | "Cozy" | "Relaxing" | "Focus" | "Minimal";
  description: string;
  previewGradient: string;
  darkOrbs: BackdropOrbConfig;
  lightOrbs: BackdropOrbConfig;
}

export const BACKDROP_PRESETS: Record<BackdropStyleId, BackdropPreset> = {
  midnight: {
    id: "midnight",
    name: "Midnight Aurora",
    moodTag: "Signature",
    description: "Deep obsidian cosmos with floating electric violet and indigo ambient orbs.",
    previewGradient: "linear-gradient(135deg, #09090b 0%, #1e1b4b 50%, #09090b 100%)",
    darkOrbs: {
      orb1: "radial-gradient(circle, var(--accent, #8b5cf6) 0%, rgba(124, 58, 237, 0.22) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(168, 85, 247, 0.7) 0%, rgba(147, 51, 234, 0.18) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, var(--accent, #8b5cf6) 0%, rgba(124, 58, 237, 0.15) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(99, 102, 241, 0.6) 0%, rgba(124, 58, 237, 0.12) 60%, transparent 80%)",
      baseTintDark: "#09090b",
    },
    lightOrbs: {
      orb1: "radial-gradient(circle, var(--accent, #7c3aed) 0%, rgba(124, 58, 237, 0.12) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(168, 85, 247, 0.4) 0%, rgba(147, 51, 234, 0.08) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, var(--accent, #7c3aed) 0%, rgba(124, 58, 237, 0.08) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(99, 102, 241, 0.35) 0%, rgba(124, 58, 237, 0.06) 60%, transparent 80%)",
      baseTintLight: "#fcfcfd",
    },
  },
  "cozy-amber": {
    id: "cozy-amber",
    name: "Cozy Sunset & Hearth",
    moodTag: "Cozy",
    description: "Warm amber glow, terracotta, and soft golden honey tones for relaxed evening work.",
    previewGradient: "linear-gradient(135deg, #1c1107 0%, #78350f 50%, #1c0e04 100%)",
    darkOrbs: {
      orb1: "radial-gradient(circle, rgba(245, 158, 11, 0.75) 0%, rgba(217, 119, 6, 0.25) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(234, 88, 12, 0.65) 0%, rgba(194, 65, 12, 0.18) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(251, 191, 36, 0.6) 0%, rgba(217, 119, 6, 0.15) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(249, 115, 22, 0.5) 0%, rgba(234, 88, 12, 0.12) 60%, transparent 80%)",
      baseTintDark: "#0d0905",
    },
    lightOrbs: {
      orb1: "radial-gradient(circle, rgba(245, 158, 11, 0.35) 0%, rgba(217, 119, 6, 0.1) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(234, 88, 12, 0.25) 0%, rgba(194, 65, 12, 0.06) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(251, 191, 36, 0.3) 0%, rgba(217, 119, 6, 0.08) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(249, 115, 22, 0.2) 0%, rgba(234, 88, 12, 0.05) 60%, transparent 80%)",
      baseTintLight: "#fffbf5",
    },
  },
  "nordic-aurora": {
    id: "nordic-aurora",
    name: "Emerald Borealis",
    moodTag: "Relaxing",
    description: "Calming botanical emerald, soft seafoam, and deep pine borealis ribbons.",
    previewGradient: "linear-gradient(135deg, #021a12 0%, #065f46 50%, #022c22 100%)",
    darkOrbs: {
      orb1: "radial-gradient(circle, rgba(16, 185, 129, 0.7) 0%, rgba(5, 150, 105, 0.22) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(20, 184, 166, 0.6) 0%, rgba(13, 148, 136, 0.18) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(52, 211, 153, 0.55) 0%, rgba(16, 185, 129, 0.15) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(6, 182, 212, 0.5) 0%, rgba(20, 184, 166, 0.12) 60%, transparent 80%)",
      baseTintDark: "#040d0a",
    },
    lightOrbs: {
      orb1: "radial-gradient(circle, rgba(16, 185, 129, 0.35) 0%, rgba(5, 150, 105, 0.1) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(20, 184, 166, 0.25) 0%, rgba(13, 148, 136, 0.07) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(52, 211, 153, 0.25) 0%, rgba(16, 185, 129, 0.06) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(6, 182, 212, 0.2) 0%, rgba(20, 184, 166, 0.05) 60%, transparent 80%)",
      baseTintLight: "#f4fdf8",
    },
  },
  "lavender-dusk": {
    id: "lavender-dusk",
    name: "Lavender Twilight",
    moodTag: "Relaxing",
    description: "Dreamy pastel lavender, dusk plum, and soft ethereal mist for calm mental clarity.",
    previewGradient: "linear-gradient(135deg, #170d26 0%, #4c1d95 50%, #200f36 100%)",
    darkOrbs: {
      orb1: "radial-gradient(circle, rgba(192, 132, 252, 0.7) 0%, rgba(147, 51, 234, 0.22) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(244, 114, 182, 0.6) 0%, rgba(219, 39, 119, 0.18) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(168, 85, 247, 0.55) 0%, rgba(147, 51, 234, 0.15) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(232, 121, 249, 0.5) 0%, rgba(192, 132, 252, 0.12) 60%, transparent 80%)",
      baseTintDark: "#0b0612",
    },
    lightOrbs: {
      orb1: "radial-gradient(circle, rgba(192, 132, 252, 0.35) 0%, rgba(147, 51, 234, 0.08) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(244, 114, 182, 0.25) 0%, rgba(219, 39, 119, 0.06) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(168, 85, 247, 0.25) 0%, rgba(147, 51, 234, 0.06) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(232, 121, 249, 0.2) 0%, rgba(192, 132, 252, 0.05) 60%, transparent 80%)",
      baseTintLight: "#fbf8ff",
    },
  },
  "ocean-calm": {
    id: "ocean-calm",
    name: "Tranquil Pacific",
    moodTag: "Focus",
    description: "Deep oceanic navy with soothing cyan waves and aquatic luminescence.",
    previewGradient: "linear-gradient(135deg, #031526 0%, #0369a1 50%, #082f49 100%)",
    darkOrbs: {
      orb1: "radial-gradient(circle, rgba(56, 189, 248, 0.7) 0%, rgba(2, 132, 199, 0.22) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(6, 182, 212, 0.6) 0%, rgba(8, 145, 178, 0.18) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(59, 130, 246, 0.55) 0%, rgba(37, 99, 235, 0.15) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(14, 165, 233, 0.5) 0%, rgba(2, 132, 199, 0.12) 60%, transparent 80%)",
      baseTintDark: "#030a12",
    },
    lightOrbs: {
      orb1: "radial-gradient(circle, rgba(56, 189, 248, 0.35) 0%, rgba(2, 132, 199, 0.08) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(6, 182, 212, 0.25) 0%, rgba(8, 145, 178, 0.06) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(59, 130, 246, 0.25) 0%, rgba(37, 99, 235, 0.06) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(14, 165, 233, 0.2) 0%, rgba(2, 132, 199, 0.05) 60%, transparent 80%)",
      baseTintLight: "#f0f9ff",
    },
  },
  "warm-cafe": {
    id: "warm-cafe",
    name: "Warm Espresso & Hearth",
    moodTag: "Cozy",
    description: "Rich roasted mocha, caramel amber, and warm diffused studio lighting.",
    previewGradient: "linear-gradient(135deg, #1f140e 0%, #543310 50%, #1a0f08 100%)",
    darkOrbs: {
      orb1: "radial-gradient(circle, rgba(217, 119, 6, 0.7) 0%, rgba(180, 83, 9, 0.22) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(251, 191, 36, 0.55) 0%, rgba(217, 119, 6, 0.18) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(161, 98, 7, 0.6) 0%, rgba(113, 63, 18, 0.15) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(245, 158, 11, 0.45) 0%, rgba(180, 83, 9, 0.12) 60%, transparent 80%)",
      baseTintDark: "#0c0805",
    },
    lightOrbs: {
      orb1: "radial-gradient(circle, rgba(217, 119, 6, 0.3) 0%, rgba(180, 83, 9, 0.08) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(251, 191, 36, 0.25) 0%, rgba(217, 119, 6, 0.06) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(161, 98, 7, 0.25) 0%, rgba(113, 63, 18, 0.06) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(245, 158, 11, 0.2) 0%, rgba(180, 83, 9, 0.05) 60%, transparent 80%)",
      baseTintLight: "#fffcf7",
    },
  },
  "minimal-pure": {
    id: "minimal-pure",
    name: "Minimalist Slate",
    moodTag: "Minimal",
    description: "Ultra-pure distraction-free obsidian with subtle monochromatic frosted reflections.",
    previewGradient: "linear-gradient(135deg, #09090b 0%, #18181b 50%, #09090b 100%)",
    darkOrbs: {
      orb1: "radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, rgba(161, 161, 170, 0.04) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(212, 212, 216, 0.06) 0%, rgba(113, 113, 122, 0.03) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(255, 255, 255, 0.07) 0%, rgba(161, 161, 170, 0.03) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(228, 228, 231, 0.05) 0%, rgba(113, 113, 122, 0.02) 60%, transparent 80%)",
      baseTintDark: "#09090b",
    },
    lightOrbs: {
      orb1: "radial-gradient(circle, rgba(0, 0, 0, 0.04) 0%, rgba(0, 0, 0, 0.02) 50%, transparent 75%)",
      orb2: "radial-gradient(circle, rgba(0, 0, 0, 0.03) 0%, rgba(0, 0, 0, 0.015) 45%, transparent 70%)",
      orb3: "radial-gradient(ellipse, rgba(0, 0, 0, 0.03) 0%, rgba(0, 0, 0, 0.015) 55%, transparent 80%)",
      orb4: "radial-gradient(circle, rgba(0, 0, 0, 0.02) 0%, rgba(0, 0, 0, 0.01) 60%, transparent 80%)",
      baseTintLight: "#f8f9fa",
    },
  },
};

export const BACKDROP_LIST: BackdropPreset[] = Object.values(BACKDROP_PRESETS);

export type WallpaperId =
  | "none"
  | "cozy-cabin"
  | "misty-forest"
  | "rainy-lofi"
  | "zen-garden"
  | "aurora-lake";

export interface WallpaperPreset {
  id: WallpaperId;
  name: string;
  category: "None" | "Cozy Interiors" | "Nature & Mist" | "Tranquility & Zen" | "Cosmic Night";
  description: string;
  imageSrc: string;
  defaultOverlayOpacity: number;
}

export const WALLPAPER_PRESETS: Record<WallpaperId, WallpaperPreset> = {
  none: {
    id: "none",
    name: "None (Ambient Atmosphere Only)",
    category: "None",
    description: "Pure liquid glass backdrop with floating dynamic ambient orbs and no photo wallpaper.",
    imageSrc: "",
    defaultOverlayOpacity: 0,
  },
  "cozy-cabin": {
    id: "cozy-cabin",
    name: "Cozy Mountain Cabin & Hearth",
    category: "Cozy Interiors",
    description: "Warm glowing stone fireplace, timber lodge, rain outside the window, and serene twilight ambiance.",
    imageSrc: "/backgrounds/cozy-cabin.jpg",
    defaultOverlayOpacity: 0.35,
  },
  "misty-forest": {
    id: "misty-forest",
    name: "Misty Evergreen Pine Forest",
    category: "Nature & Mist",
    description: "Peaceful morning fog through towering pine canopies with golden sun rays and lush ferns.",
    imageSrc: "/backgrounds/misty-forest.jpg",
    defaultOverlayOpacity: 0.3,
  },
  "rainy-lofi": {
    id: "rainy-lofi",
    name: "Rainy Lofi Study & City Bokeh",
    category: "Cozy Interiors",
    description: "Relaxing evening study with rain streaks on glass, warm desk lamp glow, and city bokeh.",
    imageSrc: "/backgrounds/rainy-lofi.jpg",
    defaultOverlayOpacity: 0.35,
  },
  "zen-garden": {
    id: "zen-garden",
    name: "Japanese Zen Bamboo Garden",
    category: "Tranquility & Zen",
    description: "Serene raked gravel, mossy stepping stones, tranquil water fountain, and gentle bamboo mist.",
    imageSrc: "/backgrounds/zen-garden.jpg",
    defaultOverlayOpacity: 0.3,
  },
  "aurora-lake": {
    id: "aurora-lake",
    name: "Alpine Lake & Aurora Borealis",
    category: "Cosmic Night",
    description: "Pristine mountain lake reflecting snow peaks, starry galaxy, and shimmering northern lights.",
    imageSrc: "/backgrounds/aurora-lake.jpg",
    defaultOverlayOpacity: 0.35,
  },
};

export const WALLPAPER_LIST: WallpaperPreset[] = Object.values(WALLPAPER_PRESETS);

