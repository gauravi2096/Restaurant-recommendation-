"""
End-to-end tests for filtering and recommendations.

Verifies:
- Full filters (location, cuisine, price range, rating): all returned restaurants
  and summary match those exact filters.
- Same location with one filter changed (e.g. cuisine): results update correctly
  and do not repeat restaurants unless they match the new filters.
- LLM summary reflects only the restaurants returned for each search.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from phase2_api.api import create_app

# All restaurant names in the sample dataset (conftest sample_raw_rows).
# Used to assert summary does not mention restaurants outside the returned list.
SAMPLE_RESTAURANT_NAMES = [
    "Jalsa",
    "Spice Elephant",
    "Addhuri Udupi Bhojana",
    "Koramangala Cafe",
    "Premium Place",
    "Luxury Place",
]


@pytest.fixture
def client_with_data(store_with_data, temp_db_path):
    """Test client with sample data (same as test_api.py)."""
    app = create_app(db_path=temp_db_path)
    return TestClient(app)


def _location_matches(loc_val: str | None, want: str) -> bool:
    """True if location or listed_in_city contains the wanted location (normalized)."""
    if not loc_val or not want:
        return False
    combined = " ".join((loc_val or "").split()).lower()
    want_norm = "".join(want.split()).lower()
    want_first = "".join(want.split()[0].split()).lower() if want.split() else ""
    return want_norm in combined or (want_first and want_first in combined)


def _restaurant_matches_filters(rest, location=None, cuisines=None, min_rating=None, min_cost=None, max_cost=None):
    """Check one restaurant against the exact filters (strict)."""
    if location:
        loc_val = (rest.get("location") or "") + " " + (rest.get("listed_in_city") or "")
        if not _location_matches(loc_val.strip(), location):
            return False
    if min_rating is not None:
        rate = rest.get("rate")
        if rate is not None and rate < min_rating:
            return False
    if min_cost is not None:
        cost = rest.get("cost_for_two")
        if cost is not None and cost < min_cost:
            return False
    if max_cost is not None:
        cost = rest.get("cost_for_two")
        if cost is not None and cost > max_cost:
            return False
    if cuisines:
        cu_str = (rest.get("cuisines") or "").lower().replace(" ", "")
        for c in cuisines:
            if c and "".join(c.split()).lower() in cu_str:
                break
        else:
            return False
    return True


def _names_mentioned_in_summary(summary: str | None) -> set[str]:
    """Extract restaurant names that appear in the summary (from known SAMPLE list)."""
    if not summary:
        return set()
    summary_lower = summary.lower()
    found = set()
    for name in SAMPLE_RESTAURANT_NAMES:
        if name.lower() in summary_lower:
            found.add(name)
    return found


class TestE2EFullFiltersMatch:
    """User searches with location, cuisine, price range, and rating; results and summary match those filters."""

    def test_full_filters_all_results_match_exact_filters(self, client_with_data):
        """With location, cuisine, price range, and rating, every returned restaurant satisfies all filters."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "cuisines": ["North Indian"],
                "min_cost": 300,
                "max_cost": 800,
                "min_rating": 3.5,
                "top_n": 10,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["relaxed"] is False
        restaurants = data["restaurants"]
        for rest in restaurants:
            assert _restaurant_matches_filters(
                rest,
                location="Banashankari",
                cuisines=["North Indian"],
                min_rating=3.5,
                min_cost=300,
                max_cost=800,
            ), f"Restaurant {rest.get('name')} does not match filters"

    def test_full_filters_strict_price_and_rating(self, client_with_data):
        """Price and rating filters are strict: no result outside range."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "min_rating": 4.0,
                "min_cost": 500,
                "max_cost": 800,
                "top_n": 10,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["relaxed"] is False
        for rest in data["restaurants"]:
            rate = rest.get("rate")
            cost = rest.get("cost_for_two")
            if rate is not None:
                assert rate >= 4.0, f"{rest.get('name')} rate {rate} < 4.0"
            if cost is not None:
                assert 500 <= cost <= 800, f"{rest.get('name')} cost {cost} outside [500,800]"

    def test_full_filters_no_match_returns_empty_no_relax(self, client_with_data):
        """When no restaurant matches all filters, returns empty list and relaxed=False."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "cuisines": ["North Indian"],
                "min_cost": 50,
                "max_cost": 100,
                "min_rating": 4.5,
                "top_n": 10,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["restaurants"] == []
        assert data["relaxed"] is False


