"""
Integration test: call Groq API via generate_summary and verify a non-empty summary.

Requires GROQ_API_KEY in the environment or in project root .env.
Run from project root: pytest phase3_llm/tests/test_integration.py -v
"""

import os
import pytest

from phase3_llm.service import generate_summary


# Sample data matching Phase 2 output shape
SAMPLE_RESTAURANTS = [
    {
        "name": "Jalsa",
        "location": "Banashankari",
        "rate": 4.1,
        "cost_for_two": 800,
        "cuisines": "North Indian, Mughlai, Chinese",
        "dish_liked": "Pasta, Lunch Buffet, Masala Papad",
        "rest_type": "Casual Dining",
        "address": "942, 21st Main Road, Banashankari, Bangalore",
        "url": "https://www.zomato.com/bangalore/jalsa-banashankari",
    },
    {
        "name": "Spice Elephant",
        "location": "Banashankari",
        "rate": 4.1,
        "cost_for_two": 800,
        "cuisines": "Chinese, North Indian, Thai",
        "dish_liked": "Momos, Lunch Buffet, Chocolate Nirvana",
        "rest_type": "Casual Dining",
        "address": "2nd Floor, 80 Feet Road, Banashankari, Bangalore",
        "url": "https://www.zomato.com/bangalore/spice-elephant-banashankari",
    },
]

SAMPLE_PREFERENCES = {
    "location": "Banashankari",
    "min_rating": 4.0,
    "max_cost": 800,
    "cuisines": ["North Indian", "Chinese"],
}


@pytest.mark.integration
def test_generate_summary_returns_non_empty_string():
    """Call Groq via generate_summary; assert we get a non-empty summary back."""
    # Ensure .env is loaded (conftest does this; config.get_api_key also loads it)
    from phase3_llm.config import get_api_key
    key = get_api_key()
    if not key:
        pytest.skip("GROQ_API_KEY not set (add to .env or environment)")

    summary = generate_summary(SAMPLE_RESTAURANTS, SAMPLE_PREFERENCES)

    assert summary is not None, "Expected a summary when API key is set"
    assert isinstance(summary, str), "Summary should be a string"
    assert len(summary.strip()) > 0, "Summary should not be empty"
    # Sanity: summary should mention at least one restaurant or something recommendation-like
    summary_lower = summary.lower()
    assert "jalsa" in summary_lower or "spice" in summary_lower or "restaurant" in summary_lower or "recommend" in summary_lower, (
        "Summary should reference the recommended restaurants or recommendations"
    )
