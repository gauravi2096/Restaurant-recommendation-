"""
REST API layer: POST /recommend, GET /health.
Phase 5: optional cache and analytics when phase5_enhancements is available.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from phase1_data_pipeline.store import RestaurantStore

from .orchestrator import recommend
from .preferences import RecommendPreferences

logger = logging.getLogger(__name__)

# Phase 5: optional cache and analytics
try:
    from phase5_enhancements import (
        RecommendationCache,
        cache_key_from_request,
        log_recommend_usage,
        get_popular,
    )
    _phase5_available = True
except ImportError:
    _phase5_available = False

# Default DB path relative to project root
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "phase1_data_pipeline" / "restaurants.db"


class RecommendRequest(BaseModel):
    """Request body for POST /recommend."""

    location: Optional[str] = Field(default=None, description="City or area")
    min_rating: Optional[float] = Field(default=None, ge=0, le=5)
    min_cost: Optional[int] = Field(default=None, ge=0)
    max_cost: Optional[int] = Field(default=None, ge=0)
    cuisines: Optional[List[str]] = Field(default=None)
    rest_type: Optional[str] = Field(default=None)
    online_order: Optional[bool] = Field(default=None)
    book_table: Optional[bool] = Field(default=None)
    top_n: int = Field(default=15, ge=1, le=50)


class RecommendResponse(BaseModel):
    """Response for POST /recommend."""

    restaurants: List[Dict[str, Any]]
    summary: Optional[str]
    relaxed: bool


def create_app(db_path: str | Path | None = None) -> FastAPI:
    """Create FastAPI app with recommendation and health endpoints."""
    app = FastAPI(
        title="Restaurant Recommendation API",
        description="Phase 2: Filter by preferences, returns candidate restaurants.",
        version="0.2.0",
    )
    recommendation_cache: Optional[Any] = (
        RecommendationCache(max_size=100) if _phase5_available else None
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    path = Path(db_path) if db_path else DEFAULT_DB_PATH

    @app.get("/health")
    def health() -> dict[str, str]:
        """Health check: API and store connectivity."""
        try:
            store = RestaurantStore(path)
            store.connect()
            n = store.count()
            store.close()
            return {"status": "ok", "store": "connected", "restaurants_count": str(n)}
        except Exception as e:
            logger.exception("Health check failed")
            raise HTTPException(status_code=503, detail=f"Store unavailable: {e}")

    @app.get("/locations")
    def get_locations() -> dict[str, List[str]]:
        """Return distinct location values from the dataset (for UI dropdown)."""
        try:
            store = RestaurantStore(path)
            store.connect()
            locations = store.get_distinct_locations()
            store.close()
            return {"locations": locations}
        except Exception as e:
            logger.exception("Failed to get locations")
            raise HTTPException(status_code=503, detail=f"Store unavailable: {e}")

    @app.post("/recommend", response_model=RecommendResponse)
    def recommend_endpoint(body: RecommendRequest) -> RecommendResponse:
        """Get restaurant recommendations from user preferences."""
        body_dict = body.model_dump()
        if _phase5_available and recommendation_cache is not None:
            log_recommend_usage(body_dict)
            key = cache_key_from_request(body_dict)
            cached = recommendation_cache.get(key)
            # Only use cache when result was strict (relaxed=False); avoid serving old relaxed results
            if cached is not None and cached.get("relaxed") is False:
                return RecommendResponse(
                    restaurants=cached["restaurants"],
                    summary=cached["summary"],
                    relaxed=cached["relaxed"],
                )
        prefs = RecommendPreferences(
            location=body.location,
            min_rating=body.min_rating,
            min_cost=body.min_cost,
            max_cost=body.max_cost,
            cuisines=body.cuisines,
            rest_type=body.rest_type,
            online_order=body.online_order,
            book_table=body.book_table,
        )
        logger.info(
            "recommend: body location=%r min_rating=%s min_cost=%s max_cost=%s cuisines=%r top_n=%s",
            body.location,
            body.min_rating,
            body.min_cost,
            body.max_cost,
            body.cuisines,
            body.top_n,
        )
        logger.info("recommend: prefs location=%r to_filter_kwargs=%s", prefs.location, prefs.to_filter_kwargs(limit=body.top_n * 2))
        store = RestaurantStore(path)
        try:
            store.connect()
            store_count = store.count()
            logger.info("recommend: dataset db_path=%s total_restaurants=%d", path, store_count)
            if store_count == 0:
                logger.warning(
                    "recommend: store is empty; populate from Hugging Face dataset: "
                    "python -m phase1_data_pipeline --max-rows N"
                )
            result = recommend(store, prefs, top_n=body.top_n, relax_if_empty=False)
            if _phase5_available and recommendation_cache is not None:
                recommendation_cache.set(key, result)
            return RecommendResponse(
                restaurants=result["restaurants"],
                summary=result["summary"],
                relaxed=result["relaxed"],
            )
        finally:
            store.close()

    if _phase5_available:
        @app.get("/analytics/popular")
        def analytics_popular(
            top_locations: int = 10,
            top_cuisines: int = 10,
        ) -> dict:
            """Return popular locations and cuisines from anonymous usage (Phase 5)."""
            return get_popular(top_locations=top_locations, top_cuisines=top_cuisines)

    # Serve Phase 4 web UI from same origin so one URL works (API + UI on port 8000)
    _ui_path = Path(__file__).resolve().parent.parent / "phase4_web_ui"
    if _ui_path.is_dir():

        @app.get("/")
        def serve_ui_root():
            return FileResponse(_ui_path / "index.html")

        @app.get("/{rest:path}")
        def serve_ui_files(rest: str):
            if not rest or rest == "index.html":
                return FileResponse(_ui_path / "index.html")
            file_path = (_ui_path / rest).resolve()
            if file_path.is_file() and str(file_path).startswith(str(_ui_path)):
                return FileResponse(file_path)
            return FileResponse(_ui_path / "index.html")

    return app


app = create_app()
