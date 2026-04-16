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
  onChange: (
    patch: Partial<{
      persona: PersonaKey;
      language: Language;
      seriousness: number;
      cards: CardKind[];
    }>,
  ) => void;
  onThemeChange: (themeId: string) => void;
  disabled?: boolean;
}

export default function SettingsBar({
  personas,
  persona,
  language,
  seriousness,
  cards,
  themeId,
  onChange,
  onThemeChange,
  disabled,
}: Props) {
  const [open, setOpen] = useState(false);

  const L = {
    persona: language === "no" ? "Persona" : "Persona",
    language: language === "no" ? "Språk" : "Language",
    seriousness: language === "no" ? "Seriøsitet" : "Seriousness",
    cards: language === "no" ? "Kort" : "Cards",
    moreSettings: language === "no" ? "Flere innstillinger" : "More settings",
    lessSettings: language === "no" ? "Skjul innstillinger" : "Hide settings",
    fullyPro: language === "no" ? "Dyp alvor" : "Dead serious",
    fullyWild: language === "no" ? "Fullt kaos" : "Fully unhinged",
    theme: language === "no" ? "Tema" : "Theme",
  };

  function toggleCard(k: CardKind) {
    const next = cards.includes(k) ? cards.filter((x) => x !== k) : [...cards, k];
    onChange({ cards: next });
  }

  return (
    <section className="settings" aria-label="settings">
      <div className="settings__row">
        <div className="settings__group" role="radiogroup" aria-label={L.persona}>
          {personas.map((p) => (
            <button
              key={p.key}
              type="button"
              role="radio"
              aria-checked={persona === p.key}
              className={`persona-pill ${
                persona === p.key ? "persona-pill--active" : ""
              }`}
              style={
                persona === p.key
                  ? { background: p.accent_color, color: "white" }
                  : { borderColor: p.accent_color, color: p.accent_color }
              }
              onClick={() => {
                playPersonaSound(p.key);
                onChange({ persona: p.key });
              }}
              disabled={disabled}
            >
              {p.name}
            </button>
          ))}
        </div>

        <div className="settings__group">
          <button
            type="button"
            className={`lang-pill ${language === "en" ? "lang-pill--active" : ""}`}
            onClick={() => onChange({ language: "en" })}
            disabled={disabled}
          >
            EN
          </button>
          <button
            type="button"
            className={`lang-pill ${language === "no" ? "lang-pill--active" : ""}`}
            onClick={() => onChange({ language: "no" })}
            disabled={disabled}
          >
            NO
          </button>
        </div>

        <div className="theme-picker" role="group" aria-label={L.theme}>
          {THEMES.map((t: Theme) => (
            <button
              key={t.id}
              type="button"
              title={t.label}
              className={`theme-pill ${themeId === t.id ? "theme-pill--active" : ""}`}
              onClick={() => onThemeChange(t.id)}
              disabled={disabled}
            >
              {t.emoji} {t.label}
            </button>
          ))}
        </div>

        <button
          type="button"
          className="settings__toggle"
          onClick={() => setOpen((x) => !x)}
          aria-expanded={open}
        >
          {open ? L.lessSettings : L.moreSettings}
        </button>
      </div>

      {open && (
        <div className="settings__panel">
          <div className="settings__slider">
            <label htmlFor="seriousness">
              {L.seriousness}: <strong>{seriousness}</strong>
            </label>
            <input
              id="seriousness"
              type="range"
              min={0}
              max={100}
              value={seriousness}
              onChange={(e) => onChange({ seriousness: Number(e.target.value) })}
              disabled={disabled}
            />
            <div className="settings__slider-labels">
              <span>{L.fullyPro}</span>
              <span>{L.fullyWild}</span>
            </div>
          </div>

          <fieldset className="settings__cards">
            <legend>{L.cards}</legend>
            <div className="settings__cards-grid">
              {ALL_CARD_KINDS.map((k) => (
                <label key={k} className="settings__card-toggle">
                  <input
                    type="checkbox"
                    checked={cards.includes(k)}
                    onChange={() => toggleCard(k)}
                    disabled={disabled}
                  />
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
