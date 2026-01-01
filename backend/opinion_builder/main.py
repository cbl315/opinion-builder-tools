"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from opinion_builder.api.v1.health import router as health_router
from opinion_builder.api.v1.topics import router as topics_router
from opinion_builder.config import settings
from opinion_builder.sdk.client import OpinionSDKClient
from opinion_builder.services.topic_service import TopicService
from opinion_builder.websocket.consumer import ws_consumer

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Opinion Builder API")

    # Initialize SDK client
    sdk_client = OpinionSDKClient()

    # Initialize topic service
    topic_service = TopicService(sdk_client)

    # Load initial topics
    try:
        await topic_service.load_initial_topics()
        logger.info("Initial topics loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load initial topics: {e}")

    # Start WebSocket consumer
    try:
        await ws_consumer.start()
        logger.info("WebSocket consumer started")
    except Exception as e:
        logger.error(f"Failed to start WebSocket consumer: {e}")

    # Store services in app state
    app.state.topic_service = topic_service  # type: ignore
    app.state.sdk_client = sdk_client  # type: ignore

    yield

    # Shutdown
    logger.info("Shutting down Opinion Builder API")
    await ws_consumer.stop()
    await sdk_client.close()


app = FastAPI(
    title="Opinion Builder Tools",
    description="API for discovering and filtering prediction market topics",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(health_router)
app.include_router(topics_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Opinion Builder Tools API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "opinion_builder.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
