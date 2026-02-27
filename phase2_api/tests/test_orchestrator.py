"""Tests for the recommendation orchestrator."""

import pytest

from phase2_api.orchestrator import _restaurant_matches_preferences, recommend
from phase2_api.preferences import RecommendPreferences


class TestRestaurantMatchesPreferences:
    """Unit tests for strict post-filter _restaurant_matches_preferences."""

    def test_matches_location(self):
        prefs = RecommendPreferences(location="Marathahalli")
        r = {"location": "Marathahalli", "listed_in_city": "Marathahalli", "rate": 4.0, "cost_for_two": 800, "cuisines": "North Indian"}
        assert _restaurant_matches_preferences(r, prefs) is True

    def test_matches_location_exact(self):
        """Exact match: selected location must equal restaurant location (dropdown shows dataset values)."""
        prefs = RecommendPreferences(location="BTM")
        r = {"location": "BTM", "listed_in_city": "BTM", "rate": 4.0, "cost_for_two": 600, "cuisines": "North Indian"}
        assert _restaurant_matches_preferences(r, prefs) is True
        prefs2 = RecommendPreferences(location="BTM Layout")
        assert _restaurant_matches_preferences(r, prefs2) is False

    def test_fails_location_mismatch(self):
        prefs = RecommendPreferences(location="Marathahalli")
        r = {"location": "Koramangala", "listed_in_city": "Koramangala", "rate": 4.0, "cost_for_two": 800, "cuisines": "North Indian"}
        assert _restaurant_matches_preferences(r, prefs) is False

    def test_matches_cuisine(self):
        prefs = RecommendPreferences(location="X", cuisines=["Asian"])
        r = {"location": "X", "rate": 4.0, "cost_for_two": 800, "cuisines": "Chinese, Asian, Thai"}
        assert _restaurant_matches_preferences(r, prefs) is True

    def test_fails_cuisine_mismatch(self):
        prefs = RecommendPreferences(location="X", cuisines=["Asian"])
        r = {"location": "X", "rate": 4.0, "cost_for_two": 800, "cuisines": "Pizza, Cafe, Italian"}
        assert _restaurant_matches_preferences(r, prefs) is False

    def test_matches_cost_range(self):
        prefs = RecommendPreferences(location="X", min_cost=500, max_cost=1000)
        r = {"location": "X", "rate": 4.0, "cost_for_two": 600, "cuisines": "North Indian"}
        assert _restaurant_matches_preferences(r, prefs) is True

    def test_fails_cost_below_min(self):
        prefs = RecommendPreferences(location="X", min_cost=500, max_cost=1000)
        r = {"location": "X", "rate": 4.0, "cost_for_two": 400, "cuisines": "North Indian"}
        assert _restaurant_matches_preferences(r, prefs) is False

    def test_fails_cost_above_max(self):
        prefs = RecommendPreferences(location="X", min_cost=500, max_cost=1000)
        r = {"location": "X", "rate": 4.0, "cost_for_two": 1200, "cuisines": "North Indian"}
        assert _restaurant_matches_preferences(r, prefs) is False

    def test_matches_min_rating(self):
        prefs = RecommendPreferences(location="X", min_rating=4.0)
        r = {"location": "X", "rate": 4.5, "cost_for_two": 800, "cuisines": "North Indian"}
        assert _restaurant_matches_preferences(r, prefs) is True

    def test_fails_rating_below_min(self):
        prefs = RecommendPreferences(location="X", min_rating=4.0)
        r = {"location": "X", "rate": 3.5, "cost_for_two": 800, "cuisines": "North Indian"}
        assert _restaurant_matches_preferences(r, prefs) is False

    def test_all_filters_must_pass(self):
        prefs = RecommendPreferences(location="Banashankari", min_rating=4.0, max_cost=800, cuisines=["Chinese"])
        r = {"location": "Banashankari", "listed_in_city": "Banashankari", "rate": 4.1, "cost_for_two": 800, "cuisines": "Chinese, North Indian"}
        assert _restaurant_matches_preferences(r, prefs) is True
        r_bad_cuisine = {**r, "cuisines": "Pizza, Italian"}
        assert _restaurant_matches_preferences(r_bad_cuisine, prefs) is False


