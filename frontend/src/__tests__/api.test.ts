import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, fetchPersonas, motivate } from "../api";

describe("api", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllGlobals();
  });

  describe("motivate()", () => {
    it("posts the full request body and returns the parsed package", async () => {
      const pkg = {
        task: "read the news",
        persona: "consultant",
        language: "en",
        report_title: "DOSE",
        report_subtitle: "sub",
        cards: [],
      };
      fetchMock.mockResolvedValueOnce(
        new Response(JSON.stringify(pkg), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );

      const result = await motivate({
        task: "read the news",
        persona: "consultant",
        language: "en",
        seriousness: 40,
        cards: ["peptalk", "quote"],
      });

      expect(result).toEqual(pkg);
      expect(fetchMock).toHaveBeenCalledOnce();
      const [url, init] = fetchMock.mock.calls[0];
      expect(url).toBe("/api/motivate");
      expect(init.method).toBe("POST");
      expect(JSON.parse(init.body as string)).toEqual({
        task: "read the news",
        persona: "consultant",
        language: "en",
        seriousness: 40,
        cards: ["peptalk", "quote"],
      });
    });

    it("throws ApiError with status and detail on non-2xx", async () => {
      fetchMock.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "model on fire" }), { status: 502 }),
      );
      await expect(
        motivate({
          task: "x",
          persona: "consultant",
          language: "en",
          seriousness: 30,
          cards: [],
        }),
      ).rejects.toSatisfy(
        (err: unknown) =>
          err instanceof ApiError &&
          err.status === 502 &&
          err.message === "model on fire",
      );
    });
  });

  describe("fetchPersonas()", () => {
    it("requests the specified language", async () => {
      fetchMock.mockResolvedValueOnce(new Response("[]", { status: 200 }));
      await fetchPersonas("no");
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/personas?language=no",
      );
    });
  });
});
