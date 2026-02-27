"""Tests for the filter service."""

import pytest

from phase2_api.filter_service import get_recommendations
from phase2_api.preferences import RecommendPreferences


class TestGetRecommendations:
    def test_returns_top_n(self, store_with_data):
        prefs = RecommendPreferences(location="Banashankari")
        results = get_recommendations(store_with_data, prefs, top_n=2)
        assert len(results) <= 2
        assert len(results) >= 1
        assert all("name" in r and "rate" in r for r in results)

    def test_filters_by_location(self, store_with_data):
        prefs = RecommendPreferences(location="Banashankari")
        results = get_recommendations(store_with_data, prefs, top_n=10)
        assert all("Banashankari" in (r.get("location") or "") for r in results)

    def test_filters_by_min_rating(self, store_with_data):
        prefs = RecommendPreferences(location="Banashankari", min_rating=4.0)
        results = get_recommendations(store_with_data, prefs, top_n=10)
        assert all((r.get("rate") or 0) >= 4.0 for r in results)

    def test_filters_by_max_cost(self, store_with_data):
        prefs = RecommendPreferences(location="Banashankari", max_cost=400)
        results = get_recommendations(store_with_data, prefs, top_n=10)
        assert all((r.get("cost_for_two") or 0) <= 400 for r in results)

    def test_filters_by_cuisine(self, store_with_data):
        prefs = RecommendPreferences(
            location="Banashankari",
            cuisines=["North Indian"],
        )
        results = get_recommendations(store_with_data, prefs, top_n=10)
        assert len(results) >= 1
        assert any("North Indian" in (r.get("cuisines") or "") for r in results)

    def test_no_match_returns_empty(self, store_with_data):
        prefs = RecommendPreferences(location="NonExistentCity12345")
        results = get_recommendations(store_with_data, prefs, top_n=10)
        assert results == []

    def test_multiple_cuisines_merged_and_deduped(self, store_with_data):
        prefs = RecommendPreferences(
            location="Banashankari",
            cuisines=["North Indian", "Chinese"],
        )
        results = get_recommendations(store_with_data, prefs, top_n=10)
        ids = [r["id"] for r in results]
        assert len(ids) == len(set(ids))
