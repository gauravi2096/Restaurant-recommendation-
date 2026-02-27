"""
Preferences API: validate and normalize user preference inputs.
"""
from __future__ import annotations

import re
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class RecommendPreferences(BaseModel):
    """Validated user preferences for restaurant recommendations."""

    location: Optional[str] = Field(default=None, description="City or area name (e.g. Banashankari)")
    min_rating: Optional[float] = Field(default=None, ge=0, le=5, description="Minimum rating 0-5")
    min_cost: Optional[int] = Field(default=None, ge=0, description="Min cost for two (₹)")
    max_cost: Optional[int] = Field(default=None, ge=0, description="Max cost for two (₹)")
    cuisines: Optional[List[str]] = Field(default=None, description="Cuisine filters (any match)")
    rest_type: Optional[str] = Field(default=None, description="e.g. Cafe, Casual Dining")
    online_order: Optional[bool] = Field(default=None)
    book_table: Optional[bool] = Field(default=None)

    @field_validator("location", mode="before")
    @classmethod
    def normalize_location(cls, v: Any) -> Optional[str]:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("min_rating", mode="before")
    @classmethod
    def coerce_min_rating(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                return None
        return v

    @field_validator("min_cost", "max_cost", mode="before")
    @classmethod
    def coerce_cost(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v

    @field_validator("cuisines", mode="before")
    @classmethod
    def normalize_cuisines(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, list):
            out = [str(x).strip() for x in v if x is not None and str(x).strip()]
            return out if out else None
        if isinstance(v, str):
            parts = [p.strip() for p in re.split(r"[,;]+", v) if p.strip()]
            return parts if parts else None
        return None

    @field_validator("rest_type", mode="before")
    @classmethod
    def normalize_rest_type(cls, v: Any) -> Optional[str]:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return str(v).strip() or None

    def to_filter_kwargs(self, limit: int = 15) -> dict[str, Any]:
        """Convert to kwargs for RestaurantStore.query()."""
        kwargs: dict[str, Any] = {"limit": limit}
        if self.location:
            kwargs["location"] = self.location
        if self.min_rating is not None:
            kwargs["min_rate"] = self.min_rating
        if self.min_cost is not None:
            kwargs["min_cost"] = self.min_cost
        if self.max_cost is not None:
            kwargs["max_cost"] = self.max_cost
        if self.rest_type:
            kwargs["rest_type"] = self.rest_type
        if self.online_order is not None:
            kwargs["online_order"] = self.online_order
        if self.book_table is not None:
            kwargs["book_table"] = self.book_table
        return kwargs
