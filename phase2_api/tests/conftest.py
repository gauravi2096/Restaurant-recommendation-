"""Pytest fixtures for Phase 2 API tests."""

import tempfile
from pathlib import Path

import pytest

from phase1_data_pipeline.store import RestaurantStore
from phase1_data_pipeline.normalizer import normalize_restaurants


@pytest.fixture
def sample_raw_rows():
    """Sample raw rows for building store data."""
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
            "dish_liked": "Pasta, Lunch Buffet",
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
            "dish_liked": "Momos, Lunch Buffet",
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
        {
            "name": "Koramangala Cafe",
            "address": "1 MG Road, Koramangala",
            "url": "https://example.com",
            "location": "Koramangala",
            "listed_in(city)": "Koramangala",
            "rate": "4.0/5",
            "votes": 200,
            "approx_cost(for two people)": "600",
            "cuisines": "Cafe, Italian",
            "rest_type": "Cafe",
            "online_order": "Yes",
            "book_table": "No",
            "phone": None,
            "dish_liked": None,
        },
        # Cost formats that used to parse as 1 or 2 (period thousand separator)
        {
            "name": "Premium Place",
            "address": "100 High Street, Banashankari, Bangalore",
            "url": "https://example.com/premium",
            "location": "Banashankari",
            "listed_in(city)": "Banashankari",
            "rate": "4.2/5",
            "votes": 300,
            "approx_cost(for two people)": "1.000",
            "cuisines": "North Indian, Continental",
            "rest_type": "Casual Dining",
            "online_order": "Yes",
            "book_table": "Yes",
            "phone": None,
            "dish_liked": None,
        },
        {
            "name": "Luxury Place",
            "address": "200 Park Ave, Banashankari, Bangalore",
            "url": "https://example.com/luxury",
            "location": "Banashankari",
            "listed_in(city)": "Banashankari",
            "rate": "4.5/5",
            "votes": 500,
            "approx_cost(for two people)": "2.500",
            "cuisines": "North Indian, Mughlai",
            "rest_type": "Fine Dining",
            "online_order": "Yes",
            "book_table": "Yes",
            "phone": None,
            "dish_liked": None,
        },
    ]


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def store_with_data(temp_db_path, sample_raw_rows):
    """RestaurantStore with sample data loaded."""
    normalized = normalize_restaurants(sample_raw_rows)
    store = RestaurantStore(temp_db_path)
    store.connect()
    store.init_schema()
    store.insert_many(normalized)
    yield store
    store.close()
