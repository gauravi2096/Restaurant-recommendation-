# Phase 1: Data Pipeline & Restaurant Store

Loads the [Zomato restaurant dataset](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) from Hugging Face, normalizes it, and persists to SQLite for querying by location, cost, rating, and cuisine.

**Production data source:** Results returned to users must come **strictly from the Hugging Face dataset**. Populate the store using the pipeline below; do not use mock, fallback, or hardcoded data for production.

## Setup

From the **project root** (Restaurant-recommendation-):

```bash
python3 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r phase1_data_pipeline/requirements-dev.txt
```

## Run pipeline (one-time load)

From the **project root**:

```bash
# Full dataset (may take a few minutes and download ~500MB)
python -m phase1_data_pipeline.pipeline

# Or with a limit for quick verification (e.g. 1000 rows)
python -c "
from phase1_data_pipeline.pipeline import run_pipeline
result = run_pipeline(max_rows=1000, db_path='phase1_data_pipeline/restaurants.db')
print(result)
"

# Full dataset with project-local cache (recommended if ~/.cache is not writable):
python -m phase1_data_pipeline --db phase1_data_pipeline/restaurants.db --cache-dir phase1_data_pipeline/.hf_cache

# Use a local cache dir if you cannot write to ~/.cache (e.g. in CI/sandbox):
python -m phase1_data_pipeline --db restaurants.db --max-rows 100 --cache-dir ./phase1_data_pipeline/.hf_cache
```

This creates (by default) `phase1_data_pipeline/restaurants.db`, which the API uses. The raw dataset has ~51.7k rows; after deduplication (name + address) you get ~12.5k unique restaurants. Use `--max-rows` for a quicker load during development.

**For search results that match user criteria and show many different restaurants**, you must run this pipeline to load the Hugging Face dataset. The seed script (`scripts/seed_db_for_manual_testing.py`) only adds 6 sample rows, so searches will return the same or very few results until the full dataset is loaded.

## Run tests

From the **project root**:

```bash
pytest phase1_data_pipeline/tests -v
```

Tests use mocks for the Hugging Face API and a temporary SQLite file, so no network or persistent DB is required.

## Module layout

| Module        | Role                                                                 |
|---------------|----------------------------------------------------------------------|
| `loader.py`  | Load dataset from Hugging Face (`load_zomato_dataset`, `load_zomato_dataset_as_dicts`). |
| `normalizer.py` | ETL: parse rate/cost, normalize strings, dedupe by (name, address). |
| `store.py`   | SQLite store: schema, indexes, `insert_many`, `query` (location, min_rate, cost, cuisine, etc.). |
| `pipeline.py`| Orchestrator: load → normalize → store; optional `clear_before` for refresh. |

## Query example

```python
from phase1_data_pipeline.store import RestaurantStore

with RestaurantStore("phase1_data_pipeline/restaurants.db") as store:
    rows = store.query(
        location="Banashankari",
        min_rate=4.0,
        max_cost=800,
        cuisine_contains="North Indian",
        limit=10,
    )
    for r in rows:
        print(r["name"], r["rate"], r["cost_for_two"])
```
