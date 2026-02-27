/**
 * Unit tests for API helpers: buildRecommendRequest, parseRecommendResponse, fetchRecommend (mocked).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  buildRecommendRequest,
  parseRecommendResponse,
  fetchRecommend,
} from "../js/api.js";

describe("buildRecommendRequest", () => {
  it("returns empty body when form data is empty", () => {
    const out = buildRecommendRequest({});
    expect(out).not.toHaveProperty("top_n");
    expect(out.location).toBeUndefined();
    expect(out.min_cost).toBeUndefined();
  });

  it("includes location when provided", () => {
    const out = buildRecommendRequest({ location: "  Banashankari  " });
    expect(out.location).toBe("Banashankari");
  });

  it("maps price_range to min_cost/max_cost", () => {
    expect(buildRecommendRequest({ price_range: "0-250" })).toEqual({ max_cost: 250 });
    expect(buildRecommendRequest({ price_range: "250-500" })).toEqual({ min_cost: 250, max_cost: 500 });
    expect(buildRecommendRequest({ price_range: "500-1000" })).toEqual({ min_cost: 500, max_cost: 1000 });
    expect(buildRecommendRequest({ price_range: "2000-" })).toEqual({ min_cost: 2000 });
  });

  it("parses min_rating as float", () => {
    const out = buildRecommendRequest({ min_rating: "4.5" });
    expect(out.min_rating).toBe(4.5);
  });

  it("uses single cuisine select as one-element array", () => {
    const out = buildRecommendRequest({ cuisines: "North Indian" });
    expect(out.cuisines).toEqual(["North Indian"]);
  });

  it("omits empty location, price_range, cuisines", () => {
    const out = buildRecommendRequest({
      location: "Koramangala",
      price_range: "",
      cuisines: "",
      min_rating: "4",
    });
    expect(out).toHaveProperty("location", "Koramangala");
    expect(out).toHaveProperty("min_rating", 4);
    expect(out.min_cost).toBeUndefined();
    expect(out.max_cost).toBeUndefined();
    expect(out.cuisines).toBeUndefined();
  });
});

describe("parseRecommendResponse", () => {
  it("returns summary and restaurants from API shape", () => {
    const data = {
      restaurants: [{ name: "Jalsa", rate: 4.1 }],
      summary: "Great picks for you!",
      relaxed: false,
    };
    const out = parseRecommendResponse(data);
    expect(out.summary).toBe("Great picks for you!");
    expect(out.restaurants).toHaveLength(1);
    expect(out.restaurants[0].name).toBe("Jalsa");
    expect(out.relaxed).toBe(false);
  });

  it("treats null summary as null", () => {
    const out = parseRecommendResponse({ restaurants: [], summary: null, relaxed: false });
    expect(out.summary).toBeNull();
  });

  it("treats empty string summary as null", () => {
    const out = parseRecommendResponse({ restaurants: [], summary: "  ", relaxed: false });
    expect(out.summary).toBeNull();
  });

  it("defaults restaurants to empty array when missing", () => {
    const out = parseRecommendResponse({ summary: null, relaxed: false });
    expect(out.restaurants).toEqual([]);
  });
});

describe("fetchRecommend", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("calls POST /recommend with JSON body", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({ restaurants: [], summary: null, relaxed: false }),
    });

    await fetchRecommend({ location: "BSK" });

    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, opts] = fetch.mock.calls[0];
    expect(url).toMatch(/\/recommend$/);
    expect(opts.method).toBe("POST");
    expect(opts.headers["Content-Type"]).toBe("application/json");
    expect(JSON.parse(opts.body)).toEqual({ location: "BSK" });
  });

  it("throws on non-ok response with message", async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
      text: () => Promise.resolve(JSON.stringify({ detail: "Store unavailable" })),
    });

    await expect(fetchRecommend({})).rejects.toThrow("Store unavailable");
  });
});
