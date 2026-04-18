from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LUMERA CRYSTAL API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_public_base_url: str = "http://localhost:8000"
    app_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"
    admin_jwt_secret: str = "change-this-in-production"
    admin_jwt_algorithm: str = "HS256"
    admin_jwt_exp_minutes: int = 60 * 24
    admin_default_email: str = "admin@lumeracrystal.com"
    admin_default_password: str = "Lumera@123456"
    media_max_upload_size_mb: int = 5
    media_max_video_upload_size_mb: int = 20
    media_allowed_mime_types: str = "image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime"
    media_max_duration_seconds: int = 8
    stock_low_threshold: int = 5
    auto_restock_quantity: int = 30
    points_earn_rate: int = 10

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_from_email: str = "no-reply@lumeracrystal.com"
    smtp_from_name: str = "LUMERA CRYSTAL"

    mail_contacts_path: str = "config/mail_contacts.json"

    llm_provider: str | None = None  # "openai" or "ollama"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_timeout_seconds: int = 20

    chat_history_limit: int = 12
    chat_history_fallback: str = "none"  # "none" | "memory"
    support_chat_debug: bool = False

    capability_news_enabled: bool = False
    capability_news_provider: str = "juhe"
    capability_news_default_limit: int = 5
    capability_news_max_age_days: int = 30

    capability_weather_enabled: bool = False
    capability_exchange_rate_enabled: bool = False

    weather_api_base_url: str | None = None
    weather_api_key: str | None = None
    weather_api_path: str | None = None
    weather_api_timeout_seconds: int = 10

    exchange_rate_api_base_url: str | None = None
    exchange_rate_api_key: str | None = None
    exchange_rate_api_path: str | None = None
    exchange_rate_api_timeout_seconds: int = 10

    provider_juhe_base_url: str | None = None
    provider_juhe_api_key: str | None = None
    provider_juhe_news_path: str | None = None
    provider_juhe_timeout_seconds: int = 10
    provider_juhe_key_header: str = ""
    provider_juhe_key_prefix: str = ""
    provider_juhe_key_query_param: str = "key"
    provider_juhe_query_param: str = "word"

    # Deprecated news config (keep for short-term compatibility)
    news_api_enabled: bool = False
    news_api_base_url: str | None = None
    news_api_path: str | None = None
    news_api_key: str | None = None
    news_api_timeout_seconds: int = 10
    news_api_key_header: str = "Authorization"
    news_api_key_prefix: str = "Bearer"
    news_api_default_limit: int = 5

    logistics_service_enabled: bool = True
    logistics_service_base_url: str = "http://localhost:8010/api/v1/logistics"
    logistics_service_timeout_seconds: int = 8

    database_url: str = "postgresql+psycopg://postgres:123456@localhost:6543/lumera"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.app_cors_origins.split(",") if origin.strip()]

    @property
    def allowed_media_mime_types(self) -> set[str]:
        return {item.strip() for item in self.media_allowed_mime_types.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
