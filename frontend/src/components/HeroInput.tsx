import type { FormEvent } from "react";
import type { Language } from "../types";
import { QUICK_PICKS_EN, QUICK_PICKS_NO } from "../personas";

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  language: Language;
  loading: boolean;
}

export default function HeroInput({
  value,
  onChange,
  onSubmit,
  language,
  loading,
}: Props) {
  const picks = language === "no" ? QUICK_PICKS_NO : QUICK_PICKS_EN;
  const placeholder =
    language === "no"
      ? "Hva skal du i dag?"
      : "What are you about to do?";
  const cta = language === "no" ? "DOSÉR MEG" : "DOSE ME";

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (value.trim() && !loading) onSubmit();
  }

  return (
    <section className="hero" aria-label="input">
      <form className="hero__form" onSubmit={handleSubmit}>
        <label htmlFor="hero-task" className="sr-only">
          {placeholder}
        </label>
        <input
          id="hero-task"
          type="text"
          className="hero__input"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button
          type="submit"
          className="hero__cta"
          disabled={loading || !value.trim()}
        >
          {loading ? "…" : cta}
        </button>
      </form>

      <div className="hero__picks">
        {picks.map((p) => (
          <button
            key={p.label}
            type="button"
            className="hero__pick"
            onClick={() => onChange(p.value)}
            disabled={loading}
          >
            {p.label}
          </button>
        ))}
      </div>
    </section>
  );
}
