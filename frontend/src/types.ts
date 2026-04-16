export type Language = "en" | "no";
export type PersonaKey = "consultant" | "stoic" | "nordmann" | "gremlin";

export type CardKind =
  | "peptalk"
  | "quote"
  | "fact"
  | "kpi"
  | "advice"
  | "image"
  | "number_trivia"
  | "haiku"
  | "horoscope"
  | "playlist"
  | "testimonial"
  | "recommendation";

export interface Card {
  kind: CardKind;
  title: string;
  body: string;
  attribution?: string | null;
  image_url?: string | null;
  source?: string | null;
}

export interface MotivationPackage {
  task: string;
  persona: PersonaKey;
  language: Language;
  report_title: string;
  report_subtitle: string;
  cards: Card[];
}

export interface MotivationRequest {
  task: string;
  persona: PersonaKey;
  language: Language;
  seriousness: number;
  cards: CardKind[];
}

export interface PersonaSummary {
  key: PersonaKey;
  name: string;
  tagline: string;
  accent_color: string;
}
