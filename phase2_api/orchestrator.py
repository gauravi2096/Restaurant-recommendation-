"""
Recommendation orchestrator: dataset filtering is the single source of truth.

Flow:
1. Filter the dataset by user preferences (store query + strict post-filter).
2. The filtered list is the only source: it is passed to the LLM for summarization
   and returned to the UI. The LLM cannot add or invent restaurants.
3. UI and summary display only this filtered list.
"""

from __future__ import annotations

import logging
from typing import Any

from phase1_data_pipeline.store import RestaurantStore

from .filter_service import get_recommendations
from .preferences import RecommendPreferences

logger = logging.getLogger(__name__)


def _restaurant_matches_preferences(r: dict[str, Any], prefs: RecommendPreferences) -> bool:
    """Return True only if the restaurant satisfies every non-None preference (strict match)."""
    if prefs.location:
        # Exact match on displayed location only (same as store filter).
        loc_val = (r.get("location") or "").strip()
        loc_norm = "".join(loc_val.split()).lower()
        want_norm = "".join(prefs.location.split()).lower()
        if loc_norm != want_norm:
            return False
    if prefs.min_rating is not None:
        rate = r.get("rate")
        if rate is not None and rate < prefs.min_rating:
            return False
    if prefs.min_cost is not None:
        cost = r.get("cost_for_two")
        if cost is not None and cost < prefs.min_cost:
            return False
    if prefs.max_cost is not None:
        cost = r.get("cost_for_two")
        if cost is not None and cost > prefs.max_cost:
            return False
    if prefs.cuisines:
        cuisines_str = (r.get("cuisines") or "").lower().replace(" ", "")
        for c in prefs.cuisines:
            if c and "".join(c.split()).lower() in cuisines_str:
                break
        else:
            return False
    return True


def _get_llm_summary(filtered_restaurants: list[dict[str, Any]], preferences: RecommendPreferences) -> str | None:
    """
    Generate summary from the filtered list only. The LLM receives only this list;
    it cannot add or invent restaurants. Preferences are used only for optional
    context (e.g. "User searched for: Asian, Marathahalli").
    """
    try:
        from phase3_llm.service import generate_summary
        prefs_dict = preferences.model_dump()
        return generate_summary(filtered_restaurants, prefs_dict)
    except ImportError:
        return None


def recommend(
    store: RestaurantStore,
    preferences: RecommendPreferences,
    top_n: int = 15,
    relax_if_empty: bool = True,
) -> dict[str, Any]:
    """
    Get recommendations: dataset filtering is the single source of truth.
    The filtered list is passed only to the LLM and returned to the UI; the LLM
    cannot add or invent restaurants. If no results and relax_if_empty, retry
    with relaxed constraints (drop cuisines, then min_rating, then cost).

    Returns:
        { "restaurants": [...], "summary": null, "relaxed": bool }
    """
    # Step 1: Filter the dataset (single source of truth)
    raw = get_recommendations(store, preferences, top_n=top_n)
    filtered_restaurants = [r for r in raw if _restaurant_matches_preferences(r, preferences)][:top_n]
    relaxed = False
    logger.info("recommend: filtered dataset has %d restaurants (single source of truth)", len(filtered_restaurants))

    if not filtered_restaurants and relax_if_empty:
        relaxed = True
        logger.info("recommend: no results, relaxing (drop cuisines)")
        prefs_no_cuisine = RecommendPreferences(
            location=preferences.location,
            min_rating=preferences.min_rating,
            min_cost=preferences.min_cost,
            max_cost=preferences.max_cost,
            cuisines=None,
            rest_type=preferences.rest_type,
            online_order=preferences.online_order,
            book_table=preferences.book_table,
        )
        filtered_restaurants = get_recommendations(store, prefs_no_cuisine, top_n=top_n)
        logger.info("recommend: after relax (no cuisines) %d results", len(filtered_restaurants))

    if not filtered_restaurants and relax_if_empty:
        logger.info("recommend: still no results, relaxing (drop min_rating)")
        prefs_no_rating = RecommendPreferences(
            location=preferences.location,
            min_rating=None,
            min_cost=preferences.min_cost,
            max_cost=preferences.max_cost,
            cuisines=None,
            rest_type=preferences.rest_type,
            online_order=preferences.online_order,
            book_table=preferences.book_table,
        )
        filtered_restaurants = get_recommendations(store, prefs_no_rating, top_n=top_n)
        logger.info("recommend: after relax (no min_rating) %d results", len(filtered_restaurants))

    if not filtered_restaurants and relax_if_empty:
        logger.info("recommend: still no results, relaxing (drop cost bounds)")
        prefs_no_cost = RecommendPreferences(
            location=preferences.location,
            min_rating=None,
            min_cost=None,
            max_cost=None,
            cuisines=None,
            rest_type=preferences.rest_type,
            online_order=preferences.online_order,
            book_table=preferences.book_table,
        )
        filtered_restaurants = get_recommendations(store, prefs_no_cost, top_n=top_n)
        logger.info("recommend: after relax (no cost) %d results", len(filtered_restaurants))

    # Step 2: Only the filtered list goes to the LLM (no other source of restaurants)
    summary = _get_llm_summary(filtered_restaurants, preferences) if filtered_restaurants else None
    logger.info("recommend: returning %d restaurants (same list as summary source) relaxed=%s", len(filtered_restaurants), relaxed)

    # Step 3: UI and summary both use this same filtered list
    return {
        "restaurants": filtered_restaurants,
        "summary": summary,
        "relaxed": relaxed,
    }
