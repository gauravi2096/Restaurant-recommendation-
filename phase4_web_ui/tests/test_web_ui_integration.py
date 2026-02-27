"""
Integration test: Phase 4 UI can call Phase 2 API and get valid response.
Uses Phase 2 TestClient (no live server needed).
"""

import pytest
from fastapi.testclient import TestClient

from phase2_api.api import create_app
from phase1_data_pipeline.store import RestaurantStore
from phase1_data_pipeline.normalizer import normalize_restaurants


@pytest.fixture
def sample_restaurants():
    return [
        {
            "name": "Jalsa",
            "address": "942, Banashankari, Bangalore",
            "url": "https://www.zomato.com/bangalore/jalsa-banashankari",
            "location": "Banashankari",
            "cuisines": "North Indian, Mughlai, Chinese",
            "rest_type": "Casual Dining",
            "rate": 4.1,
            "cost_for_two": 800,
            "votes": 775,
            "online_order": True,
            "book_table": True,
            "phone": None,
            "dish_liked": None,
        },
    ]


@pytest.fixture
def client_with_data(sample_restaurants, tmp_path):
    normalized = normalize_restaurants(sample_restaurants)
    store = RestaurantStore(tmp_path / "test.db")
    store.connect()
    store.init_schema()
    store.insert_many(normalized)
    store.close()
    app = create_app(db_path=tmp_path / "test.db")
    return TestClient(app)


class TestRecommendEndpointForWebUI:
    """Verify POST /recommend returns the shape the Web UI expects."""

    def test_recommend_returns_restaurants_summary_relaxed(self, client_with_data):
        response = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "max_cost": 800,
                "top_n": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "restaurants" in data
        assert "summary" in data
        assert "relaxed" in data
        assert isinstance(data["restaurants"], list)
        assert isinstance(data["relaxed"], bool)

    def test_recommend_restaurant_has_name_location_rate_cost_url(self, client_with_data):
        response = client_with_data.post("/recommend", json={"location": "Banashankari"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["restaurants"]) >= 1
        r = data["restaurants"][0]
        assert "name" in r
        assert "location" in r
        assert "rate" in r
        assert "cost_for_two" in r
        assert "url" in r
