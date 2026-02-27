"""
Groq client: configure client, call chat completion with timeout and retries.
"""

from __future__ import annotations

import logging
from typing import Any

from groq import Groq

from .config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_RETRIES,
    get_api_key,
)

logger = logging.getLogger(__name__)


def get_client(api_key: str | None = None, timeout: float | None = None) -> Groq:
    """Build Groq client. Uses GROQ_API_KEY env if api_key not provided."""
    key = get_api_key(api_key)
    if not key:
        raise ValueError("Groq API key required. Set GROQ_API_KEY or pass api_key.")
    t = timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS
    return Groq(api_key=key, timeout=t)


def create_completion(
    messages: list[dict[str, str]],
    api_key: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    timeout: float | None = None,
) -> str:
    """
    Call Groq chat completion. Returns the assistant message content.
    Raises on missing key, timeout, or API errors.
    """
    client = get_client(api_key=api_key, timeout=timeout)
    model = model or DEFAULT_MODEL
    max_tokens = max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS
    temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            choice = response.choices[0] if response.choices else None
            if not choice or not getattr(choice.message, "content", None):
                return ""
            return (choice.message.content or "").strip()
        except Exception as e:
            last_error = e
            logger.warning("Groq completion attempt %s failed: %s", attempt + 1, e)
            if attempt == MAX_RETRIES:
                raise
    if last_error:
        raise last_error
    return ""
