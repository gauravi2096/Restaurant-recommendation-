"""Tests for Phase 5 anonymous analytics."""

import pytest

from phase5_enhancements.analytics import (
    log_recommend_usage,
    get_popular,
    clear_events,
)


@pytest.fixture(autouse=True)
def reset_analytics():
    clear_events()
    yield
    clear_events()


class TestLogAndPopular:
    def test_empty_events_returns_empty_popular(self):
        out = get_popular()
        assert out["locations"] == []
        assert out["cuisines"] == []

    def test_log_location_only(self):
        log_recommend_usage({"location": "Banashankari"})
        log_recommend_usage({"location": "Banashankari"})
        log_recommend_usage({"location": "Koramangala"})
        out = get_popular(top_locations=5)
        assert len(out["locations"]) == 2
        names = [x["name"] for x in out["locations"]]
        counts = [x["count"] for x in out["locations"]]
        assert "Banashankari" in names
        assert "Koramangala" in names
        assert 2 in counts
        assert 1 in counts

    def test_log_cuisines_only(self):
        log_recommend_usage({"cuisines": ["North Indian", "Chinese"]})
        log_recommend_usage({"cuisines": ["North Indian"]})
        out = get_popular(top_cuisines=5)
        assert any(x["name"] == "North Indian" and x["count"] == 2 for x in out["cuisines"])
        assert any(x["name"] == "Chinese" and x["count"] == 1 for x in out["cuisines"])

    def test_top_n_limits_results(self):
        for loc in ["A", "B", "C"]:
            log_recommend_usage({"location": loc})
        out = get_popular(top_locations=2)
        assert len(out["locations"]) == 2
        out2 = get_popular(top_locations=10)
        assert len(out2["locations"]) == 3

    def test_clear_events_resets(self):
        log_recommend_usage({"location": "X"})
        clear_events()
        out = get_popular()
        assert out["locations"] == []
        assert out["cuisines"] == []
