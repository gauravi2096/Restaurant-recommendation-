"""
Streamlit app for Zomato Restaurant Recommendations.

Run from repo root: streamlit run streamlit_app.py
Deploy on Streamlit Cloud with this file as the main script.
UI and dataset match the Phase 4 local web app (same filtering, full DB, same look).
"""

from __future__ import annotations

import html
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

# Match Phase 4 web UI (phase4_web_ui/css/styles.css): primary #8B1538, light bg, card grid
PHASE4_CSS = """
<style>
  .streamlit-zomato-topbar {
    background: #8B1538;
    color: #fff;
    padding: 0.75rem 1.5rem;
    margin: -1rem -1rem 1rem -1rem;
    font-size: 1.15rem;
    font-weight: 600;
  }
  [data-testid="stAppViewContainer"] { background: #f5f5f5; }
  [data-testid="stSidebar"] .stButton > button {
    background: #8B1538 !important;
    color: #fff !important;
  }
  [data-testid="stSidebar"] .stButton > button:hover {
    background: #a01842 !important;
  }
  .streamlit-zomato-summary {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }
  .streamlit-zomato-summary p { margin: 0; line-height: 1.6; color: #1a1a1a; white-space: pre-wrap; }
  .streamlit-zomato-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.25rem;
  }
  .streamlit-zomato-card {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 1.25rem;
    transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
  }
  .streamlit-zomato-card:hover {
    background: #fafafa;
    border-color: #8B1538;
    box-shadow: 0 4px 12px rgba(139, 21, 56, 0.08);
  }
  .streamlit-zomato-card h3 { font-size: 1.05rem; font-weight: 600; margin: 0 0 0.35rem 0; }
  .streamlit-zomato-card h3 a { color: #8B1538; text-decoration: none; }
  .streamlit-zomato-card h3 a:hover { text-decoration: underline; }
  .streamlit-zomato-meta { font-size: 0.85rem; color: #555; margin: 0.25rem 0; }
  .streamlit-zomato-cuisines { font-size: 0.9rem; margin: 0.35rem 0 0 0; }
</style>
"""

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


def _render_restaurant_card(r: dict) -> str:
    """HTML for one restaurant card (match Phase 4 js/app.js renderRestaurantCard)."""
    name = html.escape(str(r.get("name") or "Unnamed"))
    location_val = str(r.get("location") or "")
    rate = r.get("rate")
    rate_str = str(rate) if rate is not None else "—"
    cost = r.get("cost_for_two")
    cost_str = f"₹{cost:,}" if cost is not None else "—"
    cuisines_str = html.escape(str(r.get("cuisines") or ""))
    url = r.get("url")
    if url:
        url_esc = html.escape(url, quote=True)
        name_html = f'<a href="{url_esc}" target="_blank" rel="noopener">{name}</a>'
    else:
        name_html = name
    meta = f"{location_val} · Rating {rate_str}/5 · {cost_str} for two"
    meta_esc = html.escape(meta)
    cuisines_block = f'<p class="streamlit-zomato-cuisines">{cuisines_str}</p>' if cuisines_str else ""
    return f"""
    <article class="streamlit-zomato-card">
      <h3 class="streamlit-zomato-card-name">{name_html}</h3>
      <p class="streamlit-zomato-meta">{meta_esc}</p>
      {cuisines_block}
    </article>
    """


def main() -> None:
    st.set_page_config(
        page_title="Zomato Restaurant Recommendations",
        page_icon="🍽️",
        layout="wide",
    )
    st.markdown(PHASE4_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="streamlit-zomato-topbar">◆ Zomato Restaurant Recommendations</div>',
        unsafe_allow_html=True,
    )
    st.caption("Find the best places to eat at your location")

    db_path = Path(os.environ.get("RESTAURANT_DB_PATH", str(DEFAULT_DB)))
    if not db_path.is_file():
        # First-time deploy: run the data pipeline to create the database (lazy import to avoid loading Hugging Face deps when DB exists).
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with st.spinner("First-time setup: loading dataset (this may take a minute)…"):
            try:
                from phase1_data_pipeline.pipeline import run_pipeline
                run_pipeline(db_path=str(db_path), max_rows=None, clear_before=True)
            except Exception as e:
                st.error(f"Could not create database: {e}")
                return
        if not db_path.is_file():
            st.error(f"Database not found at `{db_path}`. Run the data pipeline first: `python -m phase1_data_pipeline`")
            return
        st.success("Dataset loaded. You can now use the filters below.")
        st.rerun()

    store = get_store(db_path)
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
    store = get_store(db_path)
    try:
        result = recommend(store, prefs, top_n=TOP_N, relax_if_empty=False)
    finally:
        store.close()

    restaurants = result["restaurants"]
    summary = result.get("summary")
    relaxed = result.get("relaxed", False)

    if summary:
        st.subheader("Summary")
        st.markdown(
            f'<div class="streamlit-zomato-summary"><p class="streamlit-zomato-summary-text">{html.escape(summary)}</p></div>',
            unsafe_allow_html=True,
        )

    st.subheader("Restaurants")
    if not restaurants:
        st.warning("We couldn't find any restaurants that match your current preferences.")
        return

    if relaxed:
        st.caption("Some filters were relaxed to show results.")

    count_text = f"{len(restaurants)} restaurant{'s' if len(restaurants) != 1 else ''}"
    st.caption(count_text)

    cards_html = "".join(_render_restaurant_card(r) for r in restaurants)
    st.markdown(f'<div class="streamlit-zomato-grid">{cards_html}</div>', unsafe_allow_html=True)


main()
