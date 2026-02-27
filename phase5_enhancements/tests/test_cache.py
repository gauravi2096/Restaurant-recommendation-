"""Tests for Phase 5 recommendation cache."""

import pytest

from phase5_enhancements.cache import (
    RecommendationCache,
    cache_key_from_request,
)


class TestCacheKey:
    def test_same_body_same_key(self):
        body = {"location": "Koramangala", "min_rating": 4.0, "top_n": 10}
        assert cache_key_from_request(body) == cache_key_from_request(body)

    def test_different_body_different_key(self):
        a = cache_key_from_request({"location": "A", "top_n": 5})
        b = cache_key_from_request({"location": "B", "top_n": 5})
        assert a != b

    def test_cuisines_order_irrelevant(self):
        b1 = {"location": "X", "cuisines": ["North Indian", "Chinese"]}
        b2 = {"location": "X", "cuisines": ["Chinese", "North Indian"]}
        assert cache_key_from_request(b1) == cache_key_from_request(b2)

    def test_none_omitted(self):
        b1 = {"location": "Y", "min_rating": None, "top_n": 15}
        b2 = {"location": "Y", "top_n": 15}
        assert cache_key_from_request(b1) == cache_key_from_request(b2)


class TestRecommendationCache:
    def test_get_miss_returns_none(self):
        c = RecommendationCache(max_size=10)
        assert c.get("missing") is None

    def test_set_and_get(self):
        c = RecommendationCache(max_size=10)
        val = {"restaurants": [], "summary": "Hi", "relaxed": False}
        c.set("k1", val)
        assert c.get("k1") == val

    def test_eviction_when_full(self):
        c = RecommendationCache(max_size=2)
        c.set("a", {"r": 1})
        c.set("b", {"r": 2})
        assert c.get("a") is not None
        assert c.get("b") is not None
        c.set("c", {"r": 3})
        assert c.get("a") is None
        assert c.get("b") is not None
        assert c.get("c") is not None

    def test_clear(self):
        c = RecommendationCache(max_size=10)
        c.set("x", {"r": 1})
        c.clear()
        assert c.get("x") is None
        assert len(c) == 0

    def test_len(self):
        c = RecommendationCache(max_size=10)
        assert len(c) == 0
        c.set("a", {})
        assert len(c) == 1
        c.set("b", {})
        assert len(c) == 2
        c.clear()
        assert len(c) == 0
