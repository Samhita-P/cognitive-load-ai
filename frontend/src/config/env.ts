/**
 * Build-time env (Vite)
 * Production defaults point to deployed services.
 */

function trimTrailingSlashes(url: string): string {
  return url.replace(/\/+$/, "");
}

/* Django Gateway (auth + websocket + API proxy) */
export const API_BASE_URL = trimTrailingSlashes(
  import.meta.env.VITE_API_BASE_URL ??
  "https://cognitive-ai-gateway.onrender.com"
);

/* WebSocket connection */
export const GATEWAY_WS_URL =
  import.meta.env.VITE_GATEWAY_WS_URL ??
  "wss://cognitive-ai-gateway.onrender.com/ws/telemetry/";

/* ML service direct access (only if needed) */
export const ML_BASE_URL = trimTrailingSlashes(
  import.meta.env.VITE_ML_BASE_URL ??
  "https://cognitive-ai-ml.onrender.com"
);

/** REST path under Django gateway */
export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${p}`;
}

/** Direct ML service path */
export function mlUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${ML_BASE_URL}${p}`;
}