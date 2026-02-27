"""
Dataset loader: loads Zomato restaurant data from Hugging Face.
"""

from __future__ import annotations

import logging
from typing import Any

from datasets import load_dataset

logger = logging.getLogger(__name__)

DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"
SPLIT = "train"


def load_zomato_dataset(
    dataset_id: str = DATASET_ID,
    split: str = SPLIT,
    streaming: bool = False,
    trust_remote_code: bool = False,
    cache_dir: str | None = None,
    **load_kwargs: Any,
) -> Any:
    """
    Load the Zomato restaurant recommendation dataset from Hugging Face.

    Args:
        dataset_id: Hugging Face dataset identifier.
        split: Dataset split to load (e.g. 'train').
        streaming: If True, return an iterable dataset (for very large data).
        trust_remote_code: Passed to load_dataset.
        cache_dir: Optional directory for dataset cache (avoids writing to ~/.cache).
        **load_kwargs: Additional arguments for load_dataset.

    Returns:
        Hugging Face Dataset (or IterableDataset if streaming=True).

    Raises:
        Exception: On network or dataset load errors.
    """
    logger.info("Loading dataset %s split=%s", dataset_id, split)
    kwargs = dict(load_kwargs)
    if cache_dir is not None:
        kwargs["cache_dir"] = cache_dir
    dataset = load_dataset(
        dataset_id,
        split=split,
        streaming=streaming,
        trust_remote_code=trust_remote_code,
        **kwargs,
    )
    if hasattr(dataset, "__len__"):
        logger.info("Loaded %d rows", len(dataset))
    return dataset


def load_zomato_dataset_as_dicts(
    dataset_id: str = DATASET_ID,
    split: str = SPLIT,
    max_rows: int | None = None,
    cache_dir: str | None = None,
    **load_kwargs: Any,
) -> list[dict[str, Any]]:
    """
    Load the dataset and return a list of row dictionaries.

    Args:
        dataset_id: Hugging Face dataset identifier.
        split: Dataset split.
        max_rows: If set, limit number of rows (useful for testing).

    Returns:
        List of dicts, one per row.
    """
    dataset = load_zomato_dataset(
        dataset_id=dataset_id,
        split=split,
        streaming=False,
        cache_dir=cache_dir,
        **load_kwargs,
    )
    if max_rows is not None:
        dataset = dataset.select(range(min(max_rows, len(dataset))))
    return [dict(row) for row in dataset]
