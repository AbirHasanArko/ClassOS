"""
ClassOS — Centralized Configuration
Loads all settings from environment variables / .env file using Pydantic BaseSettings.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ----- Application -----
    APP_NAME: str = "ClassOS"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"

    # ----- Database -----
    DATABASE_URL: str = "postgresql+asyncpg://classos:classos_secret@localhost:5432/classos_db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # ----- JWT Authentication -----
    JWT_SECRET_KEY: str = "change-me-to-a-random-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ----- CORS -----
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """Keep as string; we split in the property."""
        return v

    @property
    def cors_origin_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # ----- Camera (USB Webcam) -----
    CAMERA_RESOLUTION_WIDTH: int = 1280
    CAMERA_RESOLUTION_HEIGHT: int = 720
    CAMERA_FPS: int = 30
    CAMERA_DEVICE_INDEX: int = 0  # /dev/video0 (or index for cv2.VideoCapture)

    # ----- Fingerprint Sensor (R307) -----
    FINGERPRINT_UART_PORT: str = "/dev/ttyS0"
    FINGERPRINT_BAUD_RATE: int = 57600
    FINGERPRINT_MOCK_MODE: bool = False

    # ----- AI Engine -----
    FACE_CONFIDENCE_AUTO: float = 0.90
    FACE_CONFIDENCE_FINGERPRINT: float = 0.70
    YOLO_MODEL_PATH: str = "models/yolov8n.pt"
    YOLO_CONFIDENCE: float = 0.5
    HEAD_COUNT_INTERVAL: int = 5

    # ----- File Storage -----
    FACE_IMAGES_DIR: str = "data/faces"
    FACE_SAMPLES_PER_STUDENT: int = 20

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def camera_resolution(self) -> tuple[int, int]:
        return (self.CAMERA_RESOLUTION_WIDTH, self.CAMERA_RESOLUTION_HEIGHT)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Singleton settings instance
settings = Settings()
