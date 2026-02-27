"""
Phase 3 config: model, timeouts, and env key name.
Loads .env from project root so GROQ_API_KEY can be set in a .env file.
"""

from __future__ import annotations

import os
from pathlib import Path

# Load .env from project root (parent of phase3_llm)
_env_loaded = False


def _load_dotenv() -> None:
    global _env_loaded
    if _env_loaded:
        return
    try:
        from dotenv import load_dotenv
        root = Path(__file__).resolve().parent.parent
        load_dotenv(root / ".env")
        _env_loaded = True
    except ImportError:
        _env_loaded = True

# Env var for Groq API key (set in env or in .env file)
ENV_GROQ_API_KEY = "GROQ_API_KEY"

# Default model for chat completion (fast and capable)
DEFAULT_MODEL = "llama-3.1-8b-instant"

# Request limits
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.3

# Retries on transient errors
MAX_RETRIES = 2


def get_api_key(api_key: str | None = None) -> str | None:
    """Return API key from argument or from env GROQ_API_KEY (loads .env if present)."""
    _load_dotenv()
    if api_key is not None and api_key.strip():
        return api_key.strip()
    return os.environ.get(ENV_GROQ_API_KEY) or None
