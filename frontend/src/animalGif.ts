/**
 * Fetches a random animal GIF URL from one of several free, key-less APIs.
 * Add more sources here to increase animal variety.
 */

type GifSource = () => Promise<string>;

const SOURCES: GifSource[] = [
  // Cats — direct image URL, no fetch needed
  () => Promise.resolve(`https://cataas.com/cat/gif?bust=${Date.now()}`),

  // Dogs — JSON API returns { url: "...gif" }
  async () => {
    const res = await fetch("https://random.dog/woof.json?include=gif");
    const data = await res.json();
    return data.url as string;
  },
];

export async function randomAnimalGif(): Promise<string> {
  const source = SOURCES[Math.floor(Math.random() * SOURCES.length)];
  try {
    return await source();
  } catch {
    // fallback to cat on network error
    return `https://cataas.com/cat/gif?bust=${Date.now()}`;
  }
}
