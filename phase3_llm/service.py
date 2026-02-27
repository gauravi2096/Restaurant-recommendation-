"""
LLM service: generate summary from the filtered restaurant list only.

The filtered list is the single source of truth; the LLM must not add or invent
restaurants. Only the list passed here is used for summarization.
"""

from __future__ import annotations

import logging
from typing import Any

from .client import create_completion
from .config import get_api_key
from .prompt_builder import build_messages
from .response_parser import parse_summary

logger = logging.getLogger(__name__)


def generate_summary(
    restaurants: list[dict[str, Any]],
    preferences: dict[str, Any],
    api_key: str | None = None,
) -> str | None:
    """
    Generate a short summary from the filtered restaurant list only.
    This list is the single source of truth; the LLM cannot add or invent restaurants.

    Args:
        restaurants: The filtered list (only these may appear in the summary).
        preferences: Used only for one-line context in the prompt.
        api_key: Optional Groq API key; otherwise uses GROQ_API_KEY env.

    Returns:
        Summary string, or None if no API key, empty list, or on error.
    """
    if not get_api_key(api_key):
        logger.debug("No Groq API key; skipping summary")
        return None

    if not restaurants:
        logger.debug("No restaurants; skipping summary")
        return None

    try:
        messages = build_messages(restaurants, preferences)
        raw = create_completion(messages=messages, api_key=api_key)
        summary = parse_summary(raw)
        return summary if summary else None
    except Exception as e:
        logger.warning("Groq summary generation failed (fallback to no summary): %s", e)
        return None
