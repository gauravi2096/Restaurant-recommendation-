"""
Filter & rank service: query restaurant store and return top N candidates.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from phase1_data_pipeline.store import RestaurantStore

from .preferences import RecommendPreferences

logger = logging.getLogger(__name__)

DEFAULT_TOP_N = 15


def get_recommendations(
    store: RestaurantStore,
    preferences: RecommendPreferences,
    top_n: int = DEFAULT_TOP_N,
) -> list[dict[str, Any]]:
    """
    Query the store with user preferences and return ranked results.

    If multiple cuisines are given, we query once per cuisine and merge
    (by store order: rate DESC, votes DESC), then dedupe by id and take top_n.
    """
    total_in_store = store.count()
    logger.info("get_recommendations: store total count = %d, top_n = %d", total_in_store, top_n)

    # Request more than top_n so we have enough after ranking; ensures diverse results per search
    kwargs = preferences.to_filter_kwargs(limit=max(top_n * 3, 50))
    logger.info("get_recommendations: filter kwargs = %s", kwargs)

    cuisine_list = preferences.cuisines

    if not cuisine_list:
        results = store.query(**kwargs)
        logger.info("get_recommendations: after single query count = %d", len(results))
        return results[:top_n]

    seen_ids: set[int] = set()
    merged: list[dict[str, Any]] = []
    for cuisine in cuisine_list:
        kwargs["cuisine_contains"] = cuisine
        part = store.query(**kwargs)
        logger.info("get_recommendations: cuisine %r -> %d results", cuisine, len(part))
        for r in part:
            rid = r.get("id")
            if rid is not None and rid not in seen_ids:
                seen_ids.add(rid)
                merged.append(r)
        if len(merged) >= top_n:
            break
    logger.info("get_recommendations: merged total = %d", len(merged))
    return merged[:top_n]
