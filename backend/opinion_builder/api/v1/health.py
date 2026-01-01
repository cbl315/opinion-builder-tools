"""Health check API."""

from fastapi import APIRouter, Request

from opinion_builder.models.websocket import HealthStatus
from opinion_builder.services.cache_service import cache
from opinion_builder.websocket.consumer import ws_consumer

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def health_check(request: Request) -> HealthStatus:  # noqa: ARG001
    """Health check endpoint with WebSocket status."""
    ws_status = ws_consumer.get_status()
    cache_size = await cache.get_topic_count()

    return HealthStatus(
        status="healthy" if ws_status["connected"] else "degraded",
        websocket_connected=ws_status["connected"],
        websocket_details=ws_status,
        cache_size=cache_size,
    )
