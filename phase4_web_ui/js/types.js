/**
 * JSDoc types for API request/response (no runtime code).
 * @typedef {Object} RecommendRequest
 * @property {string} [location]
 * @property {number} [min_rating]
 * @property {number} [min_cost]
 * @property {number} [max_cost]
 * @property {string[]} [cuisines]
 * @property {number} [top_n]
 */

/**
 * @typedef {Object} RecommendResponse
 * @property {Array<{ name?: string, location?: string, rate?: number, cost_for_two?: number, cuisines?: string, url?: string }>} restaurants
 * @property {string|null} summary
 * @property {boolean} relaxed
 */

export {};
