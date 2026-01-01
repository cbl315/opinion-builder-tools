"""API v1 routes for topics."""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status

from opinion_builder.config import settings
from opinion_builder.models.error import ErrorDetail
from opinion_builder.models.filter import TopicFilterRequest
from opinion_builder.models.topic import TopicDetailResponse, TopicListResponse
from opinion_builder.services.topic_service import TopicService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=TopicListResponse)
async def get_topics(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    end_date_before: Annotated[datetime | None, Query()] = None,
    end_date_after: Annotated[datetime | None, Query()] = None,
    order_by: Annotated[str, Query()] = "end_date",
    order: Annotated[str, Query()] = "asc",
) -> TopicListResponse:
    """Get topics list with filtering and pagination."""
    service = request.app.state.topic_service  # type: ignore
    items, total = await service.get_topics(
        limit=limit,
        offset=offset,
        end_date_before=end_date_before,
        end_date_after=end_date_after,
        order_by=order_by,
        order=order,
    )
    return TopicListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/search", response_model=TopicListResponse)
async def search_topics(
    request: Request,
    q: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    fuzzy: Annotated[bool, Query()] = True,
) -> TopicListResponse:
    """Search topics by keyword."""
    service = request.app.state.topic_service  # type: ignore
    items = await service.search_topics(query=q, limit=limit, fuzzy=fuzzy)
    return TopicListResponse(items=items, total=len(items), limit=limit, offset=0)


@router.post("/filter", response_model=TopicListResponse)
async def filter_topics(
    request: Request,
    body: TopicFilterRequest,
) -> TopicListResponse:
    """Advanced filter topics."""
    service = request.app.state.topic_service  # type: ignore
    items, total = await service.filter_topics(body)
    limit = body.pagination.limit if body.pagination else settings.default_limit
    offset = body.pagination.offset if body.pagination else 0
    return TopicListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{topic_id}", response_model=TopicDetailResponse)
async def get_topic(request: Request, topic_id: str) -> TopicDetailResponse:
    """Get a single topic by ID."""
    service = request.app.state.topic_service  # type: ignore
    topic = await service.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(code="NOT_FOUND", message=f"Topic {topic_id} not found").model_dump(),
        )
    return TopicDetailResponse(data=topic)
