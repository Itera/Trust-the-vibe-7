/**
 * Dark trap countdown — builds tension with hi-hats and 808 bass,
 * then drops when loading is done.
 */

let ctx: AudioContext | null = null;
let master: GainNode | null = null;
let loopTimer: ReturnType<typeof setInterval> | null = null;
let barCount = 0;

// --- helpers ---

function playOsc(
  freq: number, start: number, duration: number,
  gain: number, type: OscillatorType = "sine", detune = 0,
) {
  if (!ctx || !master) return;
  const osc = ctx.createOscillator();
  const env = ctx.createGain();
  osc.connect(env); env.connect(master);
  osc.type = type;
  osc.frequency.setValueAtTime(freq, start);
  osc.detune.value = detune;
  env.gain.setValueAtTime(0, start);
  env.gain.linearRampToValueAtTime(gain, start + 0.005);
  env.gain.exponentialRampToValueAtTime(0.001, start + duration);
  osc.start(start);
  osc.stop(start + duration + 0.01);
}

function play808(freq: number, start: number, duration: number, gain = 0.6) {
  if (!ctx || !master) return;
  const osc = ctx.createOscillator();
  const env = ctx.createGain();
  osc.connect(env); env.connect(master);
  osc.type = "sine";
  osc.frequency.setValueAtTime(freq * 2.5, start);
  osc.frequency.exponentialRampToValueAtTime(freq, start + 0.05);
  env.gain.setValueAtTime(gain, start);
  env.gain.exponentialRampToValueAtTime(0.001, start + duration);
  osc.start(start);
  osc.stop(start + duration + 0.01);
}

function playNoise(start: number, duration: number, gain: number, hipass = 4000) {
  if (!ctx || !master) return;
  const buf = ctx.createBuffer(1, Math.ceil(ctx.sampleRate * duration), ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  const src = ctx.createBufferSource();
  src.buffer = buf;
  const filter = ctx.createBiquadFilter();
  filter.type = "highpass";
  filter.frequency.value = hipass;
  const env = ctx.createGain();
  src.connect(filter); filter.connect(env); env.connect(master!);
  env.gain.setValueAtTime(gain, start);
  env.gain.exponentialRampToValueAtTime(0.001, start + duration);
  src.start(start);
}

// --- building blocks ---

const BPM = 140;
const BEAT = 60 / BPM;      // ~0.428s
const BAR = BEAT * 4;        // 4 beats

// 808 pattern: C1=32.7, F1=43.7, G1=49
const BASS_PATTERNS = [
  [{ f: 41.2, b: 0 }, { f: 32.7, b: 2 }],
  [{ f: 36.7, b: 0 }, { f: 41.2, b: 1.5 }, { f: 32.7, b: 3 }],
  [{ f: 32.7, b: 0 }, { f: 43.7, b: 0.75 }, { f: 49.0, b: 2 }, { f: 41.2, b: 3 }],
];

function scheduleBar() {
  if (!ctx) return;
  const now = ctx.currentTime;
  const tension = Math.min(barCount / 8, 1); // 0→1 over 8 bars

  // --- 808 bass ---
  const bassPattern = BASS_PATTERNS[barCount % BASS_PATTERNS.length];
  bassPattern.forEach(({ f, b }) => {
    const dur = BEAT * (1.2 + tension * 1.5);
    play808(f, now + b * BEAT, dur, 0.55 + tension * 0.15);
  });

  // --- kick on 1 and 3 ---
  [0, 2].forEach((beat) => {
    play808(60, now + beat * BEAT, BEAT * 0.25, 0.5 + tension * 0.2);
  });

  // --- snare on 2 and 4 ---
  [1, 3].forEach((beat) => {
    playNoise(now + beat * BEAT, 0.12, 0.18 + tension * 0.1, 2000);
    playOsc(200, now + beat * BEAT, 0.08, 0.1, "square");
  });

  // --- hi-hats: speed up with tension ---
  const hatDivision = tension < 0.4 ? 0.5 : tension < 0.7 ? 0.25 : 0.125;
  const hatCount = Math.round(4 / hatDivision);
  for (let i = 0; i < hatCount; i++) {
    const swing = (i % 2 === 1) ? BEAT * 0.04 : 0;
    playNoise(now + i * hatDivision * BEAT + swing, 0.04, 0.07 + tension * 0.04, 7000);
  }

  // --- rising tension note every 2 bars ---
  if (barCount % 2 === 0) {
    const riseFreq = 80 + tension * 220;
    playOsc(riseFreq, now, BAR * 0.9, 0.06 + tension * 0.06, "sawtooth");
  }

  // --- sub-bass drone that grows ---
  playOsc(32.7, now, BAR, tension * 0.12, "sine");

  barCount++;
}

export function startLoadingMusic() {
  ctx = new AudioContext();
  master = ctx.createGain();
  master.gain.value = 0.6;

  // Slight compression for that punchy trap sound
  const comp = ctx.createDynamicsCompressor();
  comp.threshold.value = -18;
  comp.knee.value = 6;
  comp.ratio.value = 4;
  comp.attack.value = 0.003;
  comp.release.value = 0.1;
  master.connect(comp);
  comp.connect(ctx.destination);

  barCount = 0;
  scheduleBar();
  loopTimer = setInterval(scheduleBar, BAR * 1000);
}

export function stopLoadingMusic() {
  if (loopTimer) { clearInterval(loopTimer); loopTimer = null; }
  if (master && ctx) {
    master.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.3);
  }
  setTimeout(() => {
    ctx?.close(); ctx = null; master = null;
  }, 400);
}
