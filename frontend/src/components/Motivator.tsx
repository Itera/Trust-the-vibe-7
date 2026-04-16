import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  CardKind,
  Language,
  MotivationPackage,
  PersonaKey,
  PersonaSummary,
} from "../types";
import { ApiError, fetchPersonas, motivate } from "../api";
import { DEFAULT_CARDS, PERSONA_THEMES } from "../personas";
import HeroInput from "./HeroInput";
import SettingsBar from "./SettingsBar";
import LoadingState from "./LoadingState";
import MotivationCard from "./MotivationCard";

const STORAGE_KEY = "humotivatoren.settings.v1";

interface PersistedSettings {
  persona: PersonaKey;
  language: Language;
  seriousness: number;
  cards: CardKind[];
}

const DEFAULTS: PersistedSettings = {
  persona: "consultant",
  language: "en",
  seriousness: 40,
  cards: [...DEFAULT_CARDS],
};

function loadSettings(): PersistedSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULTS;
    const parsed = JSON.parse(raw);
    return { ...DEFAULTS, ...parsed };
  } catch {
    return DEFAULTS;
  }
}

export default function Motivator() {
  const [settings, setSettings] = useState<PersistedSettings>(DEFAULTS);
  const [task, setTask] = useState("");
  const [personas, setPersonas] = useState<PersonaSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pkg, setPkg] = useState<MotivationPackage | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // hydrate from storage on mount
  useEffect(() => {
    setSettings(loadSettings());
  }, []);

  // persist settings
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch {
      /* ignore */
    }
  }, [settings]);

  // fetch personas whenever language changes
  useEffect(() => {
    let cancelled = false;
    fetchPersonas(settings.language)
      .then((p) => {
        if (!cancelled) setPersonas(p);
      })
      .catch(() => {
        if (!cancelled) setPersonas([]);
      });
    return () => {
      cancelled = true;
    };
  }, [settings.language]);

  const theme = PERSONA_THEMES[settings.persona];

  // Apply background from response persona theme, reset when pkg is cleared
  useEffect(() => {
    const root = document.documentElement;
    if (pkg) {
      root.style.setProperty("--bg", PERSONA_THEMES[pkg.persona].gridTone);
    } else {
      root.style.removeProperty("--bg");
    }
  }, [pkg]);

  const cssVars = useMemo(
    () =>
      ({
        "--persona-accent": theme.accent,
        "--persona-accent-soft": theme.accentSoft,
        "--persona-title-font": theme.titleFont,
        "--persona-body-font": theme.bodyFont,
        "--persona-grid-tone": theme.gridTone,
      }) as React.CSSProperties,
    [theme],
  );

  const updateSettings = useCallback(
    (patch: Partial<PersistedSettings>) =>
      setSettings((prev) => ({ ...prev, ...patch })),
    [],
  );

  const submit = useCallback(async () => {
    if (!task.trim() || loading) return;
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    setLoading(true);
    setError(null);
    try {
      const out = await motivate(
        {
          task: task.trim(),
          persona: settings.persona,
          language: settings.language,
          seriousness: settings.seriousness,
          cards: settings.cards,
        },
        { signal: abortRef.current.signal },
      );
      setPkg(out);
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      const detail =
        err instanceof ApiError
          ? `(${err.status}) ${err.message}`
          : (err as Error).message || "Something went wrong.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  }, [task, loading, settings]);

  const copyReport = useCallback(async () => {
    if (!pkg) return;
    const lines = [
      pkg.report_title,
      pkg.report_subtitle,
      "",
      ...pkg.cards.map(
        (c) =>
          `${c.title.toUpperCase()}\n${c.body}${
            c.attribution ? `\n${c.attribution}` : ""
          }\n`,
      ),
    ];
    try {
      await navigator.clipboard.writeText(lines.join("\n"));
    } catch {
      /* no-op */
    }
  }, [pkg]);

  const L = useMemo(
    () => ({
      title: "HuMotivatoren™",
      subtitle:
        settings.language === "no"
          ? "Itera Intern Motivasjonskonsulent"
          : "Itera Internal Motivation Consulting",
      another:
        settings.language === "no" ? "Ny dose" : "Another dose",
      copy: settings.language === "no" ? "Kopier rapport" : "Copy report",
      empty:
        settings.language === "no"
          ? "Fortell hva du skal gjøre, så stiller HuMotivatoren diagnose."
          : "Tell us what you're about to do, and HuMotivatoren will diagnose.",
    }),
    [settings.language],
  );

  return (
    <div className="app" style={cssVars}>
      <header className="app__header">
        <div>
          <h1 className="app__title">{L.title}</h1>
          <p className="app__subtitle">{L.subtitle}</p>
        </div>
      </header>

      <HeroInput
        value={task}
        onChange={setTask}
        onSubmit={submit}
        language={settings.language}
        loading={loading}
      />

      <SettingsBar
        personas={personas}
        persona={settings.persona}
        language={settings.language}
        seriousness={settings.seriousness}
        cards={settings.cards}
        onChange={updateSettings}
        disabled={loading}
      />

      {error && (
        <div role="alert" className="alert">
          {error}
        </div>
      )}

      {loading && <LoadingState language={settings.language} />}

      {!loading && !pkg && !error && (
        <p className="empty">{L.empty}</p>
      )}

      {!loading && pkg && (
        <section className="report" aria-label="report">
          <header className="report__header">
            <h2 className="report__title">{pkg.report_title}</h2>
            {pkg.report_subtitle && (
              <p className="report__subtitle">{pkg.report_subtitle}</p>
            )}
            <div className="report__meta">
              <span>
                {new Date().toLocaleDateString(
                  settings.language === "no" ? "nb-NO" : "en-GB",
                  { year: "numeric", month: "long", day: "numeric" },
                )}
              </span>
              <span>•</span>
              <span>{settings.persona.toUpperCase()}</span>
            </div>
          </header>

          <div className="deck">
            {pkg.cards.map((c, i) => (
              <MotivationCard key={`${c.kind}-${i}`} card={c} />
            ))}
          </div>

          <footer className="report__actions">
            <button className="btn btn--primary" onClick={submit}>
              {L.another}
            </button>
            <button className="btn" onClick={copyReport}>
              {L.copy}
            </button>
          </footer>
        </section>
      )}
    </div>
  );
}
