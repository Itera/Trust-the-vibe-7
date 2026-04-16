import { useEffect, useRef, useState } from "react";
import type { Language } from "../types";
import { LOADING_LINES_EN, LOADING_LINES_NO } from "../personas";
import { randomAnimalGif } from "../animalGif";

interface Props {
  language: Language;
  darkMode?: boolean;
}

export default function LoadingState({ language, darkMode = false }: Props) {
  const lines = language === "no" ? LOADING_LINES_NO : LOADING_LINES_EN;
  const [idx, setIdx] = useState(0);
  const [gifUrl, setGifUrl] = useState<string | null>(null);
  const fetched = useRef(false);

  useEffect(() => {
    if (fetched.current) return;
    fetched.current = true;
    randomAnimalGif().then(setGifUrl);
  }, []);

  useEffect(() => {
    const t = setInterval(() => {
      setIdx((i) => (i + 1) % lines.length);
    }, 900);
    return () => clearInterval(t);
  }, [lines.length]);

  return (
    <section
      aria-live="polite"
      aria-busy="true"
      className={[
        "flex flex-col items-center gap-4 p-8 my-6",
        darkMode
          ? "bg-surface-container-high border-4 border-primary/40"
          : "bg-white border border-[var(--t-outline)]/20 rounded-xl shadow-sm",
      ].join(" ")}
    >
      {gifUrl && (
        <div className={`w-60 h-44 overflow-hidden bg-[var(--t-surface-variant)] ${darkMode ? "" : "rounded-lg"}`}>
          <img src={gifUrl} alt="loading animal gif" className="w-full h-full object-cover" />
        </div>
      )}
      <div className="flex items-center gap-3">
        <div
          aria-hidden="true"
          className={`w-7 h-7 border-4 rounded-full border-[var(--t-surface-variant)] animate-[spin_0.8s_linear_infinite]`}
          style={{ borderTopColor: darkMode ? "var(--t-secondary)" : "var(--t-primary)" }}
        />
        <p className={`font-body text-base ${darkMode ? "text-[var(--t-on-surface-variant)] font-bold uppercase tracking-wide" : "text-[var(--t-on-surface-variant)]"}`}>
          {lines[idx]}
        </p>
      </div>
    </section>
  );
}
