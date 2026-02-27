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
import streamlit.components.v1 as components
from phase1_data_pipeline.store import RestaurantStore
from phase2_api.preferences import RecommendPreferences
from phase2_api.orchestrator import recommend

DEFAULT_DB = ROOT / "phase1_data_pipeline" / "restaurants.db"
TOP_N = 15

# Zomato-style design tokens (aligned with phase4_web_ui/css/styles.css)
PRIMARY = "#8B1538"
PRIMARY_HOVER = "#a01842"
BG = "#f5f5f5"
SURFACE = "#ffffff"
BORDER = "#e0e0e0"
TEXT = "#1a1a1a"
TEXT_MUTED = "#555"
RADIUS = "12px"
RADIUS_SM = "8px"

# Main app CSS: header, sidebar, main layout, summary card, typography
PHASE4_CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap');
  :root {{
    --zomato-primary: {PRIMARY};
    --zomato-primary-hover: {PRIMARY_HOVER};
    --zomato-bg: {BG};
    --zomato-surface: {SURFACE};
    --zomato-border: {BORDER};
    --zomato-text: {TEXT};
    --zomato-text-muted: {TEXT_MUTED};
    --zomato-radius: {RADIUS};
    --zomato-radius-sm: {RADIUS_SM};
    --zomato-font: "DM Sans", system-ui, -apple-system, sans-serif;
  }}
  [data-testid="stAppViewContainer"] {{
    background: var(--zomato-bg);
    font-family: var(--zomato-font);
  }}
  [data-testid="stAppViewContainer"] > section > div {{
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 0;
    max-width: 1400px;
    margin: 0 auto;
  }}
  .streamlit-zomato-topbar {{
    background: var(--zomato-primary);
    color: #fff;
    padding: 1rem 2rem;
    margin: 0 -2rem 1.5rem -2rem;
    font-family: var(--zomato-font);
    font-size: 1.25rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }}
  .streamlit-zomato-tagline {{
    font-family: var(--zomato-font);
    font-size: 0.95rem;
    color: var(--zomato-text-muted);
    margin: -0.5rem 0 1.5rem 0;
    font-weight: 500;
  }}
  [data-testid="stSidebar"] {{
    background: #e8e8e8 !important;
    border-right: 1px solid var(--zomato-border);
  }}
  [data-testid="stSidebar"] [data-testid="stMarkdown"] {{
    font-family: var(--zomato-font);
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--zomato-text);
    margin-bottom: 0.5rem;
  }}
  [data-testid="stSidebar"] label {{
    font-family: var(--zomato-font) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    color: var(--zomato-text-muted) !important;
  }}
  [data-testid="stSidebar"] .stSelectbox > div {{
    margin-bottom: 1rem;
  }}
  [data-testid="stSidebar"] .stButton > button {{
    background: var(--zomato-primary) !important;
    color: #fff !important;
    font-family: var(--zomato-font) !important;
    font-weight: 600 !important;
    padding: 0.7rem 1.25rem !important;
    border-radius: var(--zomato-radius-sm) !important;
    width: 100%;
    margin-top: 0.25rem;
    border: none !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06);
  }}
  [data-testid="stSidebar"] .stButton > button:hover {{
    background: var(--zomato-primary-hover) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }}
  .zomato-section-title {{
    font-family: var(--zomato-font) !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: var(--zomato-text) !important;
    margin: 0 0 0.75rem 0 !important;
  }}
  .streamlit-zomato-summary {{
    background: var(--zomato-surface);
    border: 1px solid var(--zomato-border);
    border-radius: var(--zomato-radius);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }}
  .streamlit-zomato-summary p {{
    margin: 0;
    line-height: 1.65;
    color: var(--zomato-text);
    font-size: 1rem;
    white-space: pre-wrap;
  }}
  .zomato-results-count {{
    font-family: var(--zomato-font);
    font-size: 0.9rem;
    color: var(--zomato-text-muted);
    margin: -0.25rem 0 1rem 0;
  }}
  .streamlit-zomato-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.25rem;
  }}
  .streamlit-zomato-card {{
    background: var(--zomato-surface);
    border: 1px solid var(--zomato-border);
    border-radius: var(--zomato-radius);
    padding: 1.25rem;
    transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
  }}
  .streamlit-zomato-card:hover {{
    background: #fafafa;
    border-color: var(--zomato-primary);
    box-shadow: 0 4px 12px rgba(139, 21, 56, 0.08);
  }}
  .streamlit-zomato-card h3 {{
    font-size: 1.05rem;
    font-weight: 600;
    margin: 0 0 0.35rem 0;
  }}
  .streamlit-zomato-card h3 a {{
    color: var(--zomato-primary);
    text-decoration: none;
  }}
  .streamlit-zomato-card h3 a:hover {{
    text-decoration: underline;
  }}
  .streamlit-zomato-meta {{
    font-size: 0.85rem;
    color: var(--zomato-text-muted);
    margin: 0.25rem 0;
  }}
  .streamlit-zomato-cuisines {{
    font-size: 0.9rem;
    color: var(--zomato-text);
    margin: 0.35rem 0 0 0;
  }}