class TestRecommend:
    def test_returns_restaurants_and_summary_key(self, store_with_data):
        prefs = RecommendPreferences(location="Banashankari")
        result = recommend(store_with_data, prefs, top_n=5)
        assert "restaurants" in result
        assert "summary" in result
        assert "relaxed" in result
        assert isinstance(result["restaurants"], list)
        assert len(result["restaurants"]) >= 1
        # summary is None when Phase 3 has no API key, or a non-empty string when Groq succeeds
        assert result["summary"] is None or (isinstance(result["summary"], str) and len(result["summary"].strip()) > 0)
        assert result["relaxed"] is False

    def test_relaxed_false_when_results_found(self, store_with_data):
        prefs = RecommendPreferences(location="Banashankari", min_rating=3.5)
        result = recommend(store_with_data, prefs, top_n=5)
        assert result["relaxed"] is False
        assert len(result["restaurants"]) >= 1

    def test_relaxed_true_when_constraints_relaxed(self, store_with_data):
        # Strict filters that match nothing, then relax
        prefs = RecommendPreferences(
            location="Banashankari",
            min_rating=5.0,
            max_cost=100,
            cuisines=["Nonexistent Cuisine XYZ"],
        )
        result = recommend(store_with_data, prefs, top_n=5, relax_if_empty=True)
        # After relaxation we may get results from location-only
        assert result["relaxed"] is True
        # Should have tried to fill results
        assert isinstance(result["restaurants"], list)

    def test_no_relax_returns_empty_list(self, store_with_data):
        prefs = RecommendPreferences(location="NonExistentCity999")
        result = recommend(store_with_data, prefs, top_n=5, relax_if_empty=False)
        assert result["restaurants"] == []
        assert result["relaxed"] is False

    def test_respects_top_n(self, store_with_data):
        prefs = RecommendPreferences(location="Banashankari")
        result = recommend(store_with_data, prefs, top_n=2)
        assert len(result["restaurants"]) <= 2

    def test_strict_match_results_satisfy_all_filters(self, store_with_data):
        """With relax_if_empty=False, returned results must satisfy every filter."""
        prefs = RecommendPreferences(
            location="Banashankari",
            min_rating=4.0,
            max_cost=800,
            cuisines=["Chinese"],
            top_n=10,
        )
        result = recommend(store_with_data, prefs, top_n=10, relax_if_empty=False)
        assert result["relaxed"] is False
        for r in result["restaurants"]:
            assert "Banashankari" in (r.get("location") or "") or "Banashankari" in (r.get("listed_in_city") or "")
            assert (r.get("rate") or 0) >= 4.0
            assert (r.get("cost_for_two") or 0) <= 800
            assert "Chinese" in (r.get("cuisines") or "")

    def test_strict_match_empty_when_no_cuisine_match(self, store_with_data):
        """With relax_if_empty=False, impossible cuisine returns empty list."""
        prefs = RecommendPreferences(
            location="Banashankari",
            cuisines=["CuisineThatDoesNotExist123"],
            top_n=10,
        )
        result = recommend(store_with_data, prefs, top_n=10, relax_if_empty=False)
        assert result["restaurants"] == []
        assert result["relaxed"] is False

    def test_strict_match_koramangala_asian_returns_empty(self, store_with_data):
        """Koramangala has only Koramangala Cafe (Cafe, Italian). Asian filter must return 0."""
        prefs = RecommendPreferences(
            location="Koramangala",
            cuisines=["Asian"],
            top_n=10,
        )
        result = recommend(store_with_data, prefs, top_n=10, relax_if_empty=False)
        assert result["restaurants"] == []
        assert result["relaxed"] is False

    def test_strict_match_post_filter_excludes_wrong_cuisine(self, store_with_data):
        """Request Chinese in Banashankari; results must only include restaurants that have Chinese."""
        prefs = RecommendPreferences(
            location="Banashankari",
            cuisines=["Chinese"],
            min_rating=3.5,
            max_cost=900,
            top_n=10,
        )
        result = recommend(store_with_data, prefs, top_n=10, relax_if_empty=False)
        assert result["relaxed"] is False
        for r in result["restaurants"]:
            assert "Chinese" in (r.get("cuisines") or ""), f"Restaurant {r.get('name')} must have Chinese in cuisines"
            assert (r.get("rate") or 0) >= 3.5
            assert (r.get("cost_for_two") or 0) <= 900
