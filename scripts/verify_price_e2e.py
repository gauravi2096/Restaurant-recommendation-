#!/usr/bin/env python3
"""
End-to-end verification of price-for-two after full dataset load.

Checks:
1. Database: no cost_for_two 1 or 2; distribution and sample of high-cost rows.
2. API: /recommend with price filters returns only in-range restaurants; no 1/2 in response.
3. Consistency: same cost values in API response and in prompt (summary input).

Run from repo root after: python -m phase1_data_pipeline --cache-dir ./phase1_data_pipeline/.hf_cache
"""

from __future__ import annotations

import sys
from pathlib import Path

# Repo root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from phase1_data_pipeline.store import RestaurantStore
from phase2_api.api import create_app
from fastapi.testclient import TestClient

DEFAULT_DB = ROOT / "phase1_data_pipeline" / "restaurants.db"


def verify_db(db_path: Path) -> tuple[bool, list[str]]:
    """Verify no cost 1/2 in DB; return (ok, errors)."""
    errors = []
    store = RestaurantStore(db_path)
    store.connect()
    try:
        rows = store.query(limit=20000)
        costs = [r.get("cost_for_two") for r in rows if r.get("cost_for_two") is not None]
        bad = [c for c in costs if c in (1, 2)]
        if bad:
            errors.append(f"DB has cost_for_two in (1, 2): count={len(bad)}, sample={bad[:20]}")
        if not costs:
            errors.append("DB has no cost_for_two values")
        else:
            high = [c for c in costs if c >= 1000]
            if not high and len(costs) > 100:
                errors.append("DB has no cost_for_two >= 1000 (possible parsing issue)")
            # Log stats for confirmation
            print(f"  Stats: {len(rows)} rows, {len(costs)} with cost; min={min(costs)}, max={max(costs)}; cost>=1000: {len(high)}")
        return (len(errors) == 0, errors)
    finally:
        store.close()


def verify_api(db_path: Path) -> tuple[bool, list[str]]:
    """Verify API responses: no cost 1/2, price filters return in-range only."""
    errors = []
    app = create_app(db_path=db_path)
    client = TestClient(app)

    # 1) No 1 or 2 in any response
    r = client.post("/recommend", json={"location": "Koramangala", "top_n": 50})
    if r.status_code != 200:
        errors.append(f"API /recommend failed: {r.status_code} {r.text[:200]}")
    else:
        data = r.json()
        for rest in data.get("restaurants", []):
            cost = rest.get("cost_for_two")
            if cost is not None and cost in (1, 2):
                errors.append(f"API returned cost_for_two={cost} for {rest.get('name')}")

    # 2) Price range 500-1000: all in range
    r = client.post(
        "/recommend",
        json={"location": "HSR Layout", "min_cost": 500, "max_cost": 1000, "top_n": 30},
    )
    if r.status_code != 200:
        errors.append(f"API price filter request failed: {r.status_code}")
    else:
        data = r.json()
        for rest in data.get("restaurants", []):
            cost = rest.get("cost_for_two")
            if cost is not None and (cost < 500 or cost > 1000):
                errors.append(f"Price filter 500-1000: {rest.get('name')} has cost {cost}")

    # 3) Price range 1000-1500: all in range
    r = client.post(
        "/recommend",
        json={"location": "Koramangala", "min_cost": 1000, "max_cost": 1500, "top_n": 30},
    )
    if r.status_code != 200:
        errors.append(f"API price filter 1000-1500 failed: {r.status_code}")
    else:
        data = r.json()
        for rest in data.get("restaurants", []):
            cost = rest.get("cost_for_two")
            if cost is not None and (cost < 1000 or cost > 1500):
                errors.append(f"Price filter 1000-1500: {rest.get('name')} has cost {cost}")

    # 4) Price range 2000+: all >= 2000
    r = client.post(
        "/recommend",
        json={"min_cost": 2000, "top_n": 20},
    )
    if r.status_code != 200:
        errors.append(f"API min_cost 2000 failed: {r.status_code}")
    else:
        data = r.json()
        for rest in data.get("restaurants", []):
            cost = rest.get("cost_for_two")
            if cost is not None and cost < 2000:
                errors.append(f"Price filter 2000+: {rest.get('name')} has cost {cost}")

    return (len(errors) == 0, errors)


def verify_summary_no_wrong_prices(db_path: Path) -> tuple[bool, list[str]]:
    """Verify summary text does not contain mistaken ₹1 or ₹2 for prices."""
    import re
    errors = []
    app = create_app(db_path=db_path)
    client = TestClient(app)
    r = client.post(
        "/recommend",
        json={"location": "Indiranagar", "min_cost": 800, "max_cost": 1500, "top_n": 10},
    )
    if r.status_code != 200:
        errors.append(f"API failed: {r.status_code}")
        return (False, errors)
    data = r.json()
    summary = data.get("summary")
    if summary:
        bad = re.compile(r"₹\s*[12]\s*(?![0-9])")
        if bad.search(summary):
            errors.append(f"Summary contains mistaken ₹1/₹2: ...{summary[:200]}...")
    return (len(errors) == 0, errors)


def main() -> int:
    db_path = DEFAULT_DB
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    all_ok = True
    print("=== 1. Database verification ===")
    ok, errs = verify_db(db_path)
    if ok:
        print("  OK: No cost_for_two 1 or 2; distribution looks valid.")
    else:
        for e in errs:
            print(f"  ERROR: {e}", file=sys.stderr)
        all_ok = False

    print("=== 2. API verification (price filters, no 1/2 in response) ===")
    ok, errs = verify_api(db_path)
    if ok:
        print("  OK: Price filters return in-range only; no 1/2 in responses.")
    else:
        for e in errs:
            print(f"  ERROR: {e}", file=sys.stderr)
        all_ok = False

    print("=== 3. Summary verification (no ₹1/₹2 in summary) ===")
    ok, errs = verify_summary_no_wrong_prices(db_path)
    if ok:
        print("  OK: Summary does not contain mistaken ₹1 or ₹2.")
    else:
        for e in errs:
            print(f"  ERROR: {e}", file=sys.stderr)
        all_ok = False

    if all_ok:
        print("\nAll price-for-two E2E checks passed.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
