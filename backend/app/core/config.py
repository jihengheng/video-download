from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Video Research Studio", alias="APP_NAME")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")
    secret_key: str = Field(default="replace-with-a-long-random-secret", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    database_url: str = Field(default="sqlite:///./storage/dev.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    object_storage_dir: Path = Field(default=Path("storage/object_store"), alias="OBJECT_STORAGE_DIR")
    workspace_dir: Path = Field(default=Path("storage/workspace"), alias="WORKSPACE_DIR")
    openai_base_url: str = Field(default="https://api.deepseek.com", alias="OPENAI_BASE_URL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="deepseek-chat", alias="OPENAI_MODEL")
    default_daily_quota: int = Field(default=3, alias="DEFAULT_DAILY_QUOTA")
    anon_daily_quota: int = Field(default=1, alias="ANON_DAILY_QUOTA")
    max_task_retries: int = Field(default=2, alias="MAX_TASK_RETRIES")
    max_video_duration_seconds: int = Field(default=7200, alias="MAX_VIDEO_DURATION_SECONDS")
    max_video_file_size_mb: int = Field(default=1024, alias="MAX_VIDEO_FILE_SIZE_MB")
    max_url_length: int = Field(default=2048, alias="MAX_URL_LENGTH")
    jwt_issuer: str = Field(default="video-research-studio", alias="JWT_ISSUER")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.object_storage_dir.mkdir(parents=True, exist_ok=True)
    settings.workspace_dir.mkdir(parents=True, exist_ok=True)
    return settings
