import type {
  Language,
  MotivationPackage,
  MotivationRequest,
  PersonaSummary,
} from "./types";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (body?.detail) return JSON.stringify(body.detail);
  } catch {
    /* not json */
  }
  return res.statusText || "Request failed";
}

export async function motivate(
  req: MotivationRequest,
  options: { signal?: AbortSignal; baseUrl?: string } = {},
): Promise<MotivationPackage> {
  const url = `${options.baseUrl ?? ""}/api/motivate`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal: options.signal,
  });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return (await res.json()) as MotivationPackage;
}

export async function fetchPersonas(
  language: Language,
  options: { baseUrl?: string } = {},
): Promise<PersonaSummary[]> {
  const url = `${options.baseUrl ?? ""}/api/personas?language=${language}`;
  const res = await fetch(url);
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return (await res.json()) as PersonaSummary[];
}
