"""
Pipeline: orchestrate load -> normalize -> store (one-time or refresh).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .loader import load_zomato_dataset_as_dicts
from .normalizer import normalize_restaurants
from .store import RestaurantStore

logger = logging.getLogger(__name__)


def run_pipeline(
    db_path: str | Path = "restaurants.db",
    dataset_id: str = "ManikaSaini/zomato-restaurant-recommendation",
    split: str = "train",
    max_rows: int | None = None,
    clear_before: bool = True,
    drop_duplicates_by: tuple[str, ...] = ("name", "address"),
    cache_dir: str | Path | None = None,
    **load_kwargs: Any,
) -> dict[str, Any]:
    """
    Run the full Phase 1 pipeline: load dataset -> normalize -> persist.

    Args:
        db_path: Path to SQLite database file.
        dataset_id: Hugging Face dataset id.
        split: Dataset split.
        max_rows: If set, limit rows loaded (for testing or partial refresh).
        clear_before: If True, clear the restaurants table before insert.
        drop_duplicates_by: Keys for deduplication in normalizer.
        cache_dir: Optional path for Hugging Face dataset cache (e.g. project-local).
        **load_kwargs: Passed to load_dataset.

    Returns:
        Summary dict with keys: loaded_rows, normalized_count, inserted_count, db_path.
    """
    logger.info("Starting pipeline: db_path=%s max_rows=%s", db_path, max_rows)
    raw = load_zomato_dataset_as_dicts(
        dataset_id=dataset_id,
        split=split,
        max_rows=max_rows,
        cache_dir=str(cache_dir) if cache_dir else None,
        **load_kwargs,
    )
    loaded_rows = len(raw)
    logger.info("Dataset loaded: %d rows (before normalize)", loaded_rows)
    if not raw:
        logger.warning("No rows loaded")
        return {
            "loaded_rows": 0,
            "normalized_count": 0,
            "inserted_count": 0,
            "db_path": str(Path(db_path).resolve()),
        }

    normalized = normalize_restaurants(raw, drop_duplicates_by=drop_duplicates_by)
    normalized_count = len(normalized)

    store = RestaurantStore(db_path)
    try:
        store.connect()
        store.init_schema()
        if clear_before:
            store.clear()
        inserted_count = store.insert_many(normalized)
    finally:
        store.close()

    result = {
        "loaded_rows": loaded_rows,
        "normalized_count": normalized_count,
        "inserted_count": inserted_count,
        "db_path": str(Path(db_path).resolve()),
    }
    logger.info("Pipeline complete: %s", result)
    return result
