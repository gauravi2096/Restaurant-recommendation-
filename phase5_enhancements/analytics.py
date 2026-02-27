"""
Anonymous analytics: log recommend usage (location, cuisines) and expose popular aggregations.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

# In-memory log of usage events (no PII; only preference keys)
_usage_events: List[Dict[str, Any]] = []


def log_recommend_usage(body: Dict[str, Any]) -> None:
    """Log one recommend request for analytics (location, cuisines only)."""
    event: Dict[str, Any] = {}
    if body.get("location"):
        event["location"] = str(body["location"]).strip()
    if body.get("cuisines"):
        cuisines = body["cuisines"]
        if isinstance(cuisines, list):
            event["cuisines"] = [str(c).strip() for c in cuisines if c]
        else:
            event["cuisines"] = [str(cuisines).strip()]
    if event:
        _usage_events.append(event)


def get_popular(
    top_locations: int = 10,
    top_cuisines: int = 10,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Return aggregated popular locations and cuisines from logged usage.
    Each item is { "name": str, "count": int }, sorted by count descending.
    """
    loc_counter: Counter[str] = Counter()
    cuisine_counter: Counter[str] = Counter()
    for ev in _usage_events:
        if ev.get("location"):
            loc_counter[ev["location"]] += 1
        for c in ev.get("cuisines") or []:
            if c:
                cuisine_counter[c] += 1
    locations = [{"name": k, "count": v} for k, v in loc_counter.most_common(top_locations)]
    cuisines = [{"name": k, "count": v} for k, v in cuisine_counter.most_common(top_cuisines)]
    return {"locations": locations, "cuisines": cuisines}


def clear_events() -> None:
    """Clear all logged events (for tests or reset)."""
    global _usage_events
    _usage_events = []
