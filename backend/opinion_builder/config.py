"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # SDK
    opinion_sdk_api_key: str = ""
    opinion_sdk_base_url: str = "https://api.opinion.trade"

    # WebSocket
    opinion_ws_api_key: str = ""
    opinion_ws_url: str = "wss://ws.opinion.trade"
    opinion_ws_heartbeat_interval: int = 30

    # Cache
    cache_enabled: bool = True
    cache_max_size: int = 10000

    # Pagination
    default_limit: int = 50
    max_limit: int = 200


# Global settings instance
settings = Settings()
