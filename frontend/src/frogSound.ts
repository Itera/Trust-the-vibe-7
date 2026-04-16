let _ctx: AudioContext | null = null;

function ctx(): AudioContext {
  if (!_ctx || _ctx.state === "closed") {
    _ctx = new AudioContext();
  }
  // Resume if suspended (browser autoplay policy)
  if (_ctx.state === "suspended") _ctx.resume();
  return _ctx;
}

/**
 * Synthesise a frog croak.
 * @param pitchMultiplier  1.0 = base pitch; >1 = higher; <1 = lower/scary
 * @param scary            Use a deeper, more menacing shape
 */
export function playFrogCroak(pitchMultiplier: number, scary = false): void {
  try {
    const ac = ctx();
    const now = ac.currentTime;
    const base = 190; // Hz — comfortable croak fundamental
    const f = base * pitchMultiplier;

    const master = ac.createGain();
    master.gain.setValueAtTime(0, now);
    master.connect(ac.destination);

    if (scary) {
      // Low, rumbling, descending growl
      const osc1 = ac.createOscillator();
      osc1.type = "sawtooth";
      osc1.frequency.setValueAtTime(f * 1.1, now);
      osc1.frequency.exponentialRampToValueAtTime(f * 0.45, now + 0.55);

      const osc2 = ac.createOscillator();
      osc2.type = "square";
      osc2.frequency.setValueAtTime(f * 0.55, now);
      osc2.frequency.exponentialRampToValueAtTime(f * 0.28, now + 0.6);

      const g1 = ac.createGain();
      g1.gain.setValueAtTime(0.45, now);
      g1.gain.exponentialRampToValueAtTime(0.001, now + 0.6);

      const g2 = ac.createGain();
      g2.gain.setValueAtTime(0.3, now);
      g2.gain.exponentialRampToValueAtTime(0.001, now + 0.65);

      osc1.connect(g1);
      osc2.connect(g2);
      g1.connect(master);
      g2.connect(master);

      master.gain.setValueAtTime(0.65, now);

      osc1.start(now); osc1.stop(now + 0.65);
      osc2.start(now); osc2.stop(now + 0.7);
    } else {
      // Chirpy upward-then-down croak
      const osc1 = ac.createOscillator();
      osc1.type = "square";
      osc1.frequency.setValueAtTime(f * 0.9, now);
      osc1.frequency.exponentialRampToValueAtTime(f * 1.5, now + 0.06);
      osc1.frequency.exponentialRampToValueAtTime(f * 0.85, now + 0.18);

      const osc2 = ac.createOscillator();
      osc2.type = "sine";
      osc2.frequency.setValueAtTime(f * 1.9, now);
      osc2.frequency.exponentialRampToValueAtTime(f * 1.3, now + 0.16);

      const g1 = ac.createGain();
      g1.gain.setValueAtTime(0.35, now);
      g1.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

      const g2 = ac.createGain();
      g2.gain.setValueAtTime(0.12, now);
      g2.gain.exponentialRampToValueAtTime(0.001, now + 0.16);

      osc1.connect(g1);
      osc2.connect(g2);
      g1.connect(master);
      g2.connect(master);

      master.gain.setValueAtTime(0.5, now);

      osc1.start(now); osc1.stop(now + 0.22);
      osc2.start(now); osc2.stop(now + 0.18);
    }
  } catch {
    // Audio blocked or unsupported — silently ignore
  }
}