</style>
"""

# CSS for restaurant grid iframe (same design tokens, self-contained)
GRID_IFRAME_CSS = f"""
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: "DM Sans", system-ui, sans-serif; background: transparent; font-size: 16px; line-height: 1.5; }}
  .streamlit-zomato-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.25rem;
    padding: 0;
  }}
  .streamlit-zomato-card {{
    background: #fff;
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    padding: 1.25rem;
    transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
  }}
  .streamlit-zomato-card:hover {{
    background: #fafafa;
    border-color: {PRIMARY};
    box-shadow: 0 4px 12px rgba(139, 21, 56, 0.08);
  }}
  .streamlit-zomato-card h3 {{
    font-size: 1.05rem;
    font-weight: 600;
    margin: 0 0 0.35rem 0;
    color: #1a1a1a;
  }}
  .streamlit-zomato-card h3 a {{
    color: {PRIMARY};
    text-decoration: none;
  }}
  .streamlit-zomato-card h3 a:hover {{
    text-decoration: underline;
  }}
  .streamlit-zomato-meta {{
    font-size: 0.85rem;
    color: #555;
    margin: 0.25rem 0;
  }}
  .streamlit-zomato-cuisines {{
    font-size: 0.9rem;
    color: #1a1a1a;
    margin: 0.35rem 0 0 0;
  }}
  @media (max-width: 640px) {{
    .streamlit-zomato-grid {{ grid-template-columns: 1fr; }}
  }}
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
    """HTML for one restaurant card (match Phase 4 js/app.js renderRestaurantCard).
    Returns a single line so st.markdown(unsafe_allow_html=True) does not treat
    subsequent lines as Markdown code blocks."""
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
    return f'<article class="streamlit-zomato-card"><h3 class="streamlit-zomato-card-name">{name_html}</h3><p class="streamlit-zomato-meta">{meta_esc}</p>{cuisines_block}</article>'


def main() -> None:
    st.set_page_config(
        page_title="Zomato Restaurant Recommendations",
        page_icon="🍽️",
        layout="wide",
    )
    st.markdown(PHASE4_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="streamlit-zomato-topbar">◆ Zomato Restaurant Recommendations</div>'
        '<p class="streamlit-zomato-tagline">Find the best places to eat at your location</p>',
        unsafe_allow_html=True,
    )

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
        st.markdown('<h2 class="zomato-section-title">Summary</h2>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="streamlit-zomato-summary"><p class="streamlit-zomato-summary-text">{html.escape(summary)}</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<h2 class="zomato-section-title">Restaurants</h2>', unsafe_allow_html=True)
    if not restaurants:
        st.warning("We couldn't find any restaurants that match your current preferences.")
        return

    if relaxed:
        st.caption("Some filters were relaxed to show results.")

    count_text = f"{len(restaurants)} restaurant{'s' if len(restaurants) != 1 else ''}"
    st.markdown(f'<p class="zomato-results-count">{count_text}</p>', unsafe_allow_html=True)

    cards_html = "".join(_render_restaurant_card(r) for r in restaurants)
    grid_doc = f"""<!DOCTYPE html><html><head><style>{GRID_IFRAME_CSS}</style></head><body><div class="streamlit-zomato-grid">{cards_html}</div></body></html>"""
    components.html(grid_doc, height=min(800, 200 + len(restaurants) * 140), scrolling=True)


main()
