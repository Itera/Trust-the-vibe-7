export interface Theme {
  id: string;
  label: string;
  emoji: string;
  dark: boolean; // true = light text needed
}

export const THEMES: Theme[] = [
  { id: "vaporwave",      label: "Vaporwave",      emoji: "🌸", dark: false },
  { id: "cyberpunk",      label: "Cyberpunk",      emoji: "⚡", dark: true  },
  { id: "cottagecore",    label: "Cottagecore",    emoji: "🌿", dark: false },
  { id: "corporate-hell", label: "Corporate Hell", emoji: "💼", dark: true  },
  { id: "aurora",         label: "Aurora",         emoji: "🌌", dark: true  },
  { id: "synthwave",      label: "Synthwave",      emoji: "🎹", dark: true  },
  { id: "lava",           label: "Lava Lamp",      emoji: "🔴", dark: true  },
  { id: "acid",           label: "Acid Trip",      emoji: "🍄", dark: false },
];

export function randomTheme(): Theme {
  return THEMES[Math.floor(Math.random() * THEMES.length)];
}
