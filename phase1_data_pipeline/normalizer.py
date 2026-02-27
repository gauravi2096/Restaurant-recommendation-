"""
ETL / Normalizer: clean and normalize Zomato dataset rows.
"""

from __future__ import annotations

import re
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Column names in the Hugging Face dataset (with special chars)
COL_RATE = "rate"
COL_APPROX_COST = "approx_cost(for two people)"
COL_LOCATION = "location"
COL_LISTED_CITY = "listed_in(city)"
COL_CUISINES = "cuisines"
COL_REST_TYPE = "rest_type"
COL_ONLINE_ORDER = "online_order"
COL_BOOK_TABLE = "book_table"
COL_NAME = "name"
COL_ADDRESS = "address"
COL_URL = "url"
COL_VOTES = "votes"
COL_PHONE = "phone"
COL_DISH_LIKED = "dish_liked"


def _parse_rate(value: Any) -> float | None:
    """Parse rate from values like '4.1/5' or '4.1' or 4.1."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s or s.lower() in ("nan", "null", ""):
        return None
    match = re.search(r"(\d+\.?\d*)", s)
    if match:
        try:
            v = float(match.group(1))
            return v if 0 <= v <= 5 else None
        except ValueError:
            pass
    return None


def _parse_cost(value: Any) -> int | None:
    """Parse approx cost for two. Handles '800', '300,400' (range → first), '1,000' (thousand sep), '1,00'/'2,00' (Indian = 100, 200), '1.000'/'2.500' (period thousand sep)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s or s.lower() in ("nan", "null", ""):
        return None
    # "1.000" / "2.500" — period as thousand separator (e.g. from locale or HF); else we'd parse as 1 or 2
    if re.match(r"^\d{1,4}\.\d{3}$", s):
        return int(s.replace(".", ""))
    parts = [p.strip() for p in s.split(",")]
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        # "1,000" / "1,200" = Western thousand separator
        if len(parts[1]) == 3 and len(parts[0]) <= 2:
            return int(parts[0] + parts[1])
        # "1,00" / "2,00" / "2,50" = Indian style (100, 200, 250) — avoid wrongly parsing as 1 or 2
        if len(parts[1]) == 2:
            return int(parts[0]) * 100 + int(parts[1])
        # "300,400" = range (take first)
        return int(parts[0])
    if len(parts) == 1 and parts[0].isdigit():
        return int(parts[0])
    # Fallback: first number in string (e.g. with extra chars)
    match = re.search(r"(\d+)", s)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    return None


def _normalize_string(value: Any, max_length: int | None = 500) -> str | None:
    """Normalize string: strip, empty -> None, optionally truncate."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s:
        return None
    if max_length and len(s) > max_length:
        s = s[:max_length]
    return s


def _normalize_location(value: Any) -> str | None:
    """Prefer listed_in(city) or location for filter-friendly value."""
    s = _normalize_string(value, max_length=200)
    return s if s else None


def _normalize_cuisines(value: Any) -> str | None:
    """Normalize cuisines: strip, collapse whitespace/comma."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s:
        return None
    # Normalize separators to comma, single space
    s = re.sub(r"[,]+", ",", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:500] if s else None


def _normalize_bool(value: Any) -> bool:
    """Map Yes/No, true/false, 1/0 to bool."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    s = str(value).strip().lower()
    return s in ("yes", "true", "1", "y")


def _normalize_votes(value: Any) -> int | None:
    """Parse votes to int."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def normalize_row(row: dict[str, Any]) -> dict[str, Any] | None:
    """
    Normalize a single dataset row to the canonical schema.

    Returns None if the row is invalid (e.g. missing required fields).
    """
    name = _normalize_string(row.get(COL_NAME), max_length=300)
    if not name:
        return None

    rate = _parse_rate(row.get(COL_RATE))
    cost = _parse_cost(row.get(COL_APPROX_COST))
    location = _normalize_location(row.get(COL_LOCATION)) or _normalize_location(
        row.get(COL_LISTED_CITY)
    )
    listed_in_city = _normalize_location(row.get(COL_LISTED_CITY)) or _normalize_location(
        row.get(COL_LOCATION)
    )
    cuisines = _normalize_cuisines(row.get(COL_CUISINES))
    rest_type = _normalize_string(row.get(COL_REST_TYPE), max_length=200)
    address = _normalize_string(row.get(COL_ADDRESS), max_length=500)
    url = _normalize_string(row.get(COL_URL), max_length=600)
    online_order = _normalize_bool(row.get(COL_ONLINE_ORDER))
    book_table = _normalize_bool(row.get(COL_BOOK_TABLE))
    votes = _normalize_votes(row.get(COL_VOTES))
    phone = _normalize_string(row.get(COL_PHONE), max_length=50)
    dish_liked = _normalize_string(row.get(COL_DISH_LIKED), max_length=500)

    return {
        "name": name,
        "address": address,
        "url": url,
        "location": location,
        "listed_in_city": listed_in_city,
        "cuisines": cuisines,
        "rest_type": rest_type,
        "rate": rate,
        "cost_for_two": cost,
        "votes": votes,
        "online_order": online_order,
        "book_table": book_table,
        "phone": phone,
        "dish_liked": dish_liked,
    }


def normalize_restaurants(
    rows: list[dict[str, Any]],
    drop_duplicates_by: tuple[str, ...] = ("name", "address"),
) -> list[dict[str, Any]]:
    """
    Normalize a list of raw rows and optionally drop duplicates.

    Args:
        rows: List of raw dataset row dicts.
        drop_duplicates_by: Keys to use for deduplication (default: name + address).

    Returns:
        List of normalized restaurant dicts.
    """
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    for row in rows:
        out = normalize_row(row)
        if out is None:
            continue
        key = tuple(out.get(k) or "" for k in drop_duplicates_by)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(out)

    logger.info(
        "Normalized %d rows -> %d records (dropped %d)",
        len(rows),
        len(normalized),
        len(rows) - len(normalized),
    )
    return normalized
