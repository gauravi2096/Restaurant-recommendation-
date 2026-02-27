"""
CLI to test Phase 3 summary generation (requires GROQ_API_KEY in .env or env).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Load .env from project root so GROQ_API_KEY is available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


def main() -> int:
    if not os.environ.get("GROQ_API_KEY"):
        print("Set GROQ_API_KEY in the environment to run this script.", file=sys.stderr)
        return 1

    from phase3_llm.service import generate_summary

    # Sample data for a quick test
    restaurants = [
        {
            "name": "Jalsa",
            "location": "Banashankari",
            "rate": 4.1,
            "cost_for_two": 800,
            "cuisines": "North Indian, Mughlai, Chinese",
            "dish_liked": "Pasta, Lunch Buffet, Masala Papad",
            "rest_type": "Casual Dining",
        },
        {
            "name": "Spice Elephant",
            "location": "Banashankari",
            "rate": 4.1,
            "cost_for_two": 800,
            "cuisines": "Chinese, North Indian, Thai",
            "dish_liked": "Momos, Lunch Buffet",
            "rest_type": "Casual Dining",
        },
    ]
    preferences = {
        "location": "Banashankari",
        "min_rating": 4.0,
        "max_cost": 800,
        "cuisines": ["North Indian", "Chinese"],
    }

    print("Calling Groq to generate summary...")
    summary = generate_summary(restaurants, preferences)
    if summary:
        print("Summary:", summary)
        return 0
    print("No summary returned (check logs).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
