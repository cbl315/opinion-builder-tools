"""Filter data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DateRangeFilter(BaseModel):
    """Date range filter."""

    start: Optional[datetime] = None
    end: Optional[datetime] = None


class PriceRange(BaseModel):
    """Price range filter."""

    min: Optional[str] = None
    max: Optional[str] = None


class Filters(BaseModel):
    """Advanced filter options."""

    end_date_range: Optional[DateRangeFilter] = None
    outcome_types: Optional[list[str]] = Field(
        default_factory=list, description="binary, scalar, categorical"
    )
    categories: Optional[list[str]] = Field(default_factory=list)
    keywords: Optional[list[str]] = Field(default_factory=list)
    exclude_keywords: Optional[list[str]] = Field(default_factory=list)
    price_range: Optional[PriceRange] = None
    min_volume: Optional[float] = None
    max_volume: Optional[float] = None
    created_after: Optional[datetime] = None


class SortOption(BaseModel):
    """Sort options."""

    field: str = Field(
        default="end_date",
        description="Sort field: end_date, created_at, volume, last_price",
    )
    order: str = Field(default="asc", description="Sort order: asc, desc")


class Pagination(BaseModel):
    """Pagination options."""

    limit: int = Field(default=50, ge=1, le=200, description="Return count (max 200)")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class TopicFilterRequest(BaseModel):
    """Request model for topic filtering."""

    filters: Optional[Filters] = None
    sort: Optional[SortOption] = None
    pagination: Optional[Pagination] = None
