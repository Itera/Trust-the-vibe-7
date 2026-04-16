import type { PersonaKey } from "./types";

const audioCtx = () => new (window.AudioContext || (window as any).webkitAudioContext)();

let ctx: AudioContext | null = null;
function getCtx(): AudioContext {
  if (!ctx) ctx = audioCtx();
  if (ctx.state === "suspended") ctx.resume();
  return ctx;
}

/* ── Consultant: crisp corporate "ding" ─────────────────────── */
function playConsultant() {
  const c = getCtx();
  const osc = c.createOscillator();
  const gain = c.createGain();
  osc.type = "sine";
  osc.frequency.setValueAtTime(1200, c.currentTime);
  osc.frequency.exponentialRampToValueAtTime(800, c.currentTime + 0.15);
  gain.gain.setValueAtTime(0.35, c.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + 0.3);
  osc.connect(gain).connect(c.destination);
  osc.start();
  osc.stop(c.currentTime + 0.3);
}

/* ── Stoic: deep, resonant gong / bell ──────────────────────── */
function playStoic() {
  const c = getCtx();
  const t = c.currentTime;

  // fundamental
  const osc1 = c.createOscillator();
  const gain1 = c.createGain();
  osc1.type = "sine";
  osc1.frequency.value = 120;
  gain1.gain.setValueAtTime(0.4, t);
  gain1.gain.exponentialRampToValueAtTime(0.001, t + 1.5);
  osc1.connect(gain1).connect(c.destination);
  osc1.start(t);
  osc1.stop(t + 1.5);

  // harmonic overtone
  const osc2 = c.createOscillator();
  const gain2 = c.createGain();
  osc2.type = "sine";
  osc2.frequency.value = 240;
  gain2.gain.setValueAtTime(0.15, t);
  gain2.gain.exponentialRampToValueAtTime(0.001, t + 1.0);
  osc2.connect(gain2).connect(c.destination);
  osc2.start(t);
  osc2.stop(t + 1.0);
}

/* ── Nordmann: cheerful Viking horn / bugle call ────────────── */
function playNordmann() {
  const c = getCtx();
  const t = c.currentTime;
  const notes = [260, 330, 390, 520]; // ascending horn call

  notes.forEach((freq, i) => {
    const osc = c.createOscillator();
    const gain = c.createGain();
    osc.type = "sawtooth";
    osc.frequency.value = freq;
    // low-pass to soften the sawtooth into a horn timbre
    const filter = c.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 800;
    const start = t + i * 0.12;
    gain.gain.setValueAtTime(0, start);
    gain.gain.linearRampToValueAtTime(0.25, start + 0.03);
    gain.gain.exponentialRampToValueAtTime(0.001, start + 0.2);
    osc.connect(filter).connect(gain).connect(c.destination);
    osc.start(start);
    osc.stop(start + 0.25);
  });
}

/* ── Gremlin: chaotic chittering / cackle ───────────────────── */
function playGremlin() {
  const c = getCtx();
  const t = c.currentTime;

  // rapid frequency-modulated chittering
  for (let i = 0; i < 6; i++) {
    const osc = c.createOscillator();
    const gain = c.createGain();
    osc.type = "square";
    const base = 300 + Math.random() * 600;
    const start = t + i * 0.07;
    osc.frequency.setValueAtTime(base, start);
    osc.frequency.linearRampToValueAtTime(base + (Math.random() > 0.5 ? 400 : -200), start + 0.05);
    gain.gain.setValueAtTime(0.18, start);
    gain.gain.exponentialRampToValueAtTime(0.001, start + 0.06);
    osc.connect(gain).connect(c.destination);
    osc.start(start);
    osc.stop(start + 0.07);
  }

  // low growl underneath
  const growl = c.createOscillator();
  const gGain = c.createGain();
  growl.type = "sawtooth";
  growl.frequency.setValueAtTime(80, t);
  growl.frequency.linearRampToValueAtTime(60, t + 0.5);
  gGain.gain.setValueAtTime(0.15, t);
  gGain.gain.exponentialRampToValueAtTime(0.001, t + 0.5);
  const dist = c.createWaveShaper();
  const curve = new Float32Array(256);
  for (let i = 0; i < 256; i++) {
    const x = (i * 2) / 256 - 1;
    curve[i] = (Math.PI + 200 * x) / (Math.PI + 200 * Math.abs(x));
  }
  dist.curve = curve;
  growl.connect(dist).connect(gGain).connect(c.destination);
  growl.start(t);
  growl.stop(t + 0.5);
}

const SOUND_MAP: Record<PersonaKey, () => void> = {
  consultant: playConsultant,
  stoic: playStoic,
  nordmann: playNordmann,
  gremlin: playGremlin,
};

export function playPersonaSound(key: PersonaKey): void {
  try {
    SOUND_MAP[key]?.();
  } catch {
    // Audio not available – silently ignore
  }
}
