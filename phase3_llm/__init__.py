"""
Phase 3: Groq LLM Integration.

Generates a short, readable recommendation summary from filtered restaurants
and user preferences. Falls back to no summary if the API key is missing or the call fails.
"""

from .config import ENV_GROQ_API_KEY, get_api_key
from .client import get_client, create_completion
from .prompt_builder import build_messages
from .response_parser import parse_summary
from .service import generate_summary

__all__ = [
    "ENV_GROQ_API_KEY",
    "get_api_key",
    "get_client",
    "create_completion",
    "build_messages",
    "parse_summary",
    "generate_summary",
]
