"""WebSocket message models."""

from enum import Enum

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """WebSocket message types."""

    DEPTH_DIFF = "market.depth.diff"
    LAST_PRICE = "market.last.price"
    LAST_TRADE = "market.last.trade"


class DepthDiffMessage(BaseModel):
    """market.depth.diff message."""

    market_id: int = Field(..., alias="marketId")
    token_id: str = Field(..., alias="tokenId")
    outcome_side: int = Field(..., alias="outcomeSide")
    side: str  # bids or asks
    price: str
    size: str
    msg_type: MessageType = Field(..., alias="msgType")

    model_config = {"populate_by_name": True}


class LastPriceMessage(BaseModel):
    """market.last.price message."""

    market_id: int = Field(..., alias="marketId")
    token_id: str = Field(..., alias="tokenId")
    outcome_side: int = Field(..., alias="outcomeSide")
    price: str
    msg_type: MessageType = Field(..., alias="msgType")

    model_config = {"populate_by_name": True}


class LastTradeMessage(BaseModel):
    """market.last.trade message."""

    market_id: int = Field(..., alias="marketId")
    token_id: str = Field(..., alias="tokenId")
    outcome_side: int = Field(..., alias="outcomeSide")
    side: str  # Buy or Sell
    price: str
    shares: str
    amount: str
    msg_type: MessageType = Field(..., alias="msgType")

    model_config = {"populate_by_name": True}


class WebSocketSubscribeMessage(BaseModel):
    """WebSocket subscribe message."""

    action: str = "SUBSCRIBE"
    channel: str
    market_id: int | None = Field(None, alias="marketId")
    root_market_id: int | None = Field(None, alias="rootMarketId")

    model_config = {"populate_by_name": True}

    def to_json(self) -> str:
        """Convert to JSON string for WebSocket send."""
        import json

        data = {"action": self.action, "channel": self.channel}
        if self.market_id is not None:
            data["marketId"] = self.market_id
        if self.root_market_id is not None:
            data["rootMarketId"] = self.root_market_id
        return json.dumps(data)


class HealthStatus(BaseModel):
    """Health check response."""

    status: str
    websocket_connected: bool
    websocket_details: dict[str, str | bool | int | None] | None = None
    cache_size: int | None = None
