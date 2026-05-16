/**
 * Build-time env (Vite): set in `.env` / `.env.local` or Docker build ARGs.
 * Defaults match local `npm run dev` + gateway/ml ports from docker-compose.
 */

function trimTrailingSlashes(url: string): string {
  return url.replace(/\/+$/, "");
}

export const API_BASE_URL = trimTrailingSlashes(
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
);

export const GATEWAY_WS_URL =
  import.meta.env.VITE_GATEWAY_WS_URL ?? "ws://localhost:8000/ws/telemetry/";

export const ML_BASE_URL = trimTrailingSlashes(
  import.meta.env.VITE_ML_BASE_URL ?? "http://127.0.0.1:8001"
);

/** REST path under API_BASE_URL (path must start with `/`). */
export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${p}`;
}

/** ML service path (must start with `/`). */
export function mlUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${ML_BASE_URL}${p}`;
}
