import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Chat from "../components/Chat";

describe("<Chat />", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllGlobals();
  });

  it("renders an empty state and disables Send when input is blank", () => {
    render(<Chat />);
    expect(screen.getByText(/say hi to get started/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("sends a message and renders the assistant reply", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ reply: "hello human", model: "gpt-4o-mini" }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const user = userEvent.setup();
    render(<Chat />);

    await user.type(screen.getByLabelText(/your message/i), "hey bot");
    await user.click(screen.getByRole("button", { name: /send/i }));

    // user message shows immediately
    expect(screen.getByText("hey bot")).toBeInTheDocument();

    // assistant reply arrives
    await waitFor(() =>
      expect(screen.getByText("hello human")).toBeInTheDocument(),
    );

    // exactly one fetch to /api/chat
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/chat");
    const body = JSON.parse(init.body as string);
    expect(body.messages).toEqual([
      { role: "system", content: expect.stringMatching(/helpful assistant/i) },
      { role: "user", content: "hey bot" },
    ]);
  });

  it("renders an error alert when the backend returns a failure", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "model on fire" }), { status: 502 }),
    );

    const user = userEvent.setup();
    render(<Chat />);

    await user.type(screen.getByLabelText(/your message/i), "hey");
    await user.click(screen.getByRole("button", { name: /send/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/model on fire/i);
    expect(alert).toHaveTextContent(/502/);
  });

  it("Reset clears the transcript", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ reply: "ok", model: "gpt-4o-mini" }), {
        status: 200,
      }),
    );

    const user = userEvent.setup();
    render(<Chat />);

    await user.type(screen.getByLabelText(/your message/i), "ping");
    await user.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => expect(screen.getByText("ok")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: /reset/i }));
    expect(screen.queryByText("ping")).not.toBeInTheDocument();
    expect(screen.queryByText("ok")).not.toBeInTheDocument();
    expect(screen.getByText(/say hi to get started/i)).toBeInTheDocument();
  });
});
