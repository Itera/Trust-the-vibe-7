import { useEffect, useState } from "react";
import type { Language } from "../types";
import { LOADING_LINES_EN, LOADING_LINES_NO } from "../personas";

interface Props {
  language: Language;
}

export default function LoadingState({ language }: Props) {
  const lines = language === "no" ? LOADING_LINES_NO : LOADING_LINES_EN;
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    const t = setInterval(() => {
      setIdx((i) => (i + 1) % lines.length);
    }, 900);
    return () => clearInterval(t);
  }, [lines.length]);

  return (
    <section className="loading" aria-live="polite" aria-busy="true">
      <div className="loading__spinner" aria-hidden="true" />
      <p className="loading__line">{lines[idx]}</p>
    </section>
  );
}
