"""
Streamlit app for Zomato Restaurant Recommendations.

Run from repo root: streamlit run streamlit_app.py
Deploy on Streamlit Cloud with this file as the main script.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is on path (for phase1_data_pipeline, phase2_api, phase3_llm)
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from phase1_data_pipeline.store import RestaurantStore
from phase2_api.preferences import RecommendPreferences
from phase2_api.orchestrator import recommend

DEFAULT_DB = ROOT / "phase1_data_pipeline" / "restaurants.db"
TOP_N = 15

# Price range options: (label, min_cost, max_cost) — None means no bound
PRICE_RANGES = [
    ("Any", None, None),
    ("Under ₹250", None, 250),
    ("₹250 – ₹500", 250, 500),
    ("₹500 – ₹1000", 500, 1000),
    ("₹1000 – ₹1500", 1000, 1500),
    ("₹1500 – ₹2000", 1500, 2000),
    ("Above ₹2000", 2000, None),
]


def get_store(db_path: Path) -> RestaurantStore:
    store = RestaurantStore(db_path)
    store.connect()
    return store


def load_locations(store: RestaurantStore) -> list[str]:
    return store.get_distinct_locations()


def load_cuisines(store: RestaurantStore) -> list[str]:
    return store.get_distinct_cuisines()


def main() -> None:
    st.set_page_config(
        page_title="Zomato Restaurant Recommendations",
        page_icon="🍽️",
        layout="wide",
    )
    st.title("🍽️ Zomato Restaurant Recommendations")
    st.caption("Find the best places to eat at your location")

    db_path = os.environ.get("RESTAURANT_DB_PATH", str(DEFAULT_DB))
    if not Path(db_path).is_file():
        st.error(f"Database not found at `{db_path}`. Run the data pipeline first: `python -m phase1_data_pipeline`")
        return

    store = get_store(Path(db_path))
    try:
        locations = load_locations(store)
        cuisines = load_cuisines(store)
    finally:
        store.close()

    with st.sidebar:
        st.subheader("Filters")
        location = st.selectbox(
            "Location",
            options=[None] + locations,
            format_func=lambda x: "Any" if x is None else x,
            key="location",
        )
        price_label = st.selectbox(
            "Price range (for two)",
            options=range(len(PRICE_RANGES)),
            format_func=lambda i: PRICE_RANGES[i][0],
            key="price",
        )
        min_cost, max_cost = PRICE_RANGES[price_label][1], PRICE_RANGES[price_label][2]
        min_rating_choice = st.selectbox(
            "Minimum rating",
            options=["Any", "3.0", "3.5", "4.0", "4.5", "5.0"],
            key="min_rating",
        )
        min_rating = None if min_rating_choice == "Any" else float(min_rating_choice)
        cuisine = st.selectbox(
            "Cuisine",
            options=[None] + cuisines,
            format_func=lambda x: "Any" if x is None else x,
            key="cuisine",
        )
        submitted = st.button("Get recommendations")

    if not submitted:
        st.info("Set your preferences in the sidebar and click **Get recommendations**.")
        return

    prefs = RecommendPreferences(
        location=location or None,
        min_rating=float(min_rating) if min_rating is not None else None,
        min_cost=min_cost,
        max_cost=max_cost,
        cuisines=[cuisine] if cuisine else None,
    )
    store = get_store(Path(db_path))
    try:
        result = recommend(store, prefs, top_n=TOP_N, relax_if_empty=False)
    finally:
        store.close()

    restaurants = result["restaurants"]
    summary = result.get("summary")
    relaxed = result.get("relaxed", False)

    if summary:
        st.subheader("Summary")
        st.write(summary)
        st.divider()

    st.subheader("Restaurants")
    if not restaurants:
        st.warning("We couldn't find any restaurants that match your current preferences.")
        return

    if relaxed:
        st.caption("Some filters were relaxed to show results.")

    st.caption(f"{len(restaurants)} restaurant{'s' if len(restaurants) != 1 else ''}")

    for r in restaurants:
        name = r.get("name") or "Unnamed"
        location_val = r.get("location") or ""
        rate = r.get("rate")
        cost = r.get("cost_for_two")
        cuisines_str = r.get("cuisines") or ""
        url = r.get("url")

        rate_str = f"{rate}/5" if rate is not None else "—"
        cost_str = f"₹{cost:,}" if cost is not None else "—"
        meta = f"{location_val} · Rating {rate_str} · {cost_str} for two"
        with st.container():
            if url:
                st.markdown(f"### [{name}]({url})")
            else:
                st.markdown(f"### {name}")
            st.caption(meta)
            if cuisines_str:
                st.write(cuisines_str)
            st.divider()


main()
