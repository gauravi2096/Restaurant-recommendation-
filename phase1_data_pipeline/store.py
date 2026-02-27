"""
Restaurant store: persist normalized restaurants in SQLite with indexes for filtering.
"""

from __future__ import annotations

import sqlite3
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    url TEXT,
    location TEXT,
    listed_in_city TEXT,
    cuisines TEXT,
    rest_type TEXT,
    rate REAL,
    cost_for_two INTEGER,
    votes INTEGER,
    online_order INTEGER NOT NULL DEFAULT 0,
    book_table INTEGER NOT NULL DEFAULT 0,
    phone TEXT,
    dish_liked TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants(location);
CREATE INDEX IF NOT EXISTS idx_restaurants_rate ON restaurants(rate);
CREATE INDEX IF NOT EXISTS idx_restaurants_cost_for_two ON restaurants(cost_for_two);
CREATE INDEX IF NOT EXISTS idx_restaurants_rest_type ON restaurants(rest_type);
CREATE INDEX IF NOT EXISTS idx_restaurants_online_order ON restaurants(online_order);
CREATE INDEX IF NOT EXISTS idx_restaurants_book_table ON restaurants(book_table);
CREATE INDEX IF NOT EXISTS idx_restaurants_cuisines ON restaurants(cuisines);
"""


class RestaurantStore:
    """
    SQLite-backed store for normalized restaurants.
    Supports insert (batch) and query by location, cost, rating, cuisines.
    """

    def __init__(self, db_path: str | Path = "restaurants.db"):
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "RestaurantStore":
        self.connect()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def init_schema(self) -> None:
        """Create tables and indexes if they do not exist. Add listed_in_city if missing (migration)."""
        conn = self.connect()
        conn.executescript(SCHEMA_SQL)
        # Migration: add listed_in_city if table existed without it (before creating index)
        cur = conn.execute("PRAGMA table_info(restaurants)")
        columns = [row[1] for row in cur.fetchall()]
        if "listed_in_city" not in columns:
            conn.execute("ALTER TABLE restaurants ADD COLUMN listed_in_city TEXT")
            logger.info("Added column listed_in_city to restaurants")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_restaurants_listed_in_city ON restaurants(listed_in_city)"
        )
        conn.commit()
        logger.info("Schema initialized at %s", self.db_path)

    def clear(self) -> int:
        """Delete all rows. Returns number of rows deleted."""
        conn = self.connect()
        cur = conn.execute("SELECT COUNT(*) FROM restaurants")
        count = cur.fetchone()[0]
        conn.execute("DELETE FROM restaurants")
        conn.commit()
        logger.info("Cleared %d rows from restaurants", count)
        return count

    def insert_many(self, restaurants: list[dict[str, Any]]) -> int:
        """Insert normalized restaurant dicts. Returns number inserted."""
        if not restaurants:
            return 0
        conn = self.connect()
        rows = [
            (
                r.get("name"),
                r.get("address"),
                r.get("url"),
                r.get("location"),
                r.get("listed_in_city"),
                r.get("cuisines"),
                r.get("rest_type"),
                r.get("rate"),
                r.get("cost_for_two"),
                r.get("votes"),
                1 if r.get("online_order") else 0,
                1 if r.get("book_table") else 0,
                r.get("phone"),
                r.get("dish_liked"),
            )
            for r in restaurants
        ]
        conn.executemany(
            """
            INSERT INTO restaurants (
                name, address, url, location, listed_in_city, cuisines, rest_type,
                rate, cost_for_two, votes, online_order, book_table, phone, dish_liked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        logger.info("Inserted %d restaurants", len(restaurants))
        return len(restaurants)

    def count(self) -> int:
        """Return total number of restaurants in the store."""
        conn = self.connect()
        cur = conn.execute("SELECT COUNT(*) FROM restaurants")
        return cur.fetchone()[0]

    def get_by_id(self, id: int) -> dict[str, Any] | None:
        """Return one restaurant by primary key or None."""
        conn = self.connect()
        cur = conn.execute("SELECT * FROM restaurants WHERE id = ?", (id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def query(
        self,
        *,
        location: str | None = None,
        min_rate: float | None = None,
        max_cost: int | None = None,
        min_cost: int | None = None,
        cuisine_contains: str | None = None,
        rest_type: str | None = None,
        online_order: bool | None = None,
        book_table: bool | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query restaurants with optional filters.
        All filters are ANDed. location/cuisine/rest_type use case-insensitive LIKE.
        Location and cuisine use flexible matching: tokens split by whitespace joined by %,
        so "JP Nagar" matches "J P Nagar" in the dataset.
        """
        conn = self.connect()

        # Step-by-step filter audit: log count after each filter
        total_before = self.count()
        logger.info("recommend query: [audit] total records before filters = %d", total_before)

        conditions: list[str] = []
        params: list[Any] = []
        # Build conditions; include NULL rate/cost so we don't exclude rows with missing data
        if location:
            loc = location.strip()
            if loc:
                # Exact match on location (the column we display in UI). Normalize spaces/case
                # so "JP Nagar" matches "J P Nagar". Do not match listed_in_city to avoid
                # returning rows that display a different location (e.g. Jayanagar) but have
                # listed_in_city = selected (e.g. Banashankari).
                loc_norm = "".join(loc.split()).lower()
                conditions.append(
                    "REPLACE(LOWER(TRIM(COALESCE(location,''))), ' ', '') = ?"
                )
                params.append(loc_norm)
                logger.info("recommend query: applying location exact filter %r -> normalized %r", location, loc_norm)
        if min_rate is not None:
            conditions.append("(rate IS NULL OR rate >= ?)")
            params.append(min_rate)
            logger.info("recommend query: applying min_rate >= %s (NULL rate included)", min_rate)
        if max_cost is not None:
            conditions.append("(cost_for_two IS NULL OR cost_for_two <= ?)")
            params.append(max_cost)
            logger.info("recommend query: applying max_cost <= %s (NULL cost included)", max_cost)
        if min_cost is not None:
            conditions.append("(cost_for_two IS NULL OR cost_for_two >= ?)")
            params.append(min_cost)
            logger.info("recommend query: applying min_cost >= %s (NULL cost included)", min_cost)
        if cuisine_contains:
            cu = cuisine_contains.strip()
            if cu:
                cu_normalized = "%" + "".join(cu.split()).lower() + "%"
                conditions.append("(COALESCE(cuisines,'') != '' AND LOWER(REPLACE(COALESCE(cuisines,''), ' ', '')) LIKE ?)")
                params.append(cu_normalized)
                logger.info("recommend query: applying cuisine_contains %r -> normalized pattern %r", cuisine_contains, cu_normalized)
        if rest_type:
            conditions.append("LOWER(rest_type) LIKE LOWER(?)")
            params.append(f"%{rest_type}%")
            logger.info("recommend query: applying rest_type %r", rest_type)
        if online_order is not None:
            conditions.append("online_order = ?")
            params.append(1 if online_order else 0)
            logger.info("recommend query: applying online_order = %s", online_order)
        if book_table is not None:
            conditions.append("book_table = ?")
            params.append(1 if book_table else 0)
            logger.info("recommend query: applying book_table = %s", book_table)

        where = " AND ".join(conditions) if conditions else "1=1"
        # Audit: log total count matching all filters (before LIMIT)
        try:
            count_after_filters = conn.execute("SELECT COUNT(*) FROM restaurants WHERE " + where, params).fetchone()[0]
            logger.info("recommend query: [audit] count after all filters (before limit) = %d", count_after_filters)
        except Exception as e:
            logger.debug("recommend query: [audit] count failed: %s", e)
        params_with_limit = params + [limit]
        cur = conn.execute(
            f"""
            SELECT * FROM restaurants
            WHERE {where}
            ORDER BY rate IS NULL, rate DESC, votes IS NULL, votes DESC
            LIMIT ?
            """,
            params_with_limit,
        )
        rows = cur.fetchall()
        result = [dict(r) for r in rows]
        logger.info("recommend query: [audit] final after all filters count = %d (limit %d)", len(result), limit)
        return result

    def get_distinct_locations(self) -> list[str]:
        """Return sorted distinct non-null location values (for UI dropdown)."""
        conn = self.connect()
        cur = conn.execute(
            "SELECT DISTINCT location FROM restaurants WHERE location IS NOT NULL AND TRIM(location) != '' ORDER BY location"
        )
        rows = cur.fetchall()
        return [r[0] for r in rows if r[0]]

    def get_distinct_cuisines(self) -> list[str]:
        """Return sorted distinct cuisine values (from comma-separated cuisines column)."""
        conn = self.connect()
        cur = conn.execute("SELECT cuisines FROM restaurants WHERE cuisines IS NOT NULL AND TRIM(cuisines) != ''")
        rows = cur.fetchall()
        seen: set[str] = set()
        for (raw,) in rows:
            for part in (raw or "").split(","):
                s = part.strip()
                if s:
                    seen.add(s)
        return sorted(seen)
