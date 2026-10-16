// Thin typed fetch wrapper. Attaches the JWT, centralises error handling.

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000";
const TOKEN_KEY = "masdojo.token";

/** Public base URL, for non-fetch transports like EventSource. */
export const API_BASE = BASE_URL;

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
}

/** Authenticated raw fetch — for non-JSON responses (e.g. artifact files). */
export async function authedFetch(path: string): Promise<Response> {
  const token = getToken();
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!resp.ok) throw new ApiError(resp.status, `Request failed (${resp.status})`);
  return resp;
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true } = opts;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const resp = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (resp.status === 204) return undefined as T;

  let payload: unknown = null;
  const text = await resp.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = text;
    }
  }

  if (!resp.ok) {
    throw new ApiError(resp.status, formatDetail(payload, resp.status));
  }
  return payload as T;
}

/** Turn a FastAPI error body into a readable message. `detail` may be a string
 * or, for 422 validation errors, an array of {loc, msg} objects (which would
 * otherwise stringify to "[object Object]"). */
function formatDetail(payload: unknown, status: number): string {
  const fallback = `Request failed (${status})`;
  if (!payload || typeof payload !== "object") return fallback;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((d) => {
        if (d && typeof d === "object" && "msg" in d) {
          const loc = (d as { loc?: unknown[] }).loc;
          const field = Array.isArray(loc) ? loc.slice(1).join(".") : "";
          const msg = String((d as { msg: unknown }).msg);
          return field ? `${field}: ${msg}` : msg;
        }
        return typeof d === "string" ? d : "";
      })
      .filter(Boolean);
    if (msgs.length) return msgs.join("; ");
  }
  return fallback;
}
