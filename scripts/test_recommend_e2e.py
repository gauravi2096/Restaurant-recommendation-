#!/usr/bin/env python3
"""
End-to-end test for restaurant recommendation: seed DB, call POST /recommend, verify results.

Run from project root:
  python scripts/test_recommend_e2e.py

Logs show: dataset (DB) path and total_restaurants, filter kwargs, store before/after filter
counts, and orchestrator relax steps when filters return 0 results.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Enable INFO logs to see dataset loading, filter values, and result counts
logging.basicConfig(level=logging.INFO, format="%(name)s: %(levelname)s: %(message)s")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from phase1_data_pipeline.store import RestaurantStore
from phase1_data_pipeline.normalizer import normalize_restaurants
from phase2_api.api import create_app

# Test-only sample (same as seed_db_for_manual_testing.py); production uses Phase 1 pipeline + Hugging Face dataset
SAMPLE = [
    {"name": "Jalsa", "address": "942, 21st Main Road, Banashankari, Bangalore",
     "url": "https://www.zomato.com/bangalore/jalsa-banashankari", "location": "Banashankari",
     "listed_in(city)": "Banashankari", "rate": "4.1/5", "votes": 775,
     "approx_cost(for two people)": "800", "cuisines": "North Indian, Mughlai, Chinese",
     "rest_type": "Casual Dining", "online_order": "Yes", "book_table": "Yes",
     "phone": "080 42297555", "dish_liked": "Pasta, Lunch Buffet"},
    {"name": "Spice Elephant", "address": "2nd Floor, 80 Feet Road, Banashankari, Bangalore",
     "url": "https://www.zomato.com/bangalore/spice-elephant-banashankari", "location": "Banashankari",
     "listed_in(city)": "Banashankari", "rate": "4.1/5", "votes": 787,
     "approx_cost(for two people)": "800", "cuisines": "Chinese, North Indian, Thai",
     "rest_type": "Casual Dining", "online_order": "Yes", "book_table": "No",
     "phone": "080 41714161", "dish_liked": "Momos, Lunch Buffet"},
    {"name": "Addhuri Udupi Bhojana", "address": "1st Floor, Annakuteera, Banashankari, Bangalore",
     "url": "https://www.zomato.com/bangalore/addhuri-udupi-bhojana-banashankari", "location": "Banashankari",
     "listed_in(city)": "Banashankari", "rate": "3.7/5", "votes": 88,
     "approx_cost(for two people)": "300", "cuisines": "South Indian, North Indian",
     "rest_type": "Quick Bites", "online_order": "No", "book_table": "No",
     "phone": "+91 9620009302", "dish_liked": "Masala Dosa"},
    {"name": "Koramangala Cafe", "address": "1 MG Road, Koramangala", "url": "https://example.com",
     "location": "Koramangala", "listed_in(city)": "Koramangala", "rate": "4.0/5", "votes": 200,
     "approx_cost(for two people)": "600", "cuisines": "Cafe, Italian", "rest_type": "Cafe",
     "online_order": "Yes", "book_table": "No", "phone": None, "dish_liked": None},
]


def main() -> int:
    db_path = ROOT / "phase1_data_pipeline" / "restaurants.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Seed DB (dataset loading simulation)
    store = RestaurantStore(db_path)
    store.connect()
    store.init_schema()
    store.clear()
    normalized = normalize_restaurants(SAMPLE)
    inserted = store.insert_many(normalized)
    store.close()
    print(f"Seeded {inserted} restaurants at {db_path}\n")

    app = create_app(db_path=db_path)
    client = TestClient(app)

    # 1. No filters -> expect all 4
    print("--- POST /recommend (no filters) ---")
    r = client.post("/recommend", json={})
    assert r.status_code == 200, r.text
    data = r.json()
    restaurants = data["restaurants"]
    assert len(restaurants) == 4, f"expected 4 restaurants, got {len(restaurants)}"
    print(f"OK: got {len(restaurants)} restaurants\n")

    # 2. Location Banashankari -> expect 3
    print("--- POST /recommend (location=Banashankari) ---")
    r = client.post("/recommend", json={"location": "Banashankari"})
    assert r.status_code == 200, r.text
    data = r.json()
    restaurants = data["restaurants"]
    assert len(restaurants) == 3, f"expected 3 for Banashankari, got {len(restaurants)}"
    assert all((r.get("location") or "").lower().find("banashankari") >= 0 for r in restaurants)
    print(f"OK: got {len(restaurants)} restaurants for Banashankari\n")

    # 3. Location Koramangala -> expect 1
    print("--- POST /recommend (location=Koramangala) ---")
    r = client.post("/recommend", json={"location": "Koramangala"})
    assert r.status_code == 200, r.text
    data = r.json()
    restaurants = data["restaurants"]
    assert len(restaurants) == 1, f"expected 1 for Koramangala, got {len(restaurants)}"
    assert restaurants[0].get("name") == "Koramangala Cafe"
    print(f"OK: got {len(restaurants)} restaurant for Koramangala\n")

    # 4. Strict filters (max_cost=250) -> 0 then relax -> expect results
    print("--- POST /recommend (location=Banashankari, max_cost=250) ---")
    r = client.post("/recommend", json={"location": "Banashankari", "max_cost": 250})
    assert r.status_code == 200, r.text
    data = r.json()
    restaurants = data["restaurants"]
    assert data["relaxed"] is True, "expected relaxed=true when strict filters yield 0"
    assert len(restaurants) >= 1, f"expected at least 1 after relax, got {len(restaurants)}"
    print(f"OK: relaxed={data['relaxed']}, got {len(restaurants)} restaurants\n")

    # 5. Validate restaurant shape
    r0 = data["restaurants"][0]
    for key in ("name", "location", "rate", "cost_for_two", "url"):
        assert key in r0, f"missing key {key} in restaurant"

    print("All E2E checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
