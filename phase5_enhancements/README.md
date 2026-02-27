# Phase 5: Optional Enhancements

Response **caching** and **anonymous analytics** for the recommendation API.

## Features

- **Caching**: `POST /recommend` responses are cached in memory by a hash of the request body (location, min_rating, cost, cuisines, top_n, etc.). Identical requests return the cached result without calling the store or LLM again. Cache is LRU with a default max size of 100.
- **Analytics**: Each recommend request is logged anonymously (location and cuisines only). `GET /analytics/popular` returns aggregated popular locations and cuisines.

## Usage

Phase 5 is optional. When the `phase5_enhancements` package is installed, the Phase 2 API automatically enables cache and analytics and exposes `GET /analytics/popular`.

- **Run API**: From project root, `uvicorn phase2_api.api:app --reload`. Then:
  - `POST /recommend` — same as before; repeated identical requests are served from cache.
  - `GET /analytics/popular?top_locations=10&top_cuisines=10` — returns `{ "locations": [{"name", "count"}], "cuisines": [{"name", "count"}] }`.

## Module layout

| File | Purpose |
|------|--------|
| `cache.py` | `cache_key_from_request(body)`, `RecommendationCache` (get/set/clear, LRU eviction). |
| `analytics.py` | `log_recommend_usage(body)`, `get_popular()`, `clear_events()`. |
| `tests/` | Unit tests for cache and analytics; Phase 2 has integration tests in `phase2_api/tests/test_phase5_integration.py`. |

## Tests

From project root:

```bash
.venv/bin/python -m pytest phase5_enhancements/tests/ phase2_api/tests/test_phase5_integration.py -v
```

Phase 5 integration tests are skipped if `phase5_enhancements` is not installed.
