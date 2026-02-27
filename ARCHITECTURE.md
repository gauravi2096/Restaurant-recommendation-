# AI Restaurant Recommendation Service — Architecture

## Overview

The system recommends restaurants by combining **user preferences** (price, location, rating, cuisine), **restaurant data** from the [Hugging Face Zomato dataset](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation), and **Groq LLM** to produce natural-language recommendations, surfaced via a **web UI**.

**Data source policy:** Results returned to users must come **strictly from the provided dataset** ([ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)). No fallback, mock, or hardcoded results. Populate the restaurant store using the Phase 1 pipeline only; the script `scripts/seed_db_for_manual_testing.py` is for local/testing only and must not be used for production.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              WEB UI (Frontend)                                    │
│  Preferences form • Results list • LLM-generated summary                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           API LAYER (Backend)                                    │
│  REST/GraphQL • Auth (optional) • Request validation                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│   Data / Search       │  │   Recommendation       │  │   Groq LLM Service     │
│   Service             │  │   Orchestrator         │  │   (prompt + response)  │
│   (filter + rank)     │  │   (combine + decide)   │  │                        │
└───────────────────────┘  └───────────────────────┘  └───────────────────────┘
            │                           │                           │
            ▼                           │                           ▼
┌───────────────────────┐                │               ┌───────────────────────┐
│   Restaurant Store    │◄───────────────┘               │   Groq API            │
│   (DB / cache from    │                                │   (external)          │
│   Hugging Face data)  │                                └───────────────────────┘
└───────────────────────┘
```

---

## Phases

### Phase 1: Data Pipeline & Restaurant Store

**Goal:** Ingest the Zomato dataset from Hugging Face and expose it as a queryable restaurant store.

| Component | Responsibility |
|-----------|----------------|
| **Dataset loader** | Load `ManikaSaini/zomato-restaurant-recommendation` via Hugging Face `datasets` (or API). Handle CSV/Parquet, pagination, and errors. |
| **ETL / normalizer** | Clean and normalize: `rate` → numeric, `approx_cost(for two people)` → numeric range, `location` / `listed_in(city)` for location filters, `cuisines` for cuisine filters. Handle nulls and duplicates. |
| **Restaurant store** | Persist normalized records in a DB (e.g. SQLite/PostgreSQL) or search engine (e.g. Elasticsearch/Meilisearch). Index: location, cost, rating, cuisines, `rest_type`, `online_order`, `book_table` for fast filtering. |
| **Refresh strategy** | One-time load and/or scheduled refresh (e.g. daily/weekly) to keep data in sync with the dataset. |

**Outputs:**  
- Populated restaurant store.  
- Clear schema (e.g. `id`, `name`, `location`, `cuisines`, `cost_for_two`, `rate`, `url`, `address`, `rest_type`, etc.).

---

### Phase 2: Backend API & Recommendation Engine

**Goal:** Expose an API that accepts user preferences, runs filtering/ranking, and returns candidate restaurants plus an LLM-generated summary.

| Component | Responsibility |
|-----------|----------------|
| **Preferences API** | Accept `price` (min/max or range), `location` (city/area), `rating` (min), `cuisine` (list). Validate and normalize (e.g. location name matching). |
| **Filter & rank service** | Query restaurant store by: location, cost range, min rating, cuisine (and optionally rest_type, online_order). Rank by rating and optionally by votes/relevance. Return top N candidates (e.g. 5–15). |
| **Recommendation orchestrator** | 1) Call filter service with user preferences. 2) If no results, relax constraints or return “no results” message. 3) Pass candidate list + user preferences to LLM service. 4) Return structured response: list of restaurants + LLM summary. |
| **API layer** | REST (or GraphQL) endpoints, e.g. `POST /recommend` with JSON body `{ price, location, rating, cuisines }`. Optional: health check, API key, rate limiting. |

**Outputs:**  
- Working recommendation API that returns filtered restaurants and a slot for LLM text.

---

### Phase 3: Groq LLM Integration

**Goal:** Use Groq to turn filtered results and user context into clear, readable recommendations.

| Component | Responsibility |
|-----------|----------------|
| **Groq client** | Configure Groq API key (env), model (e.g. `llama-3-*` or `mixtral`), and handle timeouts/retries/errors. |
| **Prompt builder** | Build a prompt that includes: user preferences (price, location, rating, cuisine), and the list of candidate restaurants (name, location, rate, cost, cuisines, notable dishes if available). Ask for a short, user-friendly summary and optionally ordered “top picks” with 1–2 sentence reasoning. |
| **Response parser** | Parse LLM output (e.g. markdown or structured bullets). Optionally validate against the candidate list. Return both: **structured list** (from Phase 2) and **LLM summary text** to the API. |
| **Fallback** | If Groq is down or rate-limited, return only structured recommendations without LLM text. |

**Outputs:**  
- LLM service that returns a clear recommendation summary and optional per-restaurant blurbs.

---

### Phase 4: Web UI

**Goal:** Let users enter preferences and see recommendations (list + LLM summary) in a simple, responsive UI.

| Component | Responsibility |
|-----------|----------------|
| **Preferences form** | Inputs: location (dropdown or text), price range (slider or min/max), min rating (e.g. stars or number), cuisines (multi-select or tags). Optional: rest_type, online_order. Submit triggers `POST /recommend`. |
| **Results view** | Show: (1) LLM-generated summary at the top. (2) List of restaurants (name, rating, cost, location, cuisines, link to Zomato URL). Card layout, responsive. |
| **Loading & errors** | Loading state while calling API; clear messages for no results or API/LLM errors. |
| **Tech choices** | Static site (e.g. React/Vue/Svelte) or server-rendered (e.g. Next.js) calling the backend API. Host frontend and backend separately or together (e.g. same origin with reverse proxy). |

**Outputs:**  
- Deployed web UI that implements the full flow: preferences → API → recommendations + LLM summary.

---

### Phase 5: Optional Enhancements

| Area | Options |
|------|--------|
| **Caching** | Cache Groq responses for identical or similar preference sets (e.g. hash of params → summary + list). |
| **Auth** | Optional login to save preferences or favorite restaurants. |
| **Analytics** | Log anonymous usage (e.g. popular locations/cuisines) to tune filters and prompts. |
| **Reviews** | Use `reviews_list` from the dataset in the LLM prompt for richer “why we recommend” text. |
| **Deployment** | Backend: container (Docker) + cloud (e.g. Railway, Render, GCP). Frontend: Vercel/Netlify. Env-based config for Groq key and dataset/DB. |

---

## Data Flow (End-to-End)

1. **User** submits preferences (price, location, rating, cuisine) in the Web UI.
2. **Frontend** sends `POST /recommend` with JSON body to the Backend API.
3. **Recommendation orchestrator** calls the **filter service**, which queries the **restaurant store** (filled from the Hugging Face Zomato dataset).
4. **Filter service** returns a ranked list of candidate restaurants.
5. **Orchestrator** sends this list + user preferences to the **Groq LLM service**.
6. **Groq LLM** returns a natural-language summary (and optionally per-restaurant blurbs).
7. **API** returns to the frontend: `{ restaurants: [...], summary: "..." }`.
8. **Web UI** renders the LLM summary and the restaurant list (with links, rating, cost, etc.).
9. **Phase 5** (when enabled): API caches responses by request hash and logs anonymous usage; `GET /analytics/popular` returns popular locations and cuisines.

---

## Phase Connections & Verification

| From | To | Connection |
|------|-----|------------|
| Phase 2 API | Phase 1 | Uses `RestaurantStore` and DB path; filter service calls `store.query()`. |
| Phase 2 Orchestrator | Phase 3 | Dataset filtering is the single source of truth. Only the filtered restaurant list is passed to `generate_summary()`; the LLM cannot add or invent restaurants. UI and summary display only this list. |
| Phase 4 Web UI | Phase 2 | `POST /recommend` (config: `API_BASE` → `http://localhost:8000` when needed). Response: `restaurants`, `summary`, `relaxed`. |
| Phase 2 API | Phase 5 | Optional: on import, uses cache and analytics; adds `GET /analytics/popular`. |

