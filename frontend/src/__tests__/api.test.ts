import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { sendChat, ChatApiError } from "../api";

describe("sendChat", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllGlobals();
  });

  it("posts messages to /api/chat and returns the parsed response", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ reply: "hi!", model: "gpt-4o-mini", usage: null }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const result = await sendChat([{ role: "user", content: "hey" }]);

    expect(result).toEqual({ reply: "hi!", model: "gpt-4o-mini", usage: null });
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/chat");
    expect(init.method).toBe("POST");
    expect(init.headers["Content-Type"]).toBe("application/json");
    expect(JSON.parse(init.body as string)).toEqual({
      messages: [{ role: "user", content: "hey" }],
    });
  });

  it("throws ChatApiError with status and detail on non-2xx", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "bad key" }), { status: 502 }),
    );

    await expect(sendChat([{ role: "user", content: "hey" }])).rejects.toSatisfy(
      (err: unknown) =>
        err instanceof ChatApiError && err.status === 502 && err.message === "bad key",
    );
  });

  it("falls back to statusText when body is not JSON", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response("boom", { status: 500, statusText: "Internal Server Error" }),
    );

    await expect(sendChat([{ role: "user", content: "hey" }])).rejects.toSatisfy(
      (err: unknown) =>
        err instanceof ChatApiError &&
        err.status === 500 &&
        err.message === "Internal Server Error",
    );
  });
});
