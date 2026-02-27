"""
Phase 2: Backend API & Recommendation Engine.

Exposes REST API (POST /recommend, GET /health) and filters restaurants
by user preferences using the Phase 1 store.
"""

from .api import create_app, app
from .preferences import RecommendPreferences
from .filter_service import get_recommendations
from .orchestrator import recommend

__all__ = [
    "create_app",
    "app",
    "RecommendPreferences",
    "get_recommendations",
    "recommend",
]
