"""
In-memory cache for recommendation responses.
Cache key = hash of canonical request params (location, min_rating, cost, cuisines, top_n, etc.).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional


def _canonical_params(body: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize request body for stable hashing (sorted lists, omit None)."""
    out: Dict[str, Any] = {}
    for k, v in body.items():
        if v is None:
            continue
        if k == "cuisines" and isinstance(v, list):
            out[k] = sorted(str(x) for x in v)
        else:
            out[k] = v
    return out


def cache_key_from_request(body: Dict[str, Any]) -> str:
    """Produce a stable cache key from the recommend request body."""
    canonical = _canonical_params(body)
    blob = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


class RecommendationCache:
    """LRU-style in-memory cache for recommend responses (restaurants, summary, relaxed)."""

    def __init__(self, max_size: int = 100):
        self._max_size = max(1, max_size)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._order: list[str] = []

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Return cached result if present."""
        if key not in self._data:
            return None
        # Move to end (most recently used)
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)
        return self._data[key]

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Store result; evict oldest if over capacity."""
        if key in self._data:
            self._order.remove(key)
        elif len(self._data) >= self._max_size and self._order:
            oldest = self._order.pop(0)
            del self._data[oldest]
        self._data[key] = value
        self._order.append(key)

    def clear(self) -> None:
        """Clear all entries."""
        self._data.clear()
        self._order.clear()

    def __len__(self) -> int:
        return len(self._data)