**Run all tests (excluding Groq integration):**
```bash
.venv/bin/python -m pytest phase1_data_pipeline/tests phase2_api/tests phase3_llm/tests phase4_web_ui/tests phase5_enhancements/tests -m "not integration" -v
```

**Verify phase connectivity end-to-end:**
```bash
.venv/bin/python scripts/verify_connections.py
```

---

## Suggested Tech Stack (Reference Only)

| Layer | Options |
|-------|--------|
| **Data load** | Python + `datasets` (Hugging Face), `pandas` for cleaning. |
| **Restaurant store** | SQLite (simple) or PostgreSQL; or Elasticsearch/Meilisearch for richer search. |
| **Backend** | Python (FastAPI/Flask) or Node.js (Express/Fastify). |
| **LLM** | Groq API (Python `groq` SDK or HTTP client). |
| **Frontend** | React, Vue, or Svelte; or Next.js for full-stack. |
| **Deploy** | Docker; backend + DB on Railway/Render/GCP; frontend on Vercel/Netlify. |

---

## Security & Configuration

- **Groq API key:** Stored in environment variables, never in frontend or repo.
- **Dataset:** Public; no secrets. Optionally cache dataset or DB in object storage for faster restarts.
- **API:** Optional API key or CORS restriction for production; rate limiting to protect Groq and backend.

---

## Success Criteria (Per Phase)

| Phase | Done when |
|-------|-----------|
| 1 | Dataset is loaded, normalized, and queryable by location, price, rating, cuisine. |
| 2 | API accepts preferences and returns a filtered, ranked list of restaurants. |
| 3 | Groq returns a clear recommendation summary (and optional blurbs) for that list. |
| 4 | User can submit preferences in the UI and see recommendations + summary. |
| 5 | Optional: caching, auth, or review-aware prompts are implemented if scoped. |

This architecture is ready to be broken down into tasks and implemented phase by phase.
