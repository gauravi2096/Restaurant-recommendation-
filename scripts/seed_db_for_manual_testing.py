#!/usr/bin/env python3
"""
TESTING ONLY — DO NOT USE FOR PRODUCTION.

This script populates the DB with hardcoded sample rows. Results from this data
are NOT from the official dataset. For production, results must come strictly
from the Hugging Face dataset; use the Phase 1 pipeline instead:

  python -m phase1_data_pipeline --max-rows N

Dataset: https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from phase1_data_pipeline.store import RestaurantStore
from phase1_data_pipeline.normalizer import normalize_restaurants

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
    {"name": "North Indian Kitchen", "address": "80 Feet Road, JP Nagar", "url": "https://example.com/jpnagar1",
     "location": "JP Nagar", "listed_in(city)": "JP Nagar", "rate": "4.2/5", "votes": 350,
     "approx_cost(for two people)": "700", "cuisines": "North Indian, Mughlai", "rest_type": "Casual Dining",
     "online_order": "Yes", "book_table": "Yes", "phone": None, "dish_liked": "Butter Naan, Dal Makhani"},
    {"name": "Spice Route JP", "address": "Phase 1, JP Nagar", "url": "https://example.com/jpnagar2",
     "location": "JP Nagar", "listed_in(city)": "JP Nagar", "rate": "4.0/5", "votes": 180,
     "approx_cost(for two people)": "550", "cuisines": "North Indian, Chinese", "rest_type": "Casual Dining",
     "online_order": "Yes", "book_table": "No", "phone": None, "dish_liked": None},
]

def main() -> None:
    db_path = ROOT / "phase1_data_pipeline" / "restaurants.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    store = RestaurantStore(db_path)
    store.connect()
    store.init_schema()
    store.clear()
    normalized = normalize_restaurants(SAMPLE)
    n = store.insert_many(normalized)
    store.close()
    print(f"Seeded {n} restaurants at {db_path}")


if __name__ == "__main__":
    main()
