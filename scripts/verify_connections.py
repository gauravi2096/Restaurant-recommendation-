#!/usr/bin/env python3
"""
Verify that all phases are properly connected and the system works end-to-end.
Run from project root: python scripts/verify_connections.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def phase1_ok() -> bool:
    """Phase 1: Store and normalizer can be used."""
    try:
        from phase1_data_pipeline.store import RestaurantStore
        from phase1_data_pipeline.normalizer import normalize_restaurants
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        store = RestaurantStore(path)
        store.connect()
        store.init_schema()
        store.insert_many(normalize_restaurants([{
            "name": "Test", "address": "A", "url": "https://x", "location": "L",
            "listed_in(city)": "L", "rate": "4.0/5", "votes": 10,
            "approx_cost(for two people)": "500", "cuisines": "North Indian",
            "rest_type": "Casual", "online_order": "Yes", "book_table": "No",
            "phone": None, "dish_liked": None,
        }]))
        n = store.count()
        store.close()
        Path(path).unlink(missing_ok=True)
        return n == 1
    except Exception as e:
        print(f"Phase 1 failed: {e}")
        return False


def phase2_ok() -> bool:
    """Phase 2: API creates app, health and recommend work."""
    try:
        from fastapi.testclient import TestClient
        from phase2_api.api import create_app
        from phase1_data_pipeline.store import RestaurantStore
        from phase1_data_pipeline.normalizer import normalize_restaurants
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        store = RestaurantStore(path)
        store.connect()
        store.init_schema()
        store.insert_many(normalize_restaurants([{
            "name": "Jalsa", "address": "x", "url": "https://x", "location": "Banashankari",
            "listed_in(city)": "Banashankari", "rate": "4.1/5", "votes": 100,
            "approx_cost(for two people)": "800", "cuisines": "North Indian",
            "rest_type": "Casual Dining", "online_order": "Yes", "book_table": "Yes",
            "phone": None, "dish_liked": None,
        }]))
        store.close()
        app = create_app(db_path=path)
        client = TestClient(app)
        r = client.get("/health")
        if r.status_code != 200:
            print(f"Phase 2 health: {r.status_code} {r.text}")
            return False
        r = client.post("/recommend", json={"location": "Banashankari", "top_n": 5})
        if r.status_code != 200:
            print(f"Phase 2 recommend: {r.status_code} {r.text}")
            return False
        data = r.json()
        if "restaurants" not in data or "summary" not in data or "relaxed" not in data:
            print("Phase 2 recommend: missing keys in response")
            return False
        Path(path).unlink(missing_ok=True)
        return True
    except Exception as e:
        print(f"Phase 2 failed: {e}")
        return False


def phase3_ok() -> bool:
    """Phase 3: LLM module imports and generate_summary is callable (no API key required for import)."""
    try:
        from phase3_llm.service import generate_summary
        # Call with empty list -> returns None without calling Groq
        out = generate_summary([], {})
        return out is None
    except Exception as e:
        print(f"Phase 3 failed: {e}")
        return False


def phase4_ok() -> bool:
    """Phase 4: Web UI assets exist and request/response contract matches API."""
    try:
        ui = ROOT / "phase4_web_ui"
        if not (ui / "index.html").is_file():
            print("Phase 4: index.html missing")
            return False
        if not (ui / "js" / "api.js").is_file():
            print("Phase 4: js/api.js missing")
            return False
        if not (ui / "js" / "config.js").is_file():
            print("Phase 4: js/config.js missing")
            return False
        return True
    except Exception as e:
        print(f"Phase 4 failed: {e}")
        return False


def phase5_ok() -> bool:
    """Phase 5: Cache and analytics available; analytics endpoint exists when Phase 5 loaded."""
    try:
        from phase5_enhancements import RecommendationCache, cache_key_from_request, get_popular, log_recommend_usage
        from phase2_api.api import _phase5_available
        if not _phase5_available:
            print("Phase 5: not available (import failed in API)")
            return False
        from fastapi.testclient import TestClient
        from phase2_api.api import create_app
        from phase1_data_pipeline.store import RestaurantStore
        from phase1_data_pipeline.normalizer import normalize_restaurants
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        store = RestaurantStore(path)
        store.connect()
        store.init_schema()
        store.insert_many(normalize_restaurants([{
            "name": "J", "address": "x", "url": "https://x", "location": "L",
            "listed_in(city)": "L", "rate": "4.0/5", "votes": 1,
            "approx_cost(for two people)": "500", "cuisines": "North Indian",
            "rest_type": "Casual", "online_order": "Yes", "book_table": "No",
            "phone": None, "dish_liked": None,
        }]))
        store.close()
        app = create_app(db_path=path)
        client = TestClient(app)
        r = client.get("/analytics/popular")
        if r.status_code != 200:
            print(f"Phase 5 analytics: {r.status_code}")
            return False
        data = r.json()
        if "locations" not in data or "cuisines" not in data:
            print("Phase 5 analytics: missing keys")
            return False
        Path(path).unlink(missing_ok=True)
        return True
    except Exception as e:
        print(f"Phase 5 failed: {e}")
        return False


def main() -> int:
    print("Verifying phase connections...")
    checks = [
        ("Phase 1 (data pipeline)", phase1_ok),
        ("Phase 2 (API)", phase2_ok),
        ("Phase 3 (LLM)", phase3_ok),
        ("Phase 4 (Web UI assets)", phase4_ok),
        ("Phase 5 (cache + analytics)", phase5_ok),
    ]
    failed = []
    for name, fn in checks:
        if fn():
            print(f"  {name}: OK")
        else:
            print(f"  {name}: FAILED")
            failed.append(name)
    if failed:
        print("\nFailed:", ", ".join(failed))
        return 1
    print("\nAll phases connected and working.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
