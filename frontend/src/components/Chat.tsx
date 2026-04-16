import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { sendChat, ChatApiError } from "../api";
import type { ChatMessage, UiTheme } from "../types";
import "./Chat.css";

const SYSTEM_PROMPT: ChatMessage = {
  role: "system",
  content: "You are a helpful assistant. Keep responses concise.",
};

function applyUiTheme(ui: UiTheme) {
  const root = document.documentElement;
  if (ui.background) root.style.setProperty("--bg", ui.background);
  if (ui.accent) root.style.setProperty("--accent", ui.accent);
  if (ui.fontScale) root.style.setProperty("--font-scale", String(ui.fontScale));
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setLoading(true);
    setError(null);

    abortRef.current = new AbortController();
    try {
      const res = await sendChat([SYSTEM_PROMPT, ...next], {
        signal: abortRef.current.signal,
      });
      if (res.ui) applyUiTheme(res.ui);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      const detail =
        err instanceof ChatApiError
          ? `Backend error (${err.status}): ${err.message}`
          : (err as Error).message || "Something went wrong.";
      setError(detail);
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }

  function handleReset() {
    abortRef.current?.abort();
    setMessages([]);
    setError(null);
    setInput("");
    const root = document.documentElement;
    root.style.removeProperty("--bg");
    root.style.removeProperty("--accent");
    root.style.removeProperty("--font-scale");
  }

  return (
    <section className="chat" aria-label="chat">
      <ul className="chat__log" aria-live="polite">
        {messages.length === 0 && (
          <li className="chat__empty">Say hi to get started.</li>
        )}
        {messages.map((m, i) => (
          <li key={i} className={`chat__msg chat__msg--${m.role}`}>
            <span className="chat__role">{m.role}</span>
            <span className="chat__content">{m.content}</span>
          </li>
        ))}
        {loading && (
          <li className="chat__msg chat__msg--assistant chat__msg--pending">
            <span className="chat__role">assistant</span>
            <span className="chat__content">…thinking</span>
          </li>
        )}
      </ul>

      {error && (
        <div role="alert" className="chat__error">
          {error}
        </div>
      )}

      <form className="chat__form" onSubmit={handleSubmit}>
        <label htmlFor="chat-input" className="sr-only">
          Your message
        </label>
        <input
          id="chat-input"
          type="text"
          placeholder="Type a message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
        <button type="button" onClick={handleReset} disabled={loading && !messages.length}>
          Reset
        </button>
      </form>
    </section>
  );
}
