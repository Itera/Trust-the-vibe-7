import type { CardKind, Language, PersonaKey } from "./types";

export interface PersonaTheme {
  accent: string;
  accentSoft: string;
  titleFont: string;
  bodyFont: string;
  gridTone: string; // report background tint
}

// Matches keys returned by /api/personas. Kept client-side for theming.
export const PERSONA_THEMES: Record<PersonaKey, PersonaTheme> = {
  consultant: {
    accent: "#1e3a5f",
    accentSoft: "#dbe6f3",
    titleFont: '"Times New Roman", Georgia, serif',
    bodyFont: '"Helvetica Neue", Arial, sans-serif',
    gridTone: "#f4f6f9",
  },
  stoic: {
    accent: "#2a2a2a",
    accentSoft: "#d6d1c4",
    titleFont: '"Times New Roman", Georgia, serif',
    bodyFont: 'Georgia, serif',
    gridTone: "#efeae0",
  },
  nordmann: {
    accent: "#c8102e",
    accentSoft: "#fde5e8",
    titleFont: '"Helvetica Neue", Arial, sans-serif',
    bodyFont: '"Helvetica Neue", Arial, sans-serif',
    gridTone: "#f7f7f5",
  },
  gremlin: {
    accent: "#ff6b35",
    accentSoft: "#ffe7d9",
    titleFont: '"Impact", "Haettenschweiler", sans-serif',
    bodyFont: '"Comic Sans MS", "Chalkboard SE", sans-serif',
    gridTone: "#fff1e6",
  },
};

export const ALL_CARD_KINDS: CardKind[] = [
  "peptalk",
  "video",
  "quote",
  "mood_board",
  "fact",
  "kpi",
  "advice",
  "image",
  "haiku",
  "horoscope",
  "recommendation",
  "playlist",
  "testimonial",
  "number_trivia",
];

export const DEFAULT_CARDS: CardKind[] = [
  "peptalk",
  "video",
  "quote",
  "fact",
  "kpi",
  "mood_board",
  "advice",
  "haiku",
  "recommendation",
];

export const QUICK_PICKS_EN = [
  { label: "Read the news", value: "I'm about to read the news and need motivation." },
  { label: "Play football", value: "Ragulan wants me to play football. Help." },
  { label: "Hackathon", value: "I'm at a hackathon with my department." },
  { label: "1:1 meeting", value: "I have a 1:1 with my manager in 10 minutes." },
  { label: "Gym", value: "I told myself I'd go to the gym today." },
  { label: "Fix a bug", value: "I need to debug something stupid." },
];

export const QUICK_PICKS_NO = [
  { label: "Les nyhetene", value: "Jeg skal lese nyhetene og trenger inspirasjon." },
  { label: "Spille fotball", value: "Ragulan vil jeg skal spille fotball. Hjelp." },
  { label: "Hackathon", value: "Jeg er på hackathon med avdelingen." },
  { label: "1:1 med sjefen", value: "Jeg har 1:1 med lederen om 10 minutter." },
  { label: "Treningssenter", value: "Jeg lovte meg selv å gå på trening i dag." },
  { label: "Fikse en bug", value: "Jeg skal feilsøke noe tåpelig." },
];

export const CARD_LABELS_EN: Record<CardKind, string> = {
  peptalk: "Executive Pep Talk",
  quote: "Quote",
  fact: "Did You Know",
  kpi: "Projected KPI",
  advice: "Advisory",
  image: "Visual Aid (Cat)",
  number_trivia: "Stat Sheet",
  haiku: "Haiku",
  horoscope: "Today's Horoscope",
  playlist: "Playlist",
  testimonial: "Testimonial",
  recommendation: "Pair With",
  video: "Motion Brief",
  mood_board: "Mood Board",
};

export const CARD_LABELS_NO: Record<CardKind, string> = {
  peptalk: "Ledelsens peptalk",
  quote: "Sitat",
  fact: "Visste du at",
  kpi: "Prognose-KPI",
  advice: "Anbefaling",
  image: "Visuelt bidrag (katt)",
  number_trivia: "Tallspalten",
  haiku: "Haiku",
  horoscope: "Dagens horoskop",
  playlist: "Spilleliste",
  testimonial: "Kundeutsagn",
  recommendation: "Kombiner med",
  video: "Videonotat",
  mood_board: "Stemningstavle",
};

export const cardLabel = (kind: CardKind, lang: Language): string => {
  const map = lang === "no" ? CARD_LABELS_NO : CARD_LABELS_EN;
  return map[kind] ?? kind;
};

export const LOADING_LINES_EN = [
  "Aligning synergies…",
  "Procuring feline imagery…",
  "Normalising motivational baseline…",
  "Extracting insights from thin air…",
  "Consulting the Itera archives…",
  "Interviewing anonymous sources…",
  "Benchmarking against industry vibes…",
];

export const LOADING_LINES_NO = [
  "Justerer synergier…",
  "Henter katteportretter…",
  "Normaliserer motivasjons­nivå…",
  "Trekker innsikter ut av luft…",
  "Konsulterer Itera-arkivet…",
  "Intervjuer anonyme kilder…",
  "Benchmarker mot bransjens vibber…",
];
