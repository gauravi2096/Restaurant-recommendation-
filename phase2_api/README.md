# Phase 2: Backend API & Recommendation Engine

REST API that accepts user preferences (location, price, rating, cuisine), queries the Phase 1 restaurant store, and returns filtered recommendations. Summary field is reserved for Phase 3 (LLM).

## Setup

From the **project root** (Restaurant-recommendation-), with Phase 1 deps and data ready:

```bash
source .venv/bin/activate
pip install -r phase2_api/requirements-dev.txt
```

Ensure the Phase 1 DB exists (run Phase 1 pipeline first, or use `--db` to point to a DB path).

## Run the API

From the **project root**:

```bash
# Default: uses phase1_data_pipeline/restaurants.db
python -m phase2_api

# Custom port and DB
python -m phase2_api --host 0.0.0.0 --port 8000 --db /path/to/restaurants.db
```

Then:

- **GET** http://127.0.0.1:8000/health — health check and store row count
- **POST** http://127.0.0.1:8000/recommend — JSON body: `location`, `min_rating`, `min_cost`, `max_cost`, `cuisines`, `rest_type`, `online_order`, `book_table`, `top_n` (default 15)

## Run tests

From the **project root**:

```bash
pytest phase2_api/tests -v
```

## Module layout

| Module | Role |
|--------|------|
| `preferences.py` | Pydantic model `RecommendPreferences`: validate and normalize location, rating, cost, cuisines, etc. |
| `filter_service.py` | `get_recommendations(store, preferences, top_n)`: query store, support multiple cuisines, return top N. |
| `orchestrator.py` | `recommend(store, preferences, ...)`: run filter; if empty, relax constraints (drop cuisines, rating, cost); return `{ restaurants, summary, relaxed }`. |
| `api.py` | FastAPI app: `GET /health`, `POST /recommend`; CORS enabled. |
| `__main__.py` | Run uvicorn with optional `--db`. |

## Example request

```bash
curl -X POST http://127.0.0.1:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"location": "Banashankari", "min_rating": 4, "max_cost": 800, "top_n": 5}'
```

Response: `{ "restaurants": [...], "summary": null, "relaxed": false }`

**Optional (Phase 3):** Install `phase3_llm` and set `GROQ_API_KEY` to get a non-null `summary` (LLM-generated recommendation text).
