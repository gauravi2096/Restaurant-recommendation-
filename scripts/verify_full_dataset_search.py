#!/usr/bin/env python3
"""Verify recommendation results match user search criteria (full dataset). Run from project root."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from phase2_api.api import create_app


def norm(s):
    return "".join((s or "").lower().split())


def matches_location(r, location):
    if not location:
        return True
    loc = norm(r.get("location") or "") + norm(r.get("listed_in_city") or "")
    return location.lower() in loc or norm(location) in loc


def matches_cuisine(r, cuisine):
    if not cuisine:
        return True
    return (cuisine or "").lower() in ((r.get("cuisines") or "").lower())


def matches_cost(r, min_cost, max_cost):
    c = r.get("cost_for_two")
    if c is None:
        return True
    if min_cost is not None and c < min_cost:
        return False
    if max_cost is not None and c > max_cost:
        return False
    return True


def matches_rating(r, min_rating):
    if min_rating is None:
        return True
    rate = r.get("rate")
    if rate is None:
        return True
    return rate >= min_rating


def main():
    db = ROOT / "phase1_data_pipeline" / "restaurants.db"
    app = create_app(db_path=db)
    client = TestClient(app)
    failed = []
    tests = []

    # 1. Location: JP Nagar
    r = client.post("/recommend", json={"location": "JP Nagar", "top_n": 20})
    assert r.status_code == 200
    for x in r.json().get("restaurants", []):
        if not matches_location(x, "JP Nagar"):
            failed.append(("location=JP Nagar", x.get("name"), x.get("location")))
    tests.append(("Location JP Nagar", len(r.json()["restaurants"])))

    # 2. Location: BTM
    r = client.post("/recommend", json={"location": "BTM", "top_n": 10})
    assert r.status_code == 200
    for x in r.json().get("restaurants", []):
        if not matches_location(x, "BTM"):
            failed.append(("location=BTM", x.get("name"), x.get("location")))
    tests.append(("Location BTM", len(r.json()["restaurants"])))

    # 3. Cuisine: North Indian
    r = client.post("/recommend", json={"cuisines": ["North Indian"], "top_n": 15})
    assert r.status_code == 200
    for x in r.json().get("restaurants", []):
        if not matches_cuisine(x, "North Indian"):
            failed.append(("cuisine=North Indian", x.get("name"), x.get("cuisines")))
    tests.append(("Cuisine North Indian", len(r.json()["restaurants"])))

    # 4. Price 500-1000
    r = client.post("/recommend", json={"min_cost": 500, "max_cost": 1000, "top_n": 15})
    assert r.status_code == 200
    for x in r.json().get("restaurants", []):
        if not matches_cost(x, 500, 1000):
            failed.append(("cost 500-1000", x.get("name"), x.get("cost_for_two")))
    tests.append(("Price 500-1000", len(r.json()["restaurants"])))

    # 5. Min rating 4.0
    r = client.post("/recommend", json={"min_rating": 4.0, "top_n": 10})
    assert r.status_code == 200
    for x in r.json().get("restaurants", []):
        if not matches_rating(x, 4.0):
            failed.append(("min_rating=4", x.get("name"), x.get("rate")))
    tests.append(("Min rating 4.0", len(r.json()["restaurants"])))

    # 6. Combined
    r = client.post(
        "/recommend",
        json={
            "location": "Indiranagar",
            "cuisines": ["Chinese"],
            "min_cost": 300,
            "max_cost": 800,
            "min_rating": 3.5,
            "top_n": 10,
        },
    )
    assert r.status_code == 200
    for x in r.json().get("restaurants", []):
        if not matches_location(x, "Indiranagar"):
            failed.append(("combined location", x.get("name"), x.get("location")))
        if not matches_cuisine(x, "Chinese"):
            failed.append(("combined cuisine", x.get("name"), x.get("cuisines")))
        if not matches_cost(x, 300, 800):
            failed.append(("combined cost", x.get("name"), x.get("cost_for_two")))
        if not matches_rating(x, 3.5):
            failed.append(("combined rating", x.get("name"), x.get("rate")))
    tests.append(("Combined Indiranagar+Chinese+300-800+3.5", len(r.json()["restaurants"])))

    # 7. No filters
    r = client.post("/recommend", json={"top_n": 5})
    assert r.status_code == 200
    n = len(r.json().get("restaurants", []))
    assert n <= 5
    tests.append(("No filters top_n=5", n))

    from phase1_data_pipeline.store import RestaurantStore
    store = RestaurantStore(db)
    store.connect()
    total = store.count()
    store.close()

    print("Full-dataset search-criteria verification")
    print("=" * 55)
    print(f"DB total: {total} restaurants")
    for name, count in tests:
        print(f"  OK  {name}: {count} results")
    if failed:
        print("\nFAILED:", len(failed), "result(s) did not match criteria")
        for f in failed[:15]:
            print(" ", f)
        sys.exit(1)
    print("\nAll results match user search criteria.")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
