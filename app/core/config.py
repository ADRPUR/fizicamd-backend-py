from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_issuer: str = Field(alias="JWT_ISSUER", default="fizicamd")
    access_ttl_seconds: int = Field(alias="ACCESS_TTL_SECONDS", default=14400)
    refresh_ttl_seconds: int = Field(alias="REFRESH_TTL_SECONDS", default=1209600)
    media_storage_path: str = Field(alias="MEDIA_STORAGE_PATH", default="storage/media")
    metrics_disk_path: str = Field(alias="METRICS_DISK_PATH", default="storage/media")
    metrics_sample_interval: int = Field(alias="METRICS_SAMPLE_INTERVAL", default=5)
    cors_origins: str = Field(alias="CORS_ORIGINS", default="")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
