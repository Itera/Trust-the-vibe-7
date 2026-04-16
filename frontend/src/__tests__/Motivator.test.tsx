import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Motivator from "../components/Motivator";

function mockPersonas() {
  return [
    { key: "consultant", name: "The Consultant", tagline: "x", accent_color: "#1e3a5f" },
    { key: "stoic", name: "The Stoic", tagline: "x", accent_color: "#2a2a2a" },
    { key: "nordmann", name: "The Nordmann", tagline: "x", accent_color: "#c8102e" },
    { key: "gremlin", name: "The Gremlin", tagline: "x", accent_color: "#ff6b35" },
  ];
}

function mockPackage(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    task: "read the news",
    persona: "consultant",
    language: "en",
    report_title: "Q2 MOTIVATION DOSE",
    report_subtitle: "For immediate consumption.",
    cards: [
      {
        kind: "peptalk",
        title: "Executive Summary",
        body: "You got this.",
      },
      {
        kind: "quote",
        title: "Quote of the Quarter",
        body: "Just do it.",
        attribution: "— Nike",
      },
    ],
    ...overrides,
  };
}

describe("<Motivator />", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("fetch", fetchMock);
    // Default: personas fetch succeeds.
    fetchMock.mockImplementation(async (url: string) => {
      if (typeof url === "string" && url.includes("/api/personas")) {
        return new Response(JSON.stringify(mockPersonas()), { status: 200 });
      }
      return new Response(JSON.stringify(mockPackage()), { status: 200 });
    });
  });

  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllGlobals();
  });

  it("renders the title and empty state", async () => {
    render(<Motivator />);
    expect(screen.getByRole("heading", { name: /HuMotivatoren/i })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole("radio", { name: /the consultant/i })).toBeInTheDocument(),
    );
    expect(
      screen.getByText(/tell us what you're about to do/i),
    ).toBeInTheDocument();
  });

  it("disables the CTA when input is empty", async () => {
    render(<Motivator />);
    const cta = screen.getByRole("button", { name: /dose me/i });
    expect(cta).toBeDisabled();
  });

  it("submits a task and renders the report", async () => {
    const user = userEvent.setup();
    render(<Motivator />);

    await waitFor(() =>
      expect(screen.getByRole("radio", { name: /the consultant/i })).toBeInTheDocument(),
    );

    await user.type(screen.getByLabelText(/what are you about to do/i), "hack things");
    await user.click(screen.getByRole("button", { name: /dose me/i }));

    await waitFor(() =>
      expect(screen.getByText("Q2 MOTIVATION DOSE")).toBeInTheDocument(),
    );

    const report = screen.getByLabelText("report");
    expect(within(report).getByText("Executive Summary")).toBeInTheDocument();
    expect(within(report).getByText("— Nike")).toBeInTheDocument();

    // Verify the motivate request shape.
    const motivateCall = fetchMock.mock.calls.find(
      ([url]) => typeof url === "string" && url.includes("/api/motivate"),
    );
    expect(motivateCall).toBeTruthy();
    const body = JSON.parse(motivateCall![1].body);
    expect(body.task).toBe("hack things");
    expect(body.persona).toBe("consultant");
    expect(body.language).toBe("en");
  });

  it("surfaces backend errors as a visible alert", async () => {
    fetchMock.mockImplementation(async (url: string) => {
      if (typeof url === "string" && url.includes("/api/personas")) {
        return new Response(JSON.stringify(mockPersonas()), { status: 200 });
      }
      return new Response(JSON.stringify({ detail: "kaboom" }), { status: 502 });
    });

    const user = userEvent.setup();
    render(<Motivator />);
    await waitFor(() =>
      expect(screen.getByRole("radio", { name: /the consultant/i })).toBeInTheDocument(),
    );

    await user.type(screen.getByLabelText(/what are you about to do/i), "hey");
    await user.click(screen.getByRole("button", { name: /dose me/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/kaboom/);
    expect(alert).toHaveTextContent(/502/);
  });

  it("persists persona + language + seriousness in localStorage", async () => {
    const user = userEvent.setup();
    render(<Motivator />);
    await waitFor(() =>
      expect(screen.getByRole("radio", { name: /the stoic/i })).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("radio", { name: /the stoic/i }));
    await user.click(screen.getByRole("button", { name: /^NO$/ }));

    await waitFor(() => {
      const raw = localStorage.getItem("humotivatoren.settings.v1");
      expect(raw).not.toBeNull();
      const parsed = JSON.parse(raw!);
      expect(parsed.persona).toBe("stoic");
      expect(parsed.language).toBe("no");
    });
  });

  it("uses a quick-pick to fill the input", async () => {
    const user = userEvent.setup();
    render(<Motivator />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /read the news/i })).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: /read the news/i }));

    expect(
      (screen.getByLabelText(/what are you about to do/i) as HTMLInputElement).value,
    ).toMatch(/news/i);
  });
});
