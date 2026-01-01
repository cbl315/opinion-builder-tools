"""Topic data models."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class Topic(BaseModel):
    """Prediction market topic model."""

    id: str = Field(..., description="Topic unique identifier")
    market_id: int = Field(..., description="Market ID for WebSocket subscription")
    question: str = Field(..., description="Prediction question")
    description: Optional[str] = Field(None, description="Detailed description")
    end_date: Optional[datetime] = Field(None, description="End time")
    outcome_type: str = Field(..., description="Outcome type: binary/scalar/categorical")
    volume: Optional[Decimal] = Field(None, description="Trading volume")
    last_price: Optional[str] = Field(None, description="Latest price (real-time via WebSocket)")
    yes_price: Optional[str] = Field(None, description="Yes price")
    no_price: Optional[str] = Field(None, description="No price")
    liquidity: Optional[str] = Field(None, description="Liquidity")
    created_at: Optional[datetime] = Field(None, description="Creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    categories: Optional[list[str]] = Field(default_factory=list, description="Category tags")
    slug: Optional[str] = Field(None, description="URL-friendly identifier")

    model_config = {"from_attributes": True}


class TopicListResponse(BaseModel):
    """Response model for topic list."""

    items: list[Topic]
    total: int
    limit: int
    offset: int


class TopicDetailResponse(BaseModel):
    """Response model for single topic detail."""

    data: Topic
