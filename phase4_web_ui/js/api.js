/**
 * API client: build request body and call POST /recommend.
 * Exported for unit tests.
 */

import { API_BASE } from "./config.js";

/**
 * Map price_range select value to min_cost/max_cost.
 * @param {string} priceRange - e.g. "250-500", "0-250", "2000-"
 * @returns {{ min_cost?: number, max_cost?: number }}
 */
function parsePriceRange(priceRange) {
  const v = (priceRange || "").trim();
  if (!v) return {};
  if (v === "0-250") return { max_cost: 250 };
  if (v === "250-500") return { min_cost: 250, max_cost: 500 };
  if (v === "500-1000") return { min_cost: 500, max_cost: 1000 };
  if (v === "1000-1500") return { min_cost: 1000, max_cost: 1500 };
  if (v === "1500-2000") return { min_cost: 1500, max_cost: 2000 };
  if (v === "2000-") return { min_cost: 2000 };
  return {};
}

/**
 * Build request body from form data object (flat key-value).
 * Form uses: location (select), price_range (select), min_rating, cuisines (select).
 * @param {Record<string, string>} formData - e.g. { location: "Banashankari", price_range: "250-500", cuisines: "North Indian" }
 * @returns {import("./types.js").RecommendRequest}
 */
export function buildRecommendRequest(formData) {
  const location = formData.location?.trim() || null;
  const minRating = formData.min_rating?.trim();
  const cuisine = formData.cuisines?.trim();
  const cuisines = cuisine ? [cuisine] : null;
  const price = parsePriceRange(formData.price_range);

  const body = {
    location: location || undefined,
    min_rating: minRating ? parseFloat(minRating) : undefined,
    cuisines: cuisines && cuisines.length > 0 ? cuisines : undefined,
    ...price,
  };

  return Object.fromEntries(
    Object.entries(body).filter(([, v]) => v !== undefined && v !== null)
  );
}

/**
 * Call POST /recommend and return parsed JSON.
 * @param {import("./types.js").RecommendRequest} body
 * @returns {Promise<import("./types.js").RecommendResponse>}
 */
export async function fetchRecommend(body) {
  const url = `${API_BASE.replace(/\/$/, "")}/recommend`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    let message = `Request failed: ${res.status} ${res.statusText}`;
    try {
      const json = JSON.parse(text);
      if (json.detail) message = json.detail;
    } catch (_) {
      if (text) message = text;
    }
    throw new Error(message);
  }

  return res.json();
}

/**
 * Parse API response for UI (summary + restaurants list).
 * @param {import("./types.js").RecommendResponse} data
 * @returns {{ summary: string | null, restaurants: Array, relaxed: boolean }}
 */
export function parseRecommendResponse(data) {
  return {
    summary: data.summary && String(data.summary).trim() ? String(data.summary) : null,
    restaurants: Array.isArray(data.restaurants) ? data.restaurants : [],
    relaxed: Boolean(data.relaxed),
  };
}
