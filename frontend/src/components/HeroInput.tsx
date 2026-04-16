import type { FormEvent } from "react";
import type { Language } from "../types";
import { QUICK_PICKS_EN, QUICK_PICKS_NO } from "../personas";

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  language: Language;
  loading: boolean;
  darkMode?: boolean;
}

export default function HeroInput({
  value,
  onChange,
  onSubmit,
  language,
  loading,
  darkMode = false,
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
    <section aria-label="input">
      <form onSubmit={handleSubmit} className="mb-4">
        <label htmlFor="hero-task" className="sr-only">
          {placeholder}
        </label>

        {darkMode ? (
          /* ── Dark / Brutalist input ── */
          <div className="relative group max-w-4xl">
            <div className="absolute -inset-1 bg-gradient-to-r from-secondary via-primary to-tertiary blur opacity-20 group-hover:opacity-40 transition duration-1000 pointer-events-none" />
            <div className="relative flex items-center">
              <input
                id="hero-task"
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder.toUpperCase()}
                disabled={loading}
                autoFocus
                className="w-full bg-black border-4 border-secondary text-xl md:text-3xl font-black uppercase italic p-5 md:p-6 text-white placeholder:text-secondary/30 focus:outline-none focus:border-primary transition-all shadow-[6px_6px_0px_var(--t-secondary)] focus:shadow-[6px_6px_0px_var(--t-primary)]"
              />
              <button
                type="submit"
                disabled={loading || !value.trim()}
                aria-label={cta}
                className="absolute right-3 bg-primary p-3 border-4 border-on-primary/20 hover:bg-tertiary hover:text-black transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-3xl font-black text-on-primary">bolt</span>
              </button>
            </div>
            {/* Hidden accessible button for tests */}
            <button
              type="submit"
              disabled={loading || !value.trim()}
              className="sr-only"
            >
              {loading ? "…" : cta}
            </button>
          </div>
        ) : (
          /* ── Light / Modern input ── */
          <div className="relative group max-w-3xl">
            <input
              id="hero-task"
              type="text"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              placeholder={placeholder}
              disabled={loading}
              autoFocus
              className="w-full bg-white border-[6px] border-black p-5 md:p-7 text-xl md:text-2xl font-headline font-bold placeholder:text-neutral-400 focus:outline-none focus:border-primary focus:shadow-[10px_10px_0px_0px_var(--t-primary)] transition-all rounded-none"
            />
            <div className="absolute top-0 right-0 h-full flex items-center pr-4">
              <span className={`material-symbols-outlined text-3xl text-primary font-black opacity-0 group-focus-within:opacity-100 transition-opacity`}>
                keyboard_return
              </span>
            </div>
            <button
              type="submit"
              disabled={loading || !value.trim()}
              className="mt-3 px-8 py-4 bg-primary text-on-primary font-headline font-black text-lg uppercase tracking-widest rounded-full shadow-lg hover:scale-105 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              {loading ? "…" : cta}
            </button>
          </div>
        )}
      </form>

      {/* Quick picks */}
      <div className="flex flex-wrap gap-2">
        {picks.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => onChange(p.value)}
            disabled={loading}
            className={[
              "text-sm px-4 py-2 transition-all font-label font-bold disabled:opacity-50",
              darkMode
                ? "bg-surface-container-high text-secondary border-2 border-secondary/40 hover:border-secondary hover:bg-secondary/10 uppercase tracking-wider"
                : "bg-white border border-[var(--t-outline)]/40 text-[var(--t-on-surface-variant)] rounded-full hover:border-primary hover:text-primary",
            ].join(" ")}
          >
            {p.label}
          </button>
        ))}
      </div>
    </section>
  );
}

