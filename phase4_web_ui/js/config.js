/**
 * API base URL. In production set via build env or window.__API_BASE__.
 * When UI is served from a different port (e.g. 3000, 8080), use API on port 8000.
 * Handles both localhost and 127.0.0.1 so POST /recommend goes to the API server, not the static server.
 */
function getApiBase() {
  if (typeof window === "undefined") {
    return "http://localhost:8000";
  }
  if (window.__API_BASE__) {
    return window.__API_BASE__;
  }
  const origin = window.location.origin;
  const isLocalhost = origin.startsWith("http://localhost:");
  const is127 = origin.startsWith("http://127.0.0.1:");
  // When on localhost/127, use same origin for API (single server serves both UI + API on one port)
  if (isLocalhost || is127) {
    return origin;
  }
  return origin;
}

export const API_BASE = getApiBase();
