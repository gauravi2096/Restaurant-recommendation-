"""Tests for preferences validation and normalization."""

import pytest
from pydantic import ValidationError

from phase2_api.preferences import RecommendPreferences


class TestRecommendPreferences:
    def test_empty_preferences(self):
        p = RecommendPreferences()
        assert p.location is None
        assert p.min_rating is None
        assert p.max_cost is None
        assert p.cuisines is None
        assert p.to_filter_kwargs(limit=10) == {"limit": 10}

    def test_location_normalized(self):
        p = RecommendPreferences(location="  Banashankari  ")
        assert p.location == "Banashankari"
        assert p.to_filter_kwargs(limit=5)["location"] == "Banashankari"

    def test_empty_location_becomes_none(self):
        p = RecommendPreferences(location="   ")
        assert p.location is None

    def test_min_rating_bounds(self):
        RecommendPreferences(min_rating=0)
        RecommendPreferences(min_rating=5)
        RecommendPreferences(min_rating=3.5)
        with pytest.raises(ValidationError):
            RecommendPreferences(min_rating=-0.1)
        with pytest.raises(ValidationError):
            RecommendPreferences(min_rating=5.1)

    def test_cost_non_negative(self):
        RecommendPreferences(min_cost=0, max_cost=1000)
        with pytest.raises(ValidationError):
            RecommendPreferences(min_cost=-1)
        with pytest.raises(ValidationError):
            RecommendPreferences(max_cost=-1)

    def test_cuisines_list(self):
        p = RecommendPreferences(cuisines=["North Indian", "Chinese"])
        assert p.cuisines == ["North Indian", "Chinese"]
        kwargs = p.to_filter_kwargs(limit=5)
        assert kwargs["limit"] == 5
        # cuisine_contains is applied per-cuisine in filter_service, not in to_filter_kwargs
        assert "cuisine_contains" not in kwargs

    def test_cuisines_string_parsed(self):
        p = RecommendPreferences(cuisines="North Indian, Chinese; Thai")
        assert "North Indian" in p.cuisines
        assert "Chinese" in p.cuisines
        assert "Thai" in p.cuisines

    def test_to_filter_kwargs_includes_all_set_fields(self):
        p = RecommendPreferences(
            location="BSK",
            min_rating=4.0,
            min_cost=200,
            max_cost=800,
            rest_type="Cafe",
            online_order=True,
            book_table=False,
        )
        kw = p.to_filter_kwargs(limit=15)
        assert kw["location"] == "BSK"
        assert kw["min_rate"] == 4.0
        assert kw["min_cost"] == 200
        assert kw["max_cost"] == 800
        assert kw["rest_type"] == "Cafe"
        assert kw["online_order"] is True
        assert kw["book_table"] is False
        assert kw["limit"] == 15
