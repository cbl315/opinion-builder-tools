"""Topic service for business logic."""

from datetime import datetime
from decimal import Decimal

from opinion_builder.models.filter import (
    Filters,
    Pagination,
    SortOption,
    TopicFilterRequest,
)
from opinion_builder.models.topic import Topic
from opinion_builder.sdk.client import OpinionSDKClient
from opinion_builder.services.cache_service import cache


class TopicService:
    """Service for topic operations."""

    def __init__(self, sdk_client: OpinionSDKClient) -> None:
        """Initialize the topic service."""
        self.sdk_client = sdk_client

    async def get_topics(
        self,
        limit: int = 50,
        offset: int = 0,
        end_date_before: datetime | None = None,
        end_date_after: datetime | None = None,
        order_by: str = "end_date",
        order: str = "asc",
    ) -> tuple[list[Topic], int]:
        """Get topics with filtering and pagination."""
        all_topics = await cache.get_all_topics()
        filtered = self._apply_filters(all_topics, end_date_before, end_date_after)
        sorted_topics = self._apply_sort(filtered, order_by, order)
        total = len(sorted_topics)
        paginated = self._apply_pagination(sorted_topics, limit, offset)
        return paginated, total

    async def get_topic_by_id(self, topic_id: str) -> Topic | None:
        """Get a single topic by ID."""
        all_topics = await cache.get_all_topics()
        for topic in all_topics:
            if topic.id == topic_id:
                return topic
        return None

    async def search_topics(
        self,
        query: str,
        limit: int = 100,
        fuzzy: bool = True,
    ) -> list[Topic]:
        """Search topics by keyword."""
        if fuzzy:
            return await cache.search(query, limit)
        # Exact match (simplified)
        all_topics = await cache.get_all_topics()
        results = [
            t for t in all_topics if query.lower() in t.question.lower()
        ]
        return results[:limit]

    async def filter_topics(self, request: TopicFilterRequest) -> tuple[list[Topic], int]:
        """Advanced filter topics."""
        all_topics = await cache.get_all_topics()
        filters = request.filters or Filters()
        sort_opt = request.sort or SortOption()
        pagination = request.pagination or Pagination()

        filtered = self._apply_advanced_filters(all_topics, filters)
        sorted_topics = self._apply_sort(
            filtered, sort_opt.field, sort_opt.order
        )
        total = len(sorted_topics)
        paginated = self._apply_pagination(
            sorted_topics, pagination.limit, pagination.offset
        )
        return paginated, total

    async def load_initial_topics(self) -> None:
        """Load topics from SDK and initialize cache."""
        markets = await self.sdk_client.get_markets(limit=500)
        topics = []
        for market in markets:
            topic = self._market_to_topic(market)
            if topic:
                topics.append(topic)
        await cache.initialize_topics(topics)

    def _market_to_topic(self, market: dict) -> Topic | None:
        """Convert market dict to Topic model."""
        try:
            return Topic(
                id=str(market.get("id", "")),
                market_id=int(market.get("id", 0)),
                question=market.get("question", ""),
                description=market.get("description"),
                end_date=self._parse_datetime(market.get("endDate")),
                outcome_type=market.get("outcomeType", "binary"),
                volume=self._parse_decimal(market.get("volume")),
                last_price=market.get("lastPrice"),
                yes_price=market.get("yesPrice"),
                no_price=market.get("noPrice"),
                liquidity=market.get("liquidity"),
                created_at=self._parse_datetime(market.get("createdAt")),
                updated_at=datetime.now(),
                categories=market.get("categories", []),
                slug=market.get("slug", ""),
            )
        except Exception:
            return None

    def _apply_filters(
        self,
        topics: list[Topic],
        end_date_before: datetime | None,
        end_date_after: datetime | None,
    ) -> list[Topic]:
        """Apply date filters."""
        filtered = topics
        if end_date_before:
            filtered = [t for t in filtered if t.end_date and t.end_date <= end_date_before]
        if end_date_after:
            filtered = [t for t in filtered if t.end_date and t.end_date >= end_date_after]
        return filtered

    def _apply_advanced_filters(self, topics: list[Topic], filters: Filters) -> list[Topic]:
        """Apply advanced filters."""
        filtered = topics

        if filters.end_date_range:
            if filters.end_date_range.start:
                filtered = [
                    t for t in filtered
                    if t.end_date and t.end_date >= filters.end_date_range.start  # type: ignore
                ]
            if filters.end_date_range.end:
                filtered = [
                    t for t in filtered
                    if t.end_date and t.end_date <= filters.end_date_range.end  # type: ignore
                ]

        if filters.outcome_types:
            filtered = [t for t in filtered if t.outcome_type in filters.outcome_types]

        if filters.categories:
            filtered = [
                t for t in filtered
                if any(c in (t.categories or []) for c in filters.categories)
            ]

        if filters.keywords:
            filtered = [
                t for t in filtered
                if any(k.lower() in t.question.lower() for k in filters.keywords)
            ]

        if filters.exclude_keywords:
            filtered = [
                t for t in filtered
                if not any(k.lower() in t.question.lower() for k in filters.exclude_keywords)
            ]

        if filters.price_range:
            if filters.price_range.min:
                filtered = [
                    t for t in filtered
                    if t.last_price and float(t.last_price) >= float(filters.price_range.min)  # type: ignore
                ]
            if filters.price_range.max:
                filtered = [
                    t for t in filtered
                    if t.last_price and float(t.last_price) <= float(filters.price_range.max)  # type: ignore
                ]

        if filters.min_volume is not None:
            filtered = [
                t for t in filtered
                if t.volume and t.volume >= Decimal(str(filters.min_volume))  # type: ignore
            ]

        if filters.max_volume is not None:
            filtered = [
                t for t in filtered
                if t.volume and t.volume <= Decimal(str(filters.max_volume))  # type: ignore
            ]

        if filters.created_after:
            filtered = [
                t for t in filtered
                if t.created_at and t.created_at >= filters.created_after  # type: ignore
            ]

        return filtered

    def _apply_sort(self, topics: list[Topic], field: str, order: str) -> list[Topic]:
        """Apply sorting."""
        reverse = order.lower() == "desc"

        if field == "end_date":
            return sorted(topics, key=lambda t: t.end_date or datetime.min, reverse=reverse)
        elif field == "created_at":
            return sorted(topics, key=lambda t: t.created_at or datetime.min, reverse=reverse)
        elif field == "volume":
            return sorted(topics, key=lambda t: t.volume or Decimal(0), reverse=reverse)
        elif field == "last_price":
            return sorted(
                topics,
                key=lambda t: float(t.last_price or 0),
                reverse=reverse,
            )
        return topics

    def _apply_pagination(
        self, topics: list[Topic], limit: int, offset: int
    ) -> list[Topic]:
        """Apply pagination."""
        return topics[offset : offset + limit]

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """Parse datetime from string."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    def _parse_decimal(self, value: str | float | None) -> Decimal | None:
        """Parse decimal from value."""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except Exception:
            return None
