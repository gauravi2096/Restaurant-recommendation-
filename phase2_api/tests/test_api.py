"""Tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from phase2_api.api import create_app


@pytest.fixture
def client(temp_db_path):
    """Test client with a temporary empty DB (schema only, no data)."""
    from phase1_data_pipeline.store import RestaurantStore
    store = RestaurantStore(temp_db_path)
    store.connect()
    store.init_schema()
    store.close()
    app = create_app(db_path=temp_db_path)
    return TestClient(app)


@pytest.fixture
def client_with_data(store_with_data, temp_db_path):
    """Test client with store that has sample data (store_with_data already populated temp_db_path)."""
    app = create_app(db_path=temp_db_path)
    return TestClient(app)


class TestHealth:
    def test_health_returns_ok_when_store_exists(self, client_with_data):
        r = client_with_data.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["store"] == "connected"
        assert "restaurants_count" in data

    def test_health_returns_ok_for_empty_store(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["restaurants_count"] == "0"


class TestLocations:
    def test_locations_returns_list_from_dataset(self, client_with_data):
        r = client_with_data.get("/locations")
        assert r.status_code == 200
        data = r.json()
        assert "locations" in data
        assert isinstance(data["locations"], list)
        assert "Banashankari" in data["locations"]
        assert "Koramangala" in data["locations"]

    def test_locations_empty_store_returns_empty_list(self, client):
        r = client.get("/locations")
        assert r.status_code == 200
        assert r.json()["locations"] == []


class TestRecommend:
    def test_recommend_accepts_empty_body(self, client_with_data):
        r = client_with_data.post("/recommend", json={})
        assert r.status_code == 200
        data = r.json()
        assert "restaurants" in data
        assert "summary" in data
        assert "relaxed" in data
        assert isinstance(data["restaurants"], list)

    def test_recommend_with_preferences(self, client_with_data):
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "min_rating": 3.5,
                "max_cost": 800,
                "top_n": 5,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "restaurants" in data
        assert len(data["restaurants"]) <= 5
        if data["restaurants"]:
            assert "name" in data["restaurants"][0]
            assert "rate" in data["restaurants"][0]
            assert "location" in data["restaurants"][0]

    def test_recommend_validates_top_n_bounds(self, client_with_data):
        r = client_with_data.post("/recommend", json={"top_n": 0})
        assert r.status_code == 422
        r = client_with_data.post("/recommend", json={"top_n": 51})
        assert r.status_code == 422
        r = client_with_data.post("/recommend", json={"top_n": 10})
        assert r.status_code == 200

    def test_recommend_validates_min_rating_bounds(self, client_with_data):
        r = client_with_data.post("/recommend", json={"min_rating": -0.1})
        assert r.status_code == 422
        r = client_with_data.post("/recommend", json={"min_rating": 5.1})
        assert r.status_code == 422
        r = client_with_data.post("/recommend", json={"min_rating": 4.0})
        assert r.status_code == 200

    def test_recommend_strict_match_returns_results_when_filters_match(self, client_with_data):
        """Strict matching: when all filters match, returns results and relaxed is False."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "min_rating": 3.5,
                "max_cost": 800,
                "cuisines": ["North Indian"],
                "top_n": 10,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "restaurants" in data
        assert "relaxed" in data
        assert data["relaxed"] is False
        assert len(data["restaurants"]) >= 1
        for rest in data["restaurants"]:
            assert (rest.get("rate") or 0) >= 3.5
            assert (rest.get("cost_for_two") or 0) <= 800
            assert "North Indian" in (rest.get("cuisines") or "")

    def test_recommend_strict_match_returns_empty_when_no_match(self, client_with_data):
        """Strict matching: when no restaurant matches all filters, returns empty list and does not relax."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "NonExistentCity999",
                "min_rating": 4.0,
                "top_n": 10,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["restaurants"] == []
        assert data["relaxed"] is False

    def test_recommend_strict_match_returns_empty_for_impossible_filters(self, client_with_data):
        """Strict matching: impossible combination (e.g. max_cost 1) returns empty, no relaxation."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "max_cost": 1,
                "min_rating": 5.0,
                "top_n": 10,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["restaurants"] == []
        assert data["relaxed"] is False

    def test_recommend_cuisine_filter_excludes_non_matching(self, client_with_data):
        """Requesting Asian in Koramangala (only has Cafe/Italian) returns empty list."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Koramangala",
                "cuisines": ["Asian"],
                "top_n": 10,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["restaurants"] == []
        assert data["relaxed"] is False

    def test_recommend_cost_and_cuisine_both_applied(self, client_with_data):
        """When both cost range and cuisine are sent, every result satisfies both."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "min_cost": 300,
                "max_cost": 800,
                "cuisines": ["North Indian"],
                "top_n": 10,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["relaxed"] is False
        for rest in data["restaurants"]:
            assert "North Indian" in (rest.get("cuisines") or "")
            cost = rest.get("cost_for_two")
            assert cost is not None and 300 <= cost <= 800
