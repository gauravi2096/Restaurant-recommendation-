"""
Phase 1: Data Pipeline & Restaurant Store.

Loads Zomato dataset from Hugging Face, normalizes it, and persists to SQLite.
"""

from .loader import load_zomato_dataset, load_zomato_dataset_as_dicts
from .normalizer import normalize_restaurants, normalize_row
from .store import RestaurantStore
from .pipeline import run_pipeline

__all__ = [
    "load_zomato_dataset",
    "load_zomato_dataset_as_dicts",
    "normalize_restaurants",
    "normalize_row",
    "RestaurantStore",
    "run_pipeline",
]
