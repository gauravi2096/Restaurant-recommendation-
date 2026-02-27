"""
Phase 1: Data Pipeline & Restaurant Store.

Loads Zomato dataset from Hugging Face, normalizes it, and persists to SQLite.
Importing this package does not load the Hugging Face 'datasets' module;
use phase1_data_pipeline.loader or phase1_data_pipeline.pipeline when needed.
"""

from .normalizer import normalize_restaurants, normalize_row
from .store import RestaurantStore

__all__ = [
    "normalize_restaurants",
    "normalize_row",
    "RestaurantStore",
]
