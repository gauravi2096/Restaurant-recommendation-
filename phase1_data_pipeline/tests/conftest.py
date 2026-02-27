"""Pytest fixtures for Phase 1 tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def sample_raw_rows():
    """Sample raw rows mimicking Hugging Face Zomato dataset columns."""
    return [
        {
            "name": "Jalsa",
            "address": "942, 21st Main Road, Banashankari, Bangalore",
            "url": "https://www.zomato.com/bangalore/jalsa-banashankari",
            "location": "Banashankari",
            "listed_in(city)": "Banashankari",
            "rate": "4.1/5",
            "votes": 775,
            "approx_cost(for two people)": "800",
            "cuisines": "North Indian, Mughlai, Chinese",
            "rest_type": "Casual Dining",
            "online_order": "Yes",
            "book_table": "Yes",
            "phone": "080 42297555",
            "dish_liked": "Pasta, Lunch Buffet, Masala Papad",
        },
        {
            "name": "Spice Elephant",
            "address": "2nd Floor, 80 Feet Road, Banashankari, Bangalore",
            "url": "https://www.zomato.com/bangalore/spice-elephant-banashankari",
            "location": "Banashankari",
            "listed_in(city)": "Banashankari",
            "rate": "4.1/5",
            "votes": 787,
            "approx_cost(for two people)": "800",
            "cuisines": "Chinese, North Indian, Thai",
            "rest_type": "Casual Dining",
            "online_order": "Yes",
            "book_table": "No",
            "phone": "080 41714161",
            "dish_liked": "Momos, Lunch Buffet, Chocolate Nirvana",
        },
        {
            "name": "Addhuri Udupi Bhojana",
            "address": "1st Floor, Annakuteera, Banashankari, Bangalore",
            "url": "https://www.zomato.com/bangalore/addhuri-udupi-bhojana-banashankari",
            "location": "Banashankari",
            "listed_in(city)": "Banashankari",
            "rate": "3.7/5",
            "votes": 88,
            "approx_cost(for two people)": "300",
            "cuisines": "South Indian, North Indian",
            "rest_type": "Quick Bites",
            "online_order": "No",
            "book_table": "No",
            "phone": "+91 9620009302",
            "dish_liked": "Masala Dosa",
        },
        # Edge cases
        {
            "name": "No Rate Place",
            "address": "Some Address",
            "url": "https://example.com",
            "location": "Koramangala",
            "listed_in(city)": "Koramangala",
            "rate": None,
            "votes": 10,
            "approx_cost(for two people)": "500,600",
            "cuisines": "Cafe, Italian",
            "rest_type": "Cafe",
            "online_order": "No",
            "book_table": "No",
            "phone": None,
            "dish_liked": None,
        },
        {
            "name": "",  # invalid: no name
            "address": "Any",
            "url": "https://example.com",
            "location": "HSR",
            "rate": "4.0/5",
            "votes": 100,
            "approx_cost(for two people)": "400",
            "cuisines": "North Indian",
            "rest_type": "Casual Dining",
            "online_order": "Yes",
            "book_table": "No",
        },
    ]


@pytest.fixture
def temp_db_path():
    """Temporary SQLite database path (deleted after test)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)
