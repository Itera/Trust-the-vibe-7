import { useState } from "react";
import type { CardKind, Language, PersonaKey, PersonaSummary } from "../types";
import { ALL_CARD_KINDS, cardLabel } from "../personas";
import { playPersonaSound } from "../personaSounds";
import { THEMES } from "../themes";
import type { Theme } from "../themes";

interface Props {
  personas: PersonaSummary[];
  persona: PersonaKey;
  language: Language;
  seriousness: number;
  cards: CardKind[];
  themeId: string;
  onChange: (patch: Partial<{ persona: PersonaKey; language: Language; seriousness: number; cards: CardKind[]; }>) => void;
  onThemeChange: (themeId: string) => void;
  disabled?: boolean;
  darkMode?: boolean;
}

export default function SettingsBar({ personas, persona, language, seriousness, cards, onChange, disabled, darkMode = false }: Props) {
  const [open, setOpen] = useState(false);
  const L = {
    persona: language === "no" ? "Persona" : "Persona",
    seriousness: language === "no" ? "Seri\u00f8sitet" : "Seriousness",
    cards: language === "no" ? "Kort" : "Cards",
    moreSettings: language === "no" ? "Flere innstillinger" : "More settings",
    lessSettings: language === "no" ? "Skjul innstillinger" : "Hide settings",
    fullyPro: language === "no" ? "Dyp alvor" : "Dead serious",
    fullyWild: language === "no" ? "Fullt kaos" : "Fully unhinged",
  };
  function toggleCard(k: CardKind) {
    const next = cards.includes(k) ? cards.filter((x) => x !== k) : [...cards, k];
    onChange({ cards: next });
  }
  const panelBg = darkMode
    ? "bg-[var(--t-surface-container)] border-2 border-[var(--t-surface-container-high)]"
    : "bg-white border border-[var(--t-outline)]/20 rounded-xl shadow-sm";
  return (
    <section aria-label="settings" className={`${panelBg} p-4 mb-6`}>
      <div className="flex flex-wrap gap-3 items-center">
        <div role="radiogroup" aria-label={L.persona} className="flex flex-wrap gap-2">
          {personas.map((p) => {
            const isActive = persona === p.key;
            return (
              <button
                key={p.key} type="button" role="radio" aria-checked={isActive}
                disabled={disabled}
                onClick={() => { playPersonaSound(p.key); onChange({ persona: p.key }); }}
                className={["font-label text-sm px-4 py-2 border-2 font-bold transition-all disabled:opacity-50", darkMode ? "uppercase tracking-widest text-xs font-black" : "rounded-full"].join(" ")}
                style={isActive ? { background: p.accent_color, color: "white", borderColor: p.accent_color } : { color: p.accent_color, borderColor: p.accent_color, background: "transparent" }}
              >{p.name}</button>
            );
          })}
        </div>
        <div className="flex gap-2 ml-auto">
          {(["en", "no"] as Language[]).map((lang) => {
            const isActive = language === lang;
            return (
              <button key={lang} type="button" disabled={disabled} onClick={() => onChange({ language: lang })}
                className={["font-label font-black text-xs uppercase tracking-widest px-3 py-2 border-2 transition-all disabled:opacity-50", darkMode ? (isActive ? "bg-primary text-on-primary border-primary" : "bg-transparent text-[var(--t-on-surface-variant)] border-[var(--t-outline)] hover:border-primary") : (isActive ? "bg-primary text-on-primary border-primary rounded" : "bg-transparent text-[var(--t-on-surface-variant)] border-[var(--t-outline)]/50 rounded hover:border-primary")].join(" ")}
              >{lang.toUpperCase()}</button>
            );
          })}
        </div>
        <button type="button" aria-expanded={open} onClick={() => setOpen((x) => !x)}
          className={["text-xs font-label font-bold uppercase tracking-wider transition-all flex items-center gap-1", darkMode ? "text-[var(--t-on-surface-variant)] hover:text-secondary px-3 py-2 border border-[var(--t-outline)] hover:border-secondary" : "text-[var(--t-on-surface-variant)] hover:text-primary px-3 py-2 rounded border border-[var(--t-outline)]/30 hover:border-primary"].join(" ")}
        >
          <span className="material-symbols-outlined text-base">{open ? "expand_less" : "settings"}</span>
          {open ? L.lessSettings : L.moreSettings}
        </button>
      </div>
      {open && (
        <div className={["mt-4 pt-4 grid grid-cols-1 md:grid-cols-2 gap-6", darkMode ? "border-t-2 border-[var(--t-surface-container-high)]" : "border-t border-[var(--t-outline)]/20"].join(" ")}>
          <div>
            <label htmlFor="seriousness" className={`text-sm font-label font-black uppercase tracking-wider block mb-2 ${darkMode ? "text-secondary" : "text-[var(--t-primary)]"}`}>
              {L.seriousness}: <span>{seriousness}</span>
            </label>
            <input id="seriousness" type="range" min={0} max={100} value={seriousness}
              onChange={(e) => onChange({ seriousness: Number(e.target.value) })}
              disabled={disabled}
              className={`w-full appearance-none cursor-pointer ${darkMode ? "brutalist-slider" : "kinetic-slider"}`}
              style={{ accentColor: darkMode ? "var(--t-secondary)" : "var(--t-primary)" }}
            />
            <div className="flex justify-between text-xs text-[var(--t-on-surface-variant)] mt-1 font-label">
              <span>{L.fullyWild}</span><span>{L.fullyPro}</span>
            </div>
          </div>
          <fieldset className="border-0 p-0 m-0">
            <legend className={`text-sm font-label font-black uppercase tracking-wider mb-2 ${darkMode ? "text-primary" : "text-[var(--t-primary)]"}`}>{L.cards}</legend>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
              {ALL_CARD_KINDS.map((k) => (
                <label key={k} className="flex items-center gap-2 text-sm cursor-pointer select-none text-[var(--t-on-surface-variant)] hover:text-[var(--t-on-surface)] transition-colors">
                  <input type="checkbox" checked={cards.includes(k)} onChange={() => toggleCard(k)} disabled={disabled} className="accent-[var(--t-primary)]" />
                  <span>{cardLabel(k, language)}</span>
                </label>
              ))}
            </div>
          </fieldset>
        </div>
      )}
    </section>
  );
}