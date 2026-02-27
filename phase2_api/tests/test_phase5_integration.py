"""Integration tests for Phase 5 (cache + analytics) when phase5_enhancements is available."""

import pytest

from fastapi.testclient import TestClient

from phase2_api.api import create_app, _phase5_available
from phase5_enhancements.analytics import clear_events


@pytest.fixture
def temp_db_path():
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def client_with_data(temp_db_path):
    from phase1_data_pipeline.store import RestaurantStore
    from phase1_data_pipeline.normalizer import normalize_restaurants
    sample = [
        {"name": "Jalsa", "address": "x", "url": "https://x", "location": "Banashankari",
         "listed_in(city)": "Banashankari", "rate": "4.1/5", "votes": 100,
         "approx_cost(for two people)": "800", "cuisines": "North Indian, Chinese",
         "rest_type": "Casual Dining", "online_order": "Yes", "book_table": "Yes",
         "phone": None, "dish_liked": None},
    ]
    normalized = normalize_restaurants(sample)
    store = RestaurantStore(temp_db_path)
    store.connect()
    store.init_schema()
    store.insert_many(normalized)
    store.close()
    app = create_app(db_path=temp_db_path)
    return TestClient(app)


@pytest.mark.skipif(not _phase5_available, reason="Phase 5 not installed")
class TestPhase5Integration:
    def test_analytics_popular_endpoint_exists(self, client_with_data):
        clear_events()
        r = client_with_data.get("/analytics/popular")
        assert r.status_code == 200
        data = r.json()
        assert "locations" in data
        assert "cuisines" in data
        assert isinstance(data["locations"], list)
        assert isinstance(data["cuisines"], list)

    def test_analytics_popular_after_recommends(self, client_with_data):
        clear_events()
        client_with_data.post("/recommend", json={"location": "Banashankari", "top_n": 5})
        client_with_data.post("/recommend", json={"location": "Banashankari", "top_n": 5})
        client_with_data.post("/recommend", json={"location": "Koramangala", "top_n": 5})
        r = client_with_data.get("/analytics/popular?top_locations=5")
        assert r.status_code == 200
        data = r.json()
        locs = {x["name"]: x["count"] for x in data["locations"]}
        assert locs.get("Banashankari") == 2
        assert locs.get("Koramangala") == 1

    def test_cache_returns_same_response_for_same_request(self, client_with_data):
        body = {"location": "Banashankari", "top_n": 5}
        r1 = client_with_data.post("/recommend", json=body)
        r2 = client_with_data.post("/recommend", json=body)
        assert r1.status_code == 200 and r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        assert d1["restaurants"] == d2["restaurants"]
        assert d1["relaxed"] == d2["relaxed"]
        assert d1["summary"] == d2["summary"]
