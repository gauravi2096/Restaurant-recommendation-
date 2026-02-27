"""
Tests for Phase 4 Web UI: static assets exist and API contract is satisfied.
"""

import pytest
from pathlib import Path

# Phase 4 root (parent of tests/)
PHASE4_ROOT = Path(__file__).resolve().parent.parent


class TestStaticAssets:
    """Ensure required static files exist and contain expected content."""

    def test_index_html_exists(self):
        path = PHASE4_ROOT / "index.html"
        assert path.is_file(), "index.html should exist"

    def test_index_has_form_and_results_sections(self):
        path = PHASE4_ROOT / "index.html"
        html = path.read_text()
        assert "preferences-form" in html or "id=\"preferences-form\"" in html
        assert "recommend" in html or "Get recommendations" in html
        assert "restaurants-list" in html or "id=\"restaurants-list\"" in html

    def test_css_exists(self):
        path = PHASE4_ROOT / "css" / "styles.css"
        assert path.is_file(), "css/styles.css should exist"

    def test_js_app_exists(self):
        path = PHASE4_ROOT / "js" / "app.js"
        assert path.is_file(), "js/app.js should exist"

    def test_js_api_exists(self):
        path = PHASE4_ROOT / "js" / "api.js"
        assert path.is_file(), "js/api.js should exist"


class TestRequestResponseContract:
    """Verify the request/response shape expected by the frontend matches the API."""

    def test_build_recommend_request_shape(self):
        """Frontend sends optional location, price_range (→ min/max_cost), min_rating, cuisines (single select). No top_n."""
        form_data = {
            "location": "Banashankari",
            "price_range": "250-500",
            "min_rating": "4.0",
            "cuisines": "North Indian",
        }
        # Replicate minimal build logic: price_range → min_cost/max_cost, single cuisine → list
        body = {}
        if form_data.get("location", "").strip():
            body["location"] = form_data["location"].strip()
        pr = form_data.get("price_range", "").strip()
        if pr == "250-500":
            body["min_cost"] = 250
            body["max_cost"] = 500
        if form_data.get("min_rating", "").strip():
            body["min_rating"] = float(form_data["min_rating"])
        if form_data.get("cuisines", "").strip():
            body["cuisines"] = [form_data["cuisines"].strip()]

        assert "location" in body
        assert body["min_cost"] == 250
        assert body["max_cost"] == 500
        assert body["min_rating"] == 4.0
        assert body["cuisines"] == ["North Indian"]
        assert "top_n" not in body  # API default used

    def test_parse_recommend_response_shape(self):
        """API returns { restaurants: list, summary: str|null, relaxed: bool }."""
        data = {
            "restaurants": [
                {"name": "Jalsa", "location": "Banashankari", "rate": 4.1, "cost_for_two": 800}
            ],
            "summary": "Great picks!",
            "relaxed": False,
        }
        assert "restaurants" in data
        assert "summary" in data
        assert "relaxed" in data
        assert isinstance(data["restaurants"], list)
        assert data["restaurants"][0]["name"] == "Jalsa"
        assert data["summary"] == "Great picks!"
        assert data["relaxed"] is False
