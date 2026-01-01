"""In-memory cache service for topics."""

import asyncio
from collections import OrderedDict
from datetime import datetime
from typing import Any

from opinion_builder.config import settings
from opinion_builder.models.topic import Topic
from opinion_builder.models.websocket import (
    DepthDiffMessage,
    LastPriceMessage,
    LastTradeMessage,
)


class CacheService:
    """In-memory cache for topics with LRU eviction."""

    def __init__(self, max_size: int = 10000) -> None:
        """Initialize the cache."""
        self._topics: OrderedDict[int, Topic] = OrderedDict()
        self._lock = asyncio.Lock()
        self._max_size = max_size or settings.cache_max_size
        # Search index: keyword -> set of market_ids
        self._search_index: dict[str, set[int]] = {}

    async def get_topic(self, market_id: int) -> Topic | None:
        """Get a topic by market ID."""
        async with self._lock:
            return self._topics.get(market_id)

    async def set_topic(self, topic: Topic) -> None:
        """Set a topic in the cache."""
        async with self._lock:
            market_id = topic.market_id
            # Remove if exists to update order
            if market_id in self._topics:
                del self._topics[market_id]
            self._topics[market_id] = topic
            # Update search index
            self._update_search_index(topic)
            # Evict oldest if over limit
            if len(self._topics) > self._max_size:
                self._topics.popitem(last=False)

    async def get_all_topics(self) -> list[Topic]:
        """Get all topics."""
        async with self._lock:
            return list(self._topics.values())

    async def get_topic_count(self) -> int:
        """Get the number of topics in cache."""
        async with self._lock:
            return len(self._topics)

    async def update_price(self, market_id: int, outcome_side: int, price: str) -> None:
        """Update price for a topic."""
        async with self._lock:
            topic = self._topics.get(market_id)
            if topic:
                if outcome_side == 1:  # Yes
                    topic.yes_price = price
                    topic.last_price = price
                elif outcome_side == 2:  # No
                    topic.no_price = price
                topic.updated_at = datetime.now()

    async def update_from_ws_message(
        self,
        message: DepthDiffMessage | LastPriceMessage | LastTradeMessage,
    ) -> None:
        """Update topic from WebSocket message."""
        async with self._lock:
            topic = self._topics.get(message.market_id)
            if not topic:
                return

            topic.updated_at = datetime.now()

            if isinstance(message, LastPriceMessage):
                if message.outcome_side == 1:
                    topic.yes_price = message.price
                    topic.last_price = message.price
                elif message.outcome_side == 2:
                    topic.no_price = message.price
            elif isinstance(message, LastTradeMessage):
                # Update volume if possible
                if message.outcome_side == 1:
                    topic.yes_price = message.price
                    topic.last_price = message.price
                elif message.outcome_side == 2:
                    topic.no_price = message.price

    async def search(self, query: str, limit: int = 100) -> list[Topic]:
        """Search topics by keyword."""
        async with self._lock:
            query_lower = query.lower()
            results: list[Topic] = []

            for topic in self._topics.values():
                if (
                    query_lower in topic.question.lower()
                    or (topic.description and query_lower in topic.description.lower())
                    or any(query_lower in cat.lower() for cat in (topic.categories or []))
                ):
                    results.append(topic)
                    if len(results) >= limit:
                        break

            return results

    async def initialize_topics(self, topics: list[Topic]) -> None:
        """Initialize cache with a list of topics."""
        async with self._lock:
            for topic in topics:
                self._topics[topic.market_id] = topic
                self._update_search_index(topic)

    def _update_search_index(self, topic: Topic) -> None:
        """Update search index for a topic."""
        # Extract keywords from question and categories
        words = set(topic.question.lower().split())
        if topic.description:
            words.update(topic.description.lower().split())
        for category in topic.categories or []:
            words.update(category.lower().split())

        for word in words:
            if word not in self._search_index:
                self._search_index[word] = set()
            self._search_index[word].add(topic.market_id)


# Global cache instance
cache = CacheService()
