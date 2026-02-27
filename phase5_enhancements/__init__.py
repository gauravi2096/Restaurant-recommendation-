"""
Phase 5: Optional enhancements — response caching and anonymous analytics.
"""

from .cache import RecommendationCache, cache_key_from_request
from .analytics import log_recommend_usage, get_popular, clear_events

__all__ = [
    "RecommendationCache",
    "cache_key_from_request",
    "log_recommend_usage",
    "get_popular",
    "clear_events",
]
