"""WebSocket consumer for opinion.trade real-time updates."""

import asyncio
import json
import logging
from typing import Any

import websocket
from pydantic import ValidationError

from opinion_builder.config import settings
from opinion_builder.models.websocket import (
    DepthDiffMessage,
    LastPriceMessage,
    LastTradeMessage,
    MessageType,
    WebSocketSubscribeMessage,
)
from opinion_builder.services.cache_service import cache

logger = logging.getLogger(__name__)


class OpinionWebSocketConsumer:
    """WebSocket consumer for opinion.trade."""

    def __init__(
        self,
        api_key: str | None = None,
        url: str | None = None,
        heartbeat_interval: int | None = None,
    ) -> None:
        """Initialize the WebSocket consumer."""
        self.api_key = api_key or settings.opinion_ws_api_key
        self.url = url or settings.opinion_ws_url
        self.heartbeat_interval = heartbeat_interval or settings.opinion_ws_heartbeat_interval
        self._ws: websocket.WebSocketApp | None = None
        self._running = False
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._reconnect_delay = 5
        self._max_reconnect_delay = 60

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._ws is not None and self._running

    async def start(self) -> None:
        """Start the WebSocket connection."""
        self._running = True
        await self._connect_with_retry()

    async def stop(self) -> None:
        """Stop the WebSocket connection."""
        self._running = False
        if self._ws:
            self._ws.close()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _connect_with_retry(self) -> None:
        """Connect with auto-retry."""
        while self._running:
            try:
                await self._connect()
                self._reconnect_delay = 5  # Reset on success
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                if self._running:
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(
                        self._reconnect_delay * 2, self._max_reconnect_delay
                    )

    async def _connect(self) -> None:
        """Establish WebSocket connection."""
        ws_url = f"{self.url}?apikey={self.api_key}"

        def on_message(ws: websocket.WebSocketApp, message: str) -> None:
            asyncio.create_task(self._handle_message(message))

        def on_error(ws: websocket.WebSocketApp, error: Exception) -> None:
            logger.error(f"WebSocket error: {error}")

        def on_close(
            ws: websocket.WebSocketApp,
            close_status_code: int | None,
            close_msg: str | None,
        ) -> None:
            logger.warning("WebSocket connection closed")
            self._running = False

        def on_open(ws: websocket.WebSocketApp) -> None:
            logger.info("WebSocket connection established")
            self._running = True
            # Subscribe to all markets after connection
            asyncio.create_task(self._subscribe_all_markets())

        self._ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )

        # Run WebSocket in a thread
        await asyncio.to_thread(self._ws.run_forever)

        # Start heartbeat after connection
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _subscribe_all_markets(self) -> None:
        """Subscribe to all markets in cache."""
        topics = await cache.get_all_topics()
        for topic in topics:
            await self._subscribe_market(topic.market_id, topic.outcome_type)

    async def _subscribe_market(self, market_id: int, outcome_type: str) -> None:
        """Subscribe to market updates."""
        if not self._ws:
            return

        if outcome_type == "categorical":
            # For categorical markets, use rootMarketId
            msg = WebSocketSubscribeMessage(
                action="SUBSCRIBE",
                channel="market.last.price",
                root_market_id=market_id,
            )
        else:
            msg = WebSocketSubscribeMessage(
                action="SUBSCRIBE",
                channel="market.last.price",
                market_id=market_id,
            )

        self._ws.send(msg.to_json())

        # Also subscribe to depth and trade channels
        if outcome_type != "categorical":
            depth_msg = WebSocketSubscribeMessage(
                action="SUBSCRIBE",
                channel="market.depth.diff",
                market_id=market_id,
            )
            self._ws.send(depth_msg.to_json())

            trade_msg = WebSocketSubscribeMessage(
                action="SUBSCRIBE",
                channel="market.last.trade",
                market_id=market_id,
            )
            self._ws.send(trade_msg.to_json())

    async def _heartbeat_loop(self) -> None:
        """Send heartbeat messages periodically."""
        while self._running and self._ws:
            try:
                self._ws.send(json.dumps({"action": "HEARTBEAT"}))
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    async def _handle_message(self, message: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            data: dict[str, Any] = json.loads(message)
            msg_type = data.get("msgType")

            if msg_type == MessageType.DEPTH_DIFF:
                parsed = DepthDiffMessage(**data)
                await cache.update_from_ws_message(parsed)
            elif msg_type == MessageType.LAST_PRICE:
                parsed = LastPriceMessage(**data)
                await cache.update_from_ws_message(parsed)
            elif msg_type == MessageType.LAST_TRADE:
                parsed = LastTradeMessage(**data)
                await cache.update_from_ws_message(parsed)
            elif msg_type == "PONG":
                pass  # Heartbeat response
            else:
                logger.debug(f"Unhandled message type: {msg_type}")
        except ValidationError as e:
            logger.warning(f"Message validation error: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get WebSocket status."""
        return {
            "connected": self.is_connected,
            "url": self.url,
            "heartbeat_interval": self.heartbeat_interval,
        }


# Global WebSocket consumer instance
ws_consumer = OpinionWebSocketConsumer()
