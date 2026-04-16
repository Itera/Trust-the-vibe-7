/**
 * Procedural loading music via Web Audio API.
 * No files, no dependencies — generates a looping pentatonic melody in the browser.
 */

let ctx: AudioContext | null = null;
let master: GainNode | null = null;
let loopTimer: ReturnType<typeof setInterval> | null = null;

// Pentatonic scale — always sounds pleasant no matter the order
const NOTES = [261.63, 293.66, 329.63, 392.0, 440.0, 523.25, 587.33];

function playNote(freq: number, start: number, duration: number) {
  if (!ctx || !master) return;
  const osc = ctx.createOscillator();
  const env = ctx.createGain();
  osc.connect(env);
  env.connect(master);
  osc.type = "sine";
  osc.frequency.value = freq;
  env.gain.setValueAtTime(0, start);
  env.gain.linearRampToValueAtTime(0.25, start + 0.02);
  env.gain.linearRampToValueAtTime(0, start + duration * 0.9);
  osc.start(start);
  osc.stop(start + duration + 0.05);
}

function scheduleBar() {
  if (!ctx) return;
  const now = ctx.currentTime;
  const step = 0.28;
  // Pick 6 random notes from the scale for each bar
  for (let i = 0; i < 6; i++) {
    const freq = NOTES[Math.floor(Math.random() * NOTES.length)];
    playNote(freq, now + i * step, step * 0.85);
  }
}

export function startLoadingMusic() {
  ctx = new AudioContext();
  master = ctx.createGain();
  master.gain.value = 0.5;
  master.connect(ctx.destination);

  scheduleBar();
  loopTimer = setInterval(scheduleBar, 6 * 280); // 6 notes × 280 ms
}

export function stopLoadingMusic() {
  if (loopTimer) {
    clearInterval(loopTimer);
    loopTimer = null;
  }
  if (master && ctx) {
    master.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.4);
  }
  setTimeout(() => {
    ctx?.close();
    ctx = null;
    master = null;
  }, 500);
}
