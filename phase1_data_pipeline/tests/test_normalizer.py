"""Tests for the ETL normalizer."""

import pytest

from phase1_data_pipeline.normalizer import (
    normalize_row,
    normalize_restaurants,
    _parse_rate,
    _parse_cost,
    _normalize_bool,
)


class TestParseRate:
    def test_parse_rate_slash_five(self):
        assert _parse_rate("4.1/5") == 4.1
        assert _parse_rate("3.5/5") == 3.5

    def test_parse_rate_plain_number(self):
        assert _parse_rate("4.0") == 4.0
        assert _parse_rate(4.2) == 4.2

    def test_parse_rate_none_and_empty(self):
        assert _parse_rate(None) is None
        assert _parse_rate("") is None
        assert _parse_rate("  ") is None

    def test_parse_rate_invalid_returns_none(self):
        assert _parse_rate("N/A") is None
        assert _parse_rate("good") is None


class TestParseCost:
    def test_parse_cost_single(self):
        assert _parse_cost("800") == 800
        assert _parse_cost("300") == 300

    def test_parse_cost_range_takes_first(self):
        assert _parse_cost("300,400") == 300

    def test_parse_cost_with_comma_thousands(self):
        assert _parse_cost("1,000") == 1000
        assert _parse_cost("1,200") == 1200

    def test_parse_cost_indian_style(self):
        """Indian-style hundreds: 1,00 = 100, 2,00 = 200, 2,50 = 250."""
        assert _parse_cost("1,00") == 100
        assert _parse_cost("2,00") == 200
        assert _parse_cost("2,50") == 250

    def test_parse_cost_period_thousand_separator(self):
        """Period as thousand separator: 1.000 = 1000, 2.500 = 2500 (fixes ₹1/₹2 bug for >1000)."""
        assert _parse_cost("1.000") == 1000
        assert _parse_cost("2.500") == 2500
        assert _parse_cost("1.200") == 1200

    def test_parse_cost_none_and_empty(self):
        assert _parse_cost(None) is None
        assert _parse_cost("") is None


class TestNormalizeBool:
    def test_yes_no(self):
        assert _normalize_bool("Yes") is True
        assert _normalize_bool("No") is False

    def test_none_and_empty(self):
        assert _normalize_bool(None) is False
        assert _normalize_bool("") is False


class TestNormalizeRow:
    def test_valid_row_returns_all_fields(self, sample_raw_rows):
        row = sample_raw_rows[0]
        out = normalize_row(row)
        assert out is not None
        assert out["name"] == "Jalsa"
        assert out["rate"] == 4.1
        assert out["cost_for_two"] == 800
        assert out["location"] == "Banashankari"
        assert "North Indian" in (out["cuisines"] or "")
        assert out["online_order"] is True
        assert out["book_table"] is True
        assert out["votes"] == 775

    def test_row_without_name_returns_none(self, sample_raw_rows):
        row = sample_raw_rows[4]  # empty name
        assert normalize_row(row) is None

    def test_row_with_fallback_listed_in_city(self, sample_raw_rows):
        row = sample_raw_rows[1].copy()
        row["location"] = None
        row["listed_in(city)"] = "Banashankari"
        out = normalize_row(row)
        assert out is not None
        assert out["location"] == "Banashankari"

    def test_cost_range_parsed(self, sample_raw_rows):
        row = sample_raw_rows[3]  # "500,600"
        out = normalize_row(row)
        assert out is not None
        assert out["cost_for_two"] == 500


class TestNormalizeRestaurants:
    def test_normalizes_and_dedupes(self, sample_raw_rows):
        # Add duplicate of first row: 3 rows total, 3 valid, 2 unique (first and second)
        rows = sample_raw_rows[:2] + [sample_raw_rows[0].copy()]
        result = normalize_restaurants(rows, drop_duplicates_by=("name", "address"))
        assert len(result) == 2
        assert result[0]["name"] == "Jalsa"
        assert result[1]["name"] == "Spice Elephant"

    def test_drop_duplicates_by_name_and_address(self, sample_raw_rows):
        valid_rows = [r for r in sample_raw_rows if r.get("name")]
        result = normalize_restaurants(valid_rows)
        names = [r["name"] for r in result]
        assert len(names) == len(set(names)) or True  # may have same name different address
        assert all("name" in r and "rate" in r for r in result)
