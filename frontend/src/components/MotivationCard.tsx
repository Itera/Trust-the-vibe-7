import type { Card } from "../types";

interface Props {
  card: Card;
  index?: number;
  darkMode?: boolean;
}

// Map card kinds to bento grid column spans (md:col-span-N)
const BENTO_SPANS: Record<string, string> = {
  peptalk:         "md:col-span-8",
  quote:           "md:col-span-8",
  fact:            "md:col-span-4",
  kpi:             "md:col-span-4",
  advice:          "md:col-span-7",
  image:           "md:col-span-5",
  number_trivia:   "md:col-span-5",
  haiku:           "md:col-span-4",
  horoscope:       "md:col-span-5",
  playlist:        "md:col-span-7",
  testimonial:     "md:col-span-6",
  recommendation:  "md:col-span-6",
  meme:            "md:col-span-12",
};

// Cycle through accent text colors for dark mode cards
const DARK_ACCENT_TEXT = [
  "text-secondary",
  "text-primary",
  "text-tertiary",
  "text-secondary",
] as const;

const DARK_ATTRIBUTION_TEXT = [
  "text-secondary",
  "text-primary",
  "text-tertiary",
  "text-secondary",
] as const;
const DARK_BG_CLASSES = [
  "bg-surface-container-high border-l-8 border-secondary",
  "bg-surface-container-lowest border-4 border-primary",
  "bg-surface-container-high border-t-4 border-tertiary",
  "bg-surface-container border-l-8 border-primary",
];

// Light mode card backgrounds cycle
const LIGHT_CARD_STYLES = [
  { bg: "bg-primary text-white",                            hero: true },
  { bg: "bg-tertiary-container text-on-tertiary-container", hero: false },
  { bg: "bg-secondary text-on-secondary",                   hero: false },
  { bg: "bg-on-surface text-white border-8 border-tertiary-container", hero: false },
  { bg: "bg-white border border-[var(--t-outline)]/20",     hero: false },
];

export default function MotivationCard({ card, index = 0, darkMode = false }: Props) {
  const colSpan = BENTO_SPANS[card.kind] ?? "md:col-span-6";

  if (darkMode) {
    const accentText = DARK_ACCENT_TEXT[index % DARK_ACCENT_TEXT.length];
    const attrText   = DARK_ATTRIBUTION_TEXT[index % DARK_ATTRIBUTION_TEXT.length];
    const bgClass = DARK_BG_CLASSES[index % DARK_BG_CLASSES.length];

    return (
      <article
        className={`col-span-1 ${colSpan} ${bgClass} p-6 md:p-8 relative overflow-hidden group flex flex-col gap-3`}
        style={{ animation: `card-in 0.4s ease ${index * 0.08}s both` }}
      >
        {/* Kind badge */}
        <div className="flex justify-between items-center">
          <span className={`${accentText} font-label font-black text-[10px] uppercase tracking-[0.2em]`}>
            {card.kind.replace(/_/g, " ")}
          </span>
          {card.source && (
            <span className="text-[var(--t-on-surface-variant)] text-[10px] uppercase tracking-widest">
              {card.source}
            </span>
          )}
        </div>

        {card.image_url ? (
          <>
            <div className="overflow-hidden">
              <img
                src={card.image_url}
                alt={card.title}
                loading="lazy"
                className="w-full h-48 object-cover filter saturate-150 contrast-125"
                onError={(e) => {
                  const img = e.currentTarget;
                  if (!img.dataset.retried) {
                    img.dataset.retried = "1";
                    img.src = img.src + (img.src.includes("?") ? "&" : "?") + "cb=" + Date.now();
                  }
                }}
              />
            </div>
            <h3 className="font-headline font-black text-lg text-white uppercase italic leading-tight">
              {card.title}
            </h3>
            {card.body && <p className="text-[var(--t-on-surface-variant)] font-bold uppercase leading-tight italic text-sm">{card.body}</p>}
          </>
        ) : (
          <>
            <h3 className="font-headline font-black text-2xl md:text-3xl text-white italic uppercase leading-none">
              {card.title}
            </h3>
            <p className="text-[var(--t-on-surface-variant)] font-bold uppercase leading-snug text-sm md:text-base">
              {card.body}
            </p>
          </>
        )}

        {card.attribution && (
          <p className={`mt-auto ${attrText} font-bold uppercase tracking-widest text-xs`}>
            {card.attribution}
          </p>
        )}
      </article>
    );
  }

  // Light mode cards
  const style = LIGHT_CARD_STYLES[index % LIGHT_CARD_STYLES.length];

  return (
    <article
      className={`col-span-1 ${colSpan} ${style.bg} p-8 md:p-12 rounded-xl relative overflow-hidden group flex flex-col gap-4 shadow-xl min-h-[300px]`}
      style={{ animation: `card-in 0.4s ease ${index * 0.08}s both` }}
    >
      {/* Light decoration blob */}
      {style.hero && (
        <div className="absolute -right-16 -top-16 w-64 h-64 bg-white/10 rounded-full blur-3xl group-hover:scale-110 transition-transform duration-700 pointer-events-none" />
      )}

      <div className="relative z-10 flex flex-col gap-3 h-full">
        {/* Kind + source */}
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-4xl opacity-80">
            {card.kind === "quote" ? "format_quote" : card.kind === "image" || card.kind === "meme" ? "image" : card.kind === "fact" || card.kind === "number_trivia" ? "lightbulb" : card.kind === "haiku" ? "spa" : "emoji_emotions"}
          </span>
          <span className="font-label font-black text-xs uppercase tracking-widest opacity-60">
            {card.kind.replace(/_/g, " ")}
          </span>
          {card.source && (
            <span className="font-label font-black text-xs uppercase tracking-widest opacity-50 ml-auto">
              {card.source}
            </span>
          )}
        </div>

        {card.image_url ? (
          <div className="flex-1 rounded-lg overflow-hidden mt-2">
            <img
              src={card.image_url}
              alt={card.title}
              loading="lazy"
              className="w-full h-48 object-cover"
              onError={(e) => {
                const img = e.currentTarget;
                if (!img.dataset.retried) {
                  img.dataset.retried = "1";
                  img.src = img.src + (img.src.includes("?") ? "&" : "?") + "cb=" + Date.now();
                }
              }}
            />
            {card.body && <p className="mt-2 text-sm opacity-80">{card.body}</p>}
          </div>
        ) : (
          <>
            <h3 className={`font-headline font-black leading-tight ${style.hero ? "text-3xl md:text-5xl italic" : "text-2xl md:text-3xl"}`}>
              {card.title}
            </h3>
            <p className={`opacity-90 leading-relaxed ${style.hero ? "text-lg md:text-xl" : "text-base"}`}>
              {card.body}
            </p>
          </>
        )}

        {card.attribution && (
          <div className="mt-auto pt-4 border-t border-white/20 flex justify-between items-center">
            <p className="font-label font-bold uppercase tracking-widest text-xs opacity-70">
              {card.attribution}
            </p>
          </div>
        )}
      </div>
    </article>
  );
}
