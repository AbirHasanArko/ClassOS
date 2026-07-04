"""
ClassOS — Centralized Configuration
Loads all settings from environment variables / .env file using Pydantic BaseSettings.
"""

from typing import List, Optional
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

    # ----- Camera 0 — Entry / Face Recognition (CAM/DISP 0 on RPi5) -----
    # Used for face recognition during Take Attendance mode.
    # Also the source for face enrollment from the Pi's connected camera.
    CAMERA_RESOLUTION_WIDTH: int = 1280
    CAMERA_RESOLUTION_HEIGHT: int = 720
    CAMERA_FPS: int = 30
    CAMERA_DEVICE_INDEX: int = 42  # /dev/video42 (v4l2loopback virtual device for IMX519)

    # ----- Camera 1 — Classroom Overhead / Head Count (CAM/DISP 1 on RPi5) -----
    # Used exclusively for YOLOv8 head counting in Verify Head Count mode.
    # If unavailable, the system gracefully falls back to single-camera mode.
    CAMERA_1_DEVICE_INDEX: int = 2  # /dev/video2 (CAM 1 / DISP 1 on RPi5)

    # ----- USB Webcam Fallback -----
    # Comma-separated list of device indices to try when the preferred
    # camera (CAMERA_DEVICE_INDEX or CAMERA_1_DEVICE_INDEX) cannot be opened.
    # The system probes each index in order and uses the first that opens.
    # Example in .env: CAMERA_USB_FALLBACK_INDICES=1,3,4
    #
    # Shared list used by both Camera 0 and Camera 1 unless overridden below.
    CAMERA_USB_FALLBACK_INDICES: List[int] = [1, 3, 4]

    # Per-camera overrides — set these if Camera 0 and Camera 1 should each
    # fall back to different USB devices (e.g., two separate USB webcams).
    # Leave unset (empty string in .env) to use the shared list above.
    # Example: CAMERA_0_USB_FALLBACK_INDICES=1
    #          CAMERA_1_USB_FALLBACK_INDICES=3
    CAMERA_0_USB_FALLBACK_INDICES: Optional[List[int]] = None
    CAMERA_1_USB_FALLBACK_INDICES: Optional[List[int]] = None

    @field_validator(
        "CAMERA_USB_FALLBACK_INDICES",
        "CAMERA_0_USB_FALLBACK_INDICES",
        "CAMERA_1_USB_FALLBACK_INDICES",
        mode="before",
    )
    @classmethod
    def parse_fallback_indices(cls, v):
        """Accept a plain list (from code) or a comma-separated string (from .env).
        An empty string means 'not set' and returns None (uses shared fallback).
        """
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @property
    def camera_0_fallback_indices(self) -> List[int]:
        """Effective fallback list for Camera 0."""
        return self.CAMERA_0_USB_FALLBACK_INDICES \
            if self.CAMERA_0_USB_FALLBACK_INDICES is not None \
            else self.CAMERA_USB_FALLBACK_INDICES

    @property
    def camera_1_fallback_indices(self) -> List[int]:
        """Effective fallback list for Camera 1."""
        return self.CAMERA_1_USB_FALLBACK_INDICES \
            if self.CAMERA_1_USB_FALLBACK_INDICES is not None \
            else self.CAMERA_USB_FALLBACK_INDICES

    # ----- Fingerprint Sensor (R307) & Hardware Button -----
    FINGERPRINT_UART_PORT: str = "/dev/ttyAMA0"
    FINGERPRINT_BAUD_RATE: int = 57600
    FINGERPRINT_MOCK_MODE: bool = False
    BUTTON_GPIO_PIN: int = 23

    # ----- AI Engine -----
    # Recognition thresholds:
    #   >= FACE_CONFIDENCE_AUTO        : Auto-mark present (FACE method)
    #   >= FACE_CONFIDENCE_FINGERPRINT : Prompt fingerprint verification
    #   < FACE_CONFIDENCE_FINGERPRINT  : Unknown / ignored
    #   No face at all                 : Direct fingerprint scan always available
    FACE_CONFIDENCE_AUTO: float = 0.70         # 70% → auto mark present
    FACE_CONFIDENCE_FINGERPRINT: float = 0.30  # 30% → prompt fingerprint
    YOLO_MODEL_PATH: str = "models/yolov8n.pt"
    YOLO_CONFIDENCE: float = 0.5
    HEAD_COUNT_INTERVAL: int = 5

    @field_validator("FACE_CONFIDENCE_AUTO", "FACE_CONFIDENCE_FINGERPRINT", mode="before")
    @classmethod
    def parse_confidence_percentage(cls, v):
        try:
            val = float(v)
            if val > 1.0:
                return val / 100.0
            return val
        except (TypeError, ValueError):
            return v


    # ----- LCD Display (20x4 I2C Character LCD — HD44780 + PCF8574 backpack) -----
    # Set LCD_ENABLED=false to disable the LCD (e.g., during development on non-Pi hardware).
    # The service falls back gracefully to stdout logging if hardware is unavailable.
    LCD_ENABLED: bool = True
    LCD_I2C_ADDRESS: int = 0x27   # Default PCF8574 I2C address (run: i2cdetect -y 1 to confirm)
    LCD_I2C_BUS: int = 1           # I2C bus number (/dev/i2c-1) on Raspberry Pi

    @field_validator("LCD_I2C_ADDRESS", mode="before")
    @classmethod
    def parse_hex_address(cls, v):
        if isinstance(v, str):
            if v.startswith("0x") or v.startswith("0X"):
                return int(v, 16)
            return int(v)
        return v

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
