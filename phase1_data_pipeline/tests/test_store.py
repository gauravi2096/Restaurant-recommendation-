"""Tests for the restaurant store."""

import pytest

from phase1_data_pipeline.store import RestaurantStore
from phase1_data_pipeline.normalizer import normalize_restaurants


@pytest.fixture
def store(temp_db_path):
    s = RestaurantStore(temp_db_path)
    s.connect()
    s.init_schema()
    yield s
    s.close()


@pytest.fixture
def sample_normalized(sample_raw_rows):
    rows = [r for r in sample_raw_rows if r.get("name")]
    return normalize_restaurants(rows)


class TestRestaurantStore:
    def test_init_schema_creates_table_and_indexes(self, store):
        store.init_schema()
        count = store.count()
        assert count == 0

    def test_insert_many_and_count(self, store, sample_normalized):
        n = store.insert_many(sample_normalized)
        assert n == len(sample_normalized)
        assert store.count() == n

    def test_insert_empty_returns_zero(self, store):
        assert store.insert_many([]) == 0
        assert store.count() == 0

    def test_clear_removes_all(self, store, sample_normalized):
        store.insert_many(sample_normalized)
        assert store.count() == len(sample_normalized)
        deleted = store.clear()
        assert deleted == len(sample_normalized)
        assert store.count() == 0

    def test_get_by_id(self, store, sample_normalized):
        store.insert_many(sample_normalized)
        row = store.get_by_id(1)
        assert row is not None
        assert row["id"] == 1
        assert "name" in row
        assert row["rate"] is not None or "rate" in row
        assert store.get_by_id(99999) is None

    def test_query_by_location(self, store, sample_normalized):
        store.insert_many(sample_normalized)
        results = store.query(location="Banashankari", limit=10)
        assert len(results) >= 1
        for r in results:
            assert (r.get("location") or "").strip() == "Banashankari"

    def test_query_by_location_flexible_spacing(self, store):
        """JP Nagar / J P Nagar: flexible token matching matches dataset spacing."""
        row = [
            {
                "name": "Test Cafe",
                "address": "x",
                "url": "https://x",
                "location": "J P Nagar",
                "listed_in(city)": "J P Nagar",
                "rate": "4.0/5",
                "votes": 100,
                "approx_cost(for two people)": "500",
                "cuisines": "Cafe",
                "rest_type": "Cafe",
                "online_order": "Yes",
                "book_table": "No",
                "phone": None,
                "dish_liked": None,
            }
        ]
        norm = normalize_restaurants(row)
        store.insert_many(norm)
        results = store.query(location="JP Nagar", limit=10)
        assert len(results) == 1
        assert results[0].get("location") == "J P Nagar"

    def test_query_by_location_exact_match(self, store):
        """Exact match: only rows whose location equals the selected value (dropdown shows dataset locations)."""
        row = [
            {
                "name": "BTM Eats",
                "address": "BTM 2nd Stage",
                "url": "https://example.com",
                "location": "BTM",
                "listed_in(city)": "BTM",
                "rate": "4.0/5",
                "votes": 100,
                "approx_cost(for two people)": "600",
                "cuisines": "North Indian",
                "rest_type": "Casual Dining",
                "online_order": "Yes",
                "book_table": "No",
                "phone": None,
                "dish_liked": None,
            }
        ]
        norm = normalize_restaurants(row)
        store.insert_many(norm)
        results = store.query(location="BTM", limit=10)
        assert len(results) == 1
        assert results[0].get("location") == "BTM"
        assert results[0].get("name") == "BTM Eats"
        results_wrong = store.query(location="Jayanagar", limit=10)
        assert len(results_wrong) == 0

    def test_query_by_min_rate(self, store, sample_normalized):
        store.insert_many(sample_normalized)
        results = store.query(min_rate=4.0, limit=10)
        # Rows with NULL rate are included; rows with rate must be >= 4.0
        assert all(r.get("rate") is None or r.get("rate") >= 4.0 for r in results)

    def test_query_by_max_cost(self, store, sample_normalized):
        store.insert_many(sample_normalized)
        results = store.query(max_cost=400, limit=10)
        assert all(r.get("cost_for_two") is None or r.get("cost_for_two") <= 400 for r in results)

    def test_query_by_min_cost(self, store, sample_normalized):
        store.insert_many(sample_normalized)
        results = store.query(min_cost=500, limit=10)
        assert all(r.get("cost_for_two") is None or r.get("cost_for_two") >= 500 for r in results)

    def test_cost_for_two_period_thousand_separator_stored_and_filtered(self, store):
        """Raw '1.000' and '2.500' parse to 1000 and 2500; store returns them and price filtering works."""
        raw_rows = [
            {
                "name": "Thousand Rupees Place",
                "address": "Addr 1",
                "url": "https://x",
                "location": "Koramangala",
                "listed_in(city)": "Koramangala",
                "rate": "4.0/5",
                "votes": 100,
                "approx_cost(for two people)": "1.000",
                "cuisines": "North Indian",
                "rest_type": "Casual Dining",
                "online_order": "Yes",
                "book_table": "No",
                "phone": None,
                "dish_liked": None,
            },
            {
                "name": "Twenty Five Hundred Place",
                "address": "Addr 2",
                "url": "https://x",
                "location": "Koramangala",
                "listed_in(city)": "Koramangala",
                "rate": "4.2/5",
                "votes": 200,
                "approx_cost(for two people)": "2.500",
                "cuisines": "North Indian",
                "rest_type": "Fine Dining",
                "online_order": "Yes",
                "book_table": "Yes",
                "phone": None,
                "dish_liked": None,
            },
        ]
        normalized = normalize_restaurants(raw_rows)
        store.insert_many(normalized)
        all_results = store.query(limit=10)
        by_name = {r["name"]: r.get("cost_for_two") for r in all_results}
        assert by_name.get("Thousand Rupees Place") == 1000, f"Expected 1000, got {by_name}"
        assert by_name.get("Twenty Five Hundred Place") == 2500, f"Expected 2500, got {by_name}"
        # Price filter min_cost=2000 should return only the 2500 restaurant
        high = store.query(location="Koramangala", min_cost=2000, limit=10)
        assert len(high) >= 1
        assert all(r.get("cost_for_two") is None or r.get("cost_for_two") >= 2000 for r in high)
        assert any(r.get("name") == "Twenty Five Hundred Place" for r in high)

    def test_query_by_cuisine_contains(self, store, sample_normalized):
        store.insert_many(sample_normalized)
        results = store.query(cuisine_contains="North Indian", limit=10)
        assert len(results) >= 1
        assert any("North Indian" in (r.get("cuisines") or "") for r in results)

    def test_query_limit(self, store, sample_normalized):
        store.insert_many(sample_normalized)
        results = store.query(limit=2)
        assert len(results) <= 2

    def test_context_manager(self, temp_db_path):
        with RestaurantStore(temp_db_path) as s:
            s.init_schema()
            assert s.count() == 0
