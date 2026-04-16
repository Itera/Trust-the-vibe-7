import type { ChatMessage, ChatResponse } from "./types";

export class ChatApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ChatApiError";
  }
}

export async function sendChat(
  messages: ChatMessage[],
  options: { signal?: AbortSignal; baseUrl?: string } = {},
): Promise<ChatResponse> {
  const url = `${options.baseUrl ?? ""}/api/chat`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
    signal: options.signal,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (body?.detail) detail = JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new ChatApiError(res.status, detail);
  }

  return (await res.json()) as ChatResponse;
}
