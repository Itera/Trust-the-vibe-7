import { useEffect, useRef, useState } from "react";
import type { Language } from "../types";
import { LOADING_LINES_EN, LOADING_LINES_NO } from "../personas";
import { randomAnimalGif } from "../animalGif";

interface Props {
  language: Language;
}

export default function LoadingState({ language }: Props) {
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
    <section className="loading" aria-live="polite" aria-busy="true">
      {gifUrl && (
        <div className="loading__gif-wrap">
          <img src={gifUrl} alt="loading animal gif" className="loading__gif" />
        </div>
      )}
      <div className="loading__text">
        <div className="loading__spinner" aria-hidden="true" />
        <p className="loading__line">{lines[idx]}</p>
      </div>
    </section>
  );
}
