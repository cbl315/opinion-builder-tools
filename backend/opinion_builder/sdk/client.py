"""opinion_clob_sdk wrapper."""

from datetime import datetime
from typing import Any

import httpx

from opinion_builder.config import settings


class OpinionSDKClient:
    """Wrapper for opinion_clob_sdk."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the SDK client."""
        self.api_key = api_key or settings.opinion_sdk_api_key
        self.base_url = base_url or settings.opinion_sdk_base_url
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def get_markets(
        self,
        limit: int = 200,
        offset: int = 0,
        active: bool = True,
    ) -> list[dict[str, Any]]:
        """Get markets from opinion.trade API."""
        params = {
            "limit": limit,
            "offset": offset,
            "active": str(active).lower(),
        }
        response = await self._client.get("/markets", params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("markets", [])

    async def get_market(self, market_id: int) -> dict[str, Any]:
        """Get a single market by ID."""
        response = await self._client.get(f"/markets/{market_id}")
        response.raise_for_status()
        return response.json()

    def get_market_orderbook(self, market_id: int) -> dict[str, Any]:
        """Get order book for a market (sync method for initial load)."""
        # This can be a sync method since opinion_clob_sdk might have sync methods
        # For now, returning placeholder
        return {}
