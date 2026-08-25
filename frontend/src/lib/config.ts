// Central endpoint resolution.
//
// In dev, vite.config.ts proxies "/api" and "/ws" to the backend
// (default http://localhost:8000), so API_BASE stays "" (same origin) and the
// browser talks to Vite, which forwards to the backend. This avoids CORS and
// mixed-content issues during development.
//
// Set VITE_API_BASE (e.g. in .env.local) to point directly at a backend that
// is NOT behind the Vite proxy — for a deployed dashboard, a backend on another
// host, or a LAN demo. Example: VITE_API_BASE=http://192.168.1.20:8000

const RAW_BASE = (import.meta.env.VITE_API_BASE ?? "").trim().replace(/\/+$/, "");

/** HTTP(S) base for REST calls. "" means same-origin (uses the Vite proxy). */
export const API_BASE = RAW_BASE;

/** Build an absolute (or same-origin-relative) REST URL. */
export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

/** Build a WebSocket URL, deriving ws/wss + host from API_BASE or the page. */
export function wsUrl(path: string, params: Record<string, string | number>): string {
  const qs = new URLSearchParams(
    Object.entries(params).map(([k, v]) => [k, String(v)]),
  ).toString();

  let origin: string;
  if (API_BASE) {
    // http://host -> ws://host, https://host -> wss://host
    origin = API_BASE.replace(/^http/i, "ws");
  } else if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    origin = `${proto}//${window.location.host}`;
  } else {
    origin = "ws://localhost:8000";
  }
  return `${origin}${path}${qs ? `?${qs}` : ""}`;
}
