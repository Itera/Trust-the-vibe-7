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

interface MotivatorProps {
  task?: string;
  onTaskChange?: (task: string) => void;
}

export default function Motivator({ task: taskProp, onTaskChange }: MotivatorProps = {}) {
  const [internalTask, setInternalTask] = useState("");
  const task = taskProp !== undefined ? taskProp : internalTask;
  const setTask = onTaskChange ?? setInternalTask;
  const [settings, setSettings] = useState<PersistedSettings>(DEFAULTS);
  const [darkMode, setDarkMode] = useState(false);
  const [personas, setPersonas] = useState<PersonaSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pkg, setPkg] = useState<MotivationPackage | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Hydrate settings from storage
  useEffect(() => {
    setSettings(loadSettings());
  }, []);

  // Persist settings
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch { /* ignore */ }
  }, [settings]);

  // Apply dark mode class to <html>
  useEffect(() => {
    const html = document.documentElement;
    if (darkMode) {
      html.classList.add("dark");
    } else {
      html.classList.remove("dark");
    }
  }, [darkMode]);

  // Fetch personas when language changes
  useEffect(() => {
    let cancelled = false;
    fetchPersonas(settings.language)
      .then((p) => { if (!cancelled) setPersonas(p); })
      .catch(() => { if (!cancelled) setPersonas([]); });
    return () => { cancelled = true; };
  }, [settings.language]);

  const theme = PERSONA_THEMES[settings.persona];

  const cssVars = useMemo(
    () => ({
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
      if (err instanceof ApiError && err.status === 422) {
        setPkg(null);
        setError(err.message);
      } else {
        const detail =
          err instanceof ApiError
            ? `(${err.status}) ${err.message}`
            : (err as Error).message || "Something went wrong.";
        setError(detail);
      }
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
          `${c.title.toUpperCase()}\n${c.body}${c.attribution ? `\n${c.attribution}` : ""}\n`,
      ),
    ];
    try {
      await navigator.clipboard.writeText(lines.join("\n"));
    } catch { /* no-op */ }
  }, [pkg]);

  const L = useMemo(() => ({
    title: "HuMotivatoren\u2122",
    subtitle: settings.language === "no"
      ? "Itera Intern Motivasjonskonsulent"
      : "Itera Internal Motivation Consulting",
    another: settings.language === "no" ? "Ny dose" : "Another dose",
    copy:    settings.language === "no" ? "Kopier rapport" : "Copy report",
    empty:   settings.language === "no"
      ? "Fortell hva du skal gj\u00f8re, s\u00e5 stiller HuMotivatoren diagnose."
      : "Tell us what you're about to do, and HuMotivatoren will diagnose.",
  }), [settings.language]);

  return (
    <div style={cssVars} className="min-h-screen bg-[var(--t-background)] text-[var(--t-on-background)]">

      {/* Top Nav */}
      <header className={[
        "fixed top-0 w-full z-50 flex justify-between items-center px-6 h-16 md:h-20",
        darkMode
          ? "bg-[#0e0e0e] border-b-4 border-primary shadow-[0_0_20px_rgba(255,124,245,0.3)]"
          : "bg-white/90 backdrop-blur-md border-b border-[var(--t-outline)]/20 shadow-sm",
      ].join(" ")}>
        <div className="flex items-center gap-3">
          <h1 className={[
            "text-2xl font-black italic tracking-tighter font-headline uppercase",
            darkMode ? "text-primary hover:-skew-x-6 transition-transform" : "text-primary",
          ].join(" ")}>
            {L.title}
          </h1>
          {!darkMode && (
            <p className="hidden md:block text-xs font-bold uppercase tracking-widest text-[var(--t-on-surface-variant)]">
              {L.subtitle}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            onClick={() => setDarkMode((d) => !d)}
            className={[
              "w-10 h-10 flex items-center justify-center transition-all",
              darkMode
                ? "bg-primary/20 text-primary hover:bg-primary/30 border border-primary/40"
                : "rounded-full bg-[var(--t-surface-container-low)] text-[var(--t-on-surface)] hover:bg-[var(--t-surface-container-high)]",
            ].join(" ")}
          >
            <span className="material-symbols-outlined text-xl">
              {darkMode ? "light_mode" : "dark_mode"}
            </span>
          </button>
        </div>
      </header>

      {/* Dark sidebar */}
      {darkMode && (
        <aside className="fixed left-0 top-0 h-full w-64 bg-[#201f1f] border-r-4 border-secondary shadow-[10px_0_30px_rgba(0,251,251,0.15)] flex-col pt-20 pb-8 z-40 hidden md:flex">
          <div className="px-6 mb-8 mt-4">
            <div className="flex items-center gap-2 mb-1">
              <span className="material-symbols-outlined text-tertiary text-3xl">cyclone</span>
              <span className="text-tertiary font-black text-lg font-headline uppercase">Anarchy</span>
            </div>
            <p className="text-xs text-secondary font-bold tracking-[0.2em] uppercase">Fuel the fire</p>
          </div>
          <nav className="flex-grow flex flex-col gap-1 px-3">
            {[
              { icon: "cyclone",       label: "Chaos Feed",  active: true  },
              { icon: "electric_bolt", label: "Vibe Check",  active: false },
              { icon: "priority_high", label: "Strike Zone", active: false },
              { icon: "lock_open",     label: "Vault",       active: false },
            ].map(({ icon, label, active }) => (
              <a
                key={label}
                href="#"
                onClick={(e) => e.preventDefault()}
                className={[
                  "flex items-center gap-3 px-4 py-3 font-headline text-sm uppercase tracking-widest transition-all duration-100",
                  active
                    ? "bg-secondary text-black font-black translate-x-2"
                    : "text-white hover:text-secondary hover:translate-x-1 hover:bg-secondary/10",
                ].join(" ")}
              >
                <span className="material-symbols-outlined">{icon}</span>
                {label}
              </a>
            ))}
          </nav>
          <div className="px-3 mt-auto">
            <button
              type="button"
              onClick={submit}
              disabled={!task.trim() || loading}
              className="w-full bg-primary text-on-primary font-black py-3 mb-3 border-4 border-primary/60 shadow-[4px_4px_0px_#ff5af9] hover:translate-x-1 hover:translate-y-1 hover:shadow-none transition-all uppercase tracking-tighter disabled:opacity-40"
            >
              Get Inspired
            </button>
          </div>
        </aside>
      )}

      {/* Main */}
      <main className={[
        "pt-20 md:pt-24 pb-24 px-4 md:px-6 min-h-screen transition-all",
        darkMode ? "md:pl-72" : "max-w-7xl mx-auto",
      ].join(" ")}>

        {/* Hero */}
        <section className="mb-10 md:mb-16 relative">
          {!darkMode && (
            <>
              <div className="absolute -top-12 -left-12 w-64 h-64 bg-primary/10 blur-[100px] rounded-full pointer-events-none" />
              <div className="absolute -top-12 -right-12 w-64 h-64 bg-secondary/10 blur-[100px] rounded-full pointer-events-none" />
            </>
          )}
          <div className="relative z-10">
            <h2 className={[
              "font-headline font-black tracking-tighter leading-[0.85] mb-6 md:mb-8",
              darkMode ? "text-5xl md:text-8xl italic uppercase text-white" : "text-5xl md:text-8xl",
            ].join(" ")}>
              {darkMode
                ? <span>UNLEASH THE <span className="text-primary block">MOTIVATION</span></span>
                : <span>UNLEASH THE <span className="text-primary italic">MOTIVATION</span>.</span>
              }
            </h2>
            <HeroInput
              value={task}
              onChange={setTask}
              onSubmit={submit}
              language={settings.language}
              loading={loading}
              darkMode={darkMode}
            />
          </div>
        </section>

        {/* Sliders */}
        <section className={[
          "mb-10 md:mb-16",
          darkMode
            ? "py-6 border-t-2 border-b-2 border-[var(--t-surface-container-high)]"
            : "bg-[var(--t-surface-container-low)] p-6 md:p-8 rounded-xl",
        ].join(" ")}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
            {[
              {
                labelNo: "Kynisme", labelEn: "Cynicism",
                value: settings.seriousness,
                onChange: (v: number) => updateSettings({ seriousness: v }),
                readOnly: false,
                accentDark: "var(--t-secondary)", accentLight: "var(--t-primary)",
                accentClass: darkMode ? "text-secondary" : "text-primary",
                descNo: "Fullt kaos \u2192 Dyp alvor", descEn: "Fully unhinged \u2192 Dead serious",
              },
              {
                labelNo: "Absurditet", labelEn: "Absurdity",
                value: Math.round(100 - settings.seriousness * 0.4),
                onChange: undefined,
                readOnly: true,
                accentDark: "var(--t-primary)", accentLight: "var(--t-secondary)",
                accentClass: darkMode ? "text-primary" : "text-secondary",
                descNo: "Livet er en suppe og du er en gaffel.", descEn: "Life is a soup and you are a fork.",
              },
              {
                labelNo: "Hum\u00f8r", labelEn: "Humor",
                value: Math.round(settings.seriousness * 0.5 + 20),
                onChange: undefined,
                readOnly: true,
                accentDark: "var(--t-tertiary)", accentLight: "var(--t-tertiary)",
                accentClass: "text-[var(--t-tertiary)]",
                descNo: "Stabil nok til \u00e5 lese dette.", descEn: "Stable enough to read this.",
              },
            ].map(({ labelNo, labelEn, value, onChange: sliderChange, readOnly, accentDark, accentLight, accentClass, descNo, descEn }) => (
              <div key={labelEn} className="flex flex-col gap-3">
                <div className="flex justify-between items-end">
                  <label className="font-headline font-black text-xl uppercase tracking-tighter">
                    {settings.language === "no" ? labelNo : labelEn}
                  </label>
                  <span className={`font-headline font-bold text-lg ${accentClass}`}>{value}%</span>
                </div>
                <input
                  type="range" min={0} max={100}
                  value={value}
                  readOnly={readOnly}
                  onChange={sliderChange ? (e) => sliderChange(Number(e.target.value)) : undefined}
                  className={`w-full appearance-none ${readOnly ? "cursor-default" : "cursor-pointer"} ${darkMode ? "brutalist-slider" : "kinetic-slider"}`}
                  style={{ accentColor: darkMode ? accentDark : accentLight }}
                />
                <p className="text-sm text-[var(--t-on-surface-variant)]">
                  {settings.language === "no" ? descNo : descEn}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Settings */}
        <SettingsBar
          personas={personas}
          persona={settings.persona}
          language={settings.language}
          seriousness={settings.seriousness}
          cards={settings.cards}
          themeId=""
          onChange={updateSettings}
          onThemeChange={() => {}}
          disabled={loading}
          darkMode={darkMode}
        />

        {/* Error */}
        {error && (
          <div role="alert" className={[
            "my-4 px-4 py-3 text-sm",
            darkMode
              ? "border-2 border-error text-error"
              : "rounded border border-[var(--t-error)] text-[var(--t-error)] bg-[var(--t-error-container)]/10",
          ].join(" ")}>
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && <LoadingState language={settings.language} darkMode={darkMode} />}

        {/* Empty */}
        {!loading && !pkg && !error && (
          <p className="mt-8 text-lg italic text-[var(--t-on-surface-variant)]">{L.empty}</p>
        )}

        {/* Report */}
        {!loading && pkg && (
          <section aria-label="report" className="mt-6">
            <div className={[
              "mb-6 pb-4",
              darkMode ? "border-b-4 border-primary" : "border-b-2 border-[var(--t-primary)]",
            ].join(" ")}>
              <h2 className={[
                "font-headline font-black tracking-tight mb-1",
                darkMode
                  ? "text-3xl md:text-4xl text-primary uppercase"
                  : "text-3xl md:text-4xl text-[var(--t-primary)]",
              ].join(" ")}>{pkg.report_title}</h2>
              {pkg.report_subtitle && (
                <p className="text-[var(--t-on-surface-variant)] italic">{pkg.report_subtitle}</p>
              )}
              <div className="flex gap-2 mt-2 text-xs tracking-widest uppercase text-[var(--t-on-surface-variant)]">
                <span>
                  {new Date().toLocaleDateString(
                    settings.language === "no" ? "nb-NO" : "en-GB",
                    { year: "numeric", month: "long", day: "numeric" },
                  )}
                </span>
                <span>•</span>
                <span>{settings.persona.toUpperCase()}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 md:gap-6 items-start">
              {pkg.cards.map((c, i) => (
                <MotivationCard key={`${c.kind}-${i}`} card={c} index={i} darkMode={darkMode} />
              ))}
            </div>

            <footer className={[
              "flex gap-3 mt-6 pt-4",
              darkMode
                ? "border-t-2 border-[var(--t-surface-container-high)]"
                : "border-t border-[var(--t-outline)]/30",
            ].join(" ")}>
              <button
                type="button"
                onClick={submit}
                className={[
                  "px-6 py-3 font-headline font-black text-sm uppercase tracking-wider transition-all",
                  darkMode
                    ? "bg-primary text-on-primary border-4 border-primary/60 shadow-[4px_4px_0px_#ff5af9] hover:translate-x-1 hover:translate-y-1 hover:shadow-none"
                    : "bg-primary text-on-primary rounded-full hover:scale-105 shadow-lg",
                ].join(" ")}
              >
                {L.another}
              </button>
              <button
                type="button"
                onClick={copyReport}
                className={[
                  "px-6 py-3 font-headline font-black text-sm uppercase tracking-wider transition-all",
                  darkMode
                    ? "bg-transparent text-secondary border-4 border-secondary hover:bg-secondary/10"
                    : "bg-transparent text-[var(--t-primary)] border-2 border-[var(--t-primary)] rounded-full hover:bg-primary/10",
                ].join(" ")}
              >
                {L.copy}
              </button>
            </footer>
          </section>
        )}
      </main>

      {/* Mobile bottom nav */}
      <nav className={[
        "md:hidden fixed bottom-0 left-0 w-full flex justify-around items-center h-16 z-50",
        darkMode
          ? "bg-[var(--t-surface-container-high)] border-t-4 border-primary"
          : "bg-white/80 backdrop-blur-xl border-t border-[var(--t-outline)]/20 shadow-2xl rounded-t-3xl",
      ].join(" ")}>
        {[
          { icon: "home",                    label: darkMode ? "FEED"   : "Daily" },
          { icon: "sentiment_very_satisfied", label: darkMode ? "VIBE"   : "Meme"  },
          { icon: "mood",                    label: darkMode ? "STRIKE" : "Mood"  },
        ].map(({ icon, label }) => (
          <button
            key={label}
            type="button"
            className="flex flex-col items-center justify-center gap-0.5 px-4 py-2 text-[var(--t-on-surface-variant)]"
          >
            <span className="material-symbols-outlined text-xl">{icon}</span>
            <span className="text-[10px] font-black uppercase tracking-wider font-label">{label}</span>
          </button>
        ))}
      </nav>

      {/* Floating panic button */}
      <div className="fixed bottom-20 md:bottom-8 right-6 z-50 group">
        <div className="absolute bottom-full right-0 mb-3 w-44 scale-0 group-hover:scale-100 transition-all duration-300 origin-bottom-right pointer-events-none">
          <div className={[
            "font-headline font-black text-xs p-3 shadow-xl rotate-3",
            darkMode
              ? "bg-tertiary text-black border-4 border-black"
              : "bg-[var(--t-tertiary-container)] text-black rounded-xl border-4 border-black",
          ].join(" ")}>
            WARNING: MAY CAUSE UNCONTROLLABLE HYPE! &#x26A1;&#xFE0F;
          </div>
        </div>
        <button
          type="button"
          aria-label="Emergency motivation"
          onClick={submit}
          disabled={!task.trim() || loading}
          className={[
            "w-16 h-16 md:w-20 md:h-20 rounded-full flex flex-col items-center justify-center transition-all",
            "hover:scale-110 active:scale-90 disabled:opacity-40 disabled:cursor-not-allowed",
            "animate-pulse hover:animate-none",
            darkMode
              ? "bg-error border-4 border-tertiary text-on-error shadow-[0_0_30px_rgba(255,110,132,0.5)]"
              : "bg-red-600 border-4 border-[var(--t-tertiary-container)] text-white shadow-[0_0_30px_rgba(220,38,38,0.4)]",
          ].join(" ")}
        >
          <span className="material-symbols-outlined text-2xl md:text-3xl">
            {darkMode ? "priority_high" : "error"}
          </span>
          <span className="font-label font-black text-[9px] uppercase leading-none mt-0.5">
            {darkMode ? "EMERGENCY" : "Panic"}
          </span>
        </button>
      </div>

      {/* Dark watermark */}
      {darkMode && (
        <div className="fixed -bottom-20 -right-20 text-[18rem] font-black italic uppercase text-white/5 select-none -z-10 pointer-events-none font-headline">
          CHAOS
        </div>
      )}
    </div>
  );
}