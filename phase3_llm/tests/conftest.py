"""Load .env from project root so GROQ_API_KEY is available for integration tests."""

from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load .env from project root before any test that needs the API key."""
    try:
        from dotenv import load_dotenv
        root = Path(__file__).resolve().parent.parent.parent
        load_dotenv(root / ".env")
    except ImportError:
        pass
