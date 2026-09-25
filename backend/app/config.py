"""
Central configuration for the Quarry Monitoring backend.
All values are loaded from environment variables (.env file).
NEVER hard-code secrets here.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ---------------- Database ----------------
    DATABASE_URL: str = Field(
        default="postgresql://quarry_user:quarry_pass@localhost:5432/quarry_monitoring",
        description="SQLAlchemy connection string for PostgreSQL",
    )

    # ---------------- Google Earth Engine ----------------
    # Service account email, e.g. my-gee-bot@my-project.iam.gserviceaccount.com
    GEE_SERVICE_ACCOUNT: str = Field(default="")
    # Absolute path to the downloaded service-account JSON key file
    GEE_PRIVATE_KEY_FILE: str = Field(default="")
    # Your Earth Engine cloud project id (required for the new EE API)
    GEE_PROJECT_ID: str = Field(default="")

    # ---------------- Quarry / detection thresholds ----------------
    UNAUTHORIZED_AREA_THRESHOLD_HA: float = Field(
        default=0.01,
        description="Minimum unauthorized new-excavation area (hectares) that triggers an alert",
    )
    NDVI_THRESHOLD: float = Field(default=0.2)
    BSI_THRESHOLD: float = Field(default=0.1)
    CLOUD_COVER_MAX: float = Field(default=20.0)
    # How many days back to search for a usable Sentinel-2 image
    IMAGE_SEARCH_WINDOW_DAYS: int = Field(default=30)
    # Morphological cleanup kernel radius in pixels (0 = disabled)
    MORPHOLOGY_KERNEL_RADIUS: int = Field(default=1)
    # Reject isolated 10 m pixels before calculating detected area. This keeps
    # the 0.01 ha alert threshold unchanged while requiring spatial coherence.
    MIN_CONNECTED_PIXELS: int = Field(default=2)

    # ---------------- Scheduler ----------------
    ENABLE_SCHEDULER: bool = Field(default=True)
    # Cron-style: day_of_week (sat), hour, minute
    SCHEDULE_DAY_OF_WEEK: str = Field(default="sat")
    SCHEDULE_HOUR: int = Field(default=8)
    SCHEDULE_MINUTE: int = Field(default=0)

    # ---------------- SMTP / Email notifications ----------------
    SMTP_HOST: str = Field(default="")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    ALERT_EMAIL: str = Field(default="")
    SMTP_USE_TLS: bool = Field(default=True)
    # Dashboard alerts are always persisted. Email is an optional secondary
    # notification channel and is disabled by default for local development.
    ENABLE_EMAIL_NOTIFICATIONS: bool = Field(default=False)

    # ---------------- App ----------------
    APP_NAME: str = Field(default="Quarry Monitoring System")
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