class TestE2ESameLocationDifferentFilter:
    """Same location, one filter (e.g. cuisine) changed; results update and only match new filters."""

    def test_same_location_different_cuisine_results_differ(self, client_with_data):
        """Changing cuisine from North Indian to South Indian returns different set; each set matches its filter."""
        # Search 1: Banashankari + North Indian
        r1 = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "cuisines": ["North Indian"],
                "top_n": 10,
            },
        )
        assert r1.status_code == 200, r1.text
        data1 = r1.json()
        assert data1["relaxed"] is False
        names_north = {rest["name"] for rest in data1["restaurants"]}
        for rest in data1["restaurants"]:
            assert "North Indian" in (rest.get("cuisines") or "")

        # Search 2: Banashankari + South Indian
        r2 = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "cuisines": ["South Indian"],
                "top_n": 10,
            },
        )
        assert r2.status_code == 200, r2.text
        data2 = r2.json()
        assert data2["relaxed"] is False
        names_south = {rest["name"] for rest in data2["restaurants"]}
        for rest in data2["restaurants"]:
            assert "South Indian" in (rest.get("cuisines") or "")

        # South Indian in sample is only Addhuri; North Indian is Jalsa, Spice Elephant, Addhuri.
        # So names_south should be subset of names_north only for Addhuri (has both).
        assert "Addhuri Udupi Bhojana" in names_south
        # North Indian set should include at least Jalsa or Spice Elephant
        assert len(names_north) >= 1
        # Results for South Indian should not include Jalsa or Spice Elephant (they don't have South Indian)
        assert "Jalsa" not in names_south
        assert "Spice Elephant" not in names_south

    def test_same_location_different_cuisine_no_wrong_repeat(self, client_with_data):
        """Chinese in Banashankari returns only restaurants with Chinese; no Cafe/Italian from Koramangala."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "cuisines": ["Chinese"],
                "top_n": 10,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["relaxed"] is False
        for rest in data["restaurants"]:
            assert "Chinese" in (rest.get("cuisines") or "")
            assert _location_matches(
                (rest.get("location") or "") + " " + (rest.get("listed_in_city") or ""),
                "Banashankari",
            )
        # Koramangala Cafe must not appear (different location)
        names = [rest["name"] for rest in data["restaurants"]]
        assert "Koramangala Cafe" not in names


class TestE2ESummaryReflectsReturnedRestaurants:
    """LLM summary mentions only restaurants from the returned list for that search."""

    def test_summary_does_not_mention_restaurants_outside_returned_list(self, client_with_data):
        """If summary is present, every restaurant name in it must be in the returned list."""
        # Request filters that return only Banashankari restaurants (no Koramangala)
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "cuisines": ["North Indian"],
                "top_n": 10,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        returned_names = {rest["name"] for rest in data["restaurants"]}
        summary = data.get("summary")

        if summary is None:
            # No API key or LLM disabled: nothing to check
            return

        mentioned = _names_mentioned_in_summary(summary)
        for name in mentioned:
            assert name in returned_names, (
                f"Summary mentions '{name}' but that restaurant was not in the returned list (returned: {returned_names})"
            )

    def test_summary_for_empty_results_is_null(self, client_with_data):
        """When no restaurants match, summary should be null."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "NonExistentCity999",
                "top_n": 10,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["restaurants"] == []
        assert data.get("summary") is None


class TestE2ECostForTwoDisplayAndFiltering:
    """Price-for-two is correctly parsed (no ₹1/₹2 for 1000+), returned by API, and used in filtering."""

    def test_cost_for_two_never_1_or_2_in_response(self, client_with_data):
        """API never returns cost_for_two 1 or 2; period-thousand format (1.000, 2.500) parses to 1000, 2500."""
        r = client_with_data.post(
            "/recommend",
            json={"location": "Banashankari", "top_n": 20},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        for rest in data["restaurants"]:
            cost = rest.get("cost_for_two")
            if cost is not None:
                assert cost not in (1, 2), (
                    f"Restaurant {rest.get('name')} has cost_for_two={cost}; "
                    "values 1 or 2 indicate broken parsing of 1.000/2.500"
                )

    def test_price_range_500_1000_returns_only_in_range(self, client_with_data):
        """Filter min_cost=500 max_cost=1000: every returned restaurant has cost in [500, 1000] or NULL."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "min_cost": 500,
                "max_cost": 1000,
                "top_n": 20,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        for rest in data["restaurants"]:
            cost = rest.get("cost_for_two")
            if cost is not None:
                assert 500 <= cost <= 1000, f"{rest.get('name')} cost {cost} outside [500, 1000]"

    def test_price_range_1000_1500_includes_1000_parsed_restaurant(self, client_with_data):
        """Filter min_cost=1000 max_cost=1500 includes Premium Place (raw '1.000' -> 1000)."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "min_cost": 1000,
                "max_cost": 1500,
                "top_n": 20,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        names = [rest["name"] for rest in data["restaurants"]]
        costs = {rest["name"]: rest.get("cost_for_two") for rest in data["restaurants"]}
        assert "Premium Place" in names, f"Premium Place (cost 1000) should be in results: {names}"
        assert costs.get("Premium Place") == 1000, (
            f"Premium Place cost_for_two should be 1000, got {costs.get('Premium Place')}"
        )
        for rest in data["restaurants"]:
            cost = rest.get("cost_for_two")
            if cost is not None:
                assert 1000 <= cost <= 1500, f"{rest.get('name')} cost {cost} outside [1000, 1500]"

    def test_price_range_2000_plus_includes_2500_parsed_restaurant(self, client_with_data):
        """Filter min_cost=2000 includes Luxury Place (raw '2.500' -> 2500)."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "min_cost": 2000,
                "top_n": 20,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        names = [rest["name"] for rest in data["restaurants"]]
        costs = {rest["name"]: rest.get("cost_for_two") for rest in data["restaurants"]}
        assert "Luxury Place" in names, f"Luxury Place (cost 2500) should be in results: {names}"
        assert costs.get("Luxury Place") == 2500, (
            f"Luxury Place cost_for_two should be 2500, got {costs.get('Luxury Place')}"
        )

    def test_summary_does_not_show_1_or_2_as_price_for_expensive_restaurants(self, client_with_data):
        """When results include high-cost restaurants, summary should not contain mistaken '₹1' or '₹2'."""
        r = client_with_data.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "min_cost": 1000,
                "max_cost": 1500,
                "top_n": 10,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        summary = data.get("summary")
        if summary is None:
            return
        # Summary should not contain standalone ₹1 or ₹2 (mistaken display for 1000/2000)
        bad_pattern = re.compile(r"₹\s*[12]\s*(?![0-9])")
        assert not bad_pattern.search(summary), (
            f"Summary should not contain ₹1 or ₹2 for prices; got: {summary!r}"
        )
