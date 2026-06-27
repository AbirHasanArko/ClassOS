from backend.config import settings

class AIConfig:
    # Model Paths
    YOLO_MODEL_PATH = settings.YOLO_MODEL_PATH

    # Confidence Thresholds
    # >= FACE_CONFIDENCE_AUTO        : Auto-mark present (FACE method)
    # >= FACE_CONFIDENCE_FINGERPRINT : Prompt fingerprint verification
    # < FACE_CONFIDENCE_FINGERPRINT  : Unknown / ignored
    # No face at all                 : Direct fingerprint scan always available
    FACE_CONFIDENCE_AUTO = settings.FACE_CONFIDENCE_AUTO           # 0.70
    FACE_CONFIDENCE_FINGERPRINT = settings.FACE_CONFIDENCE_FINGERPRINT  # 0.30
    YOLO_CONFIDENCE = settings.YOLO_CONFIDENCE

    # Execution parameters
    HEAD_COUNT_INTERVAL = settings.HEAD_COUNT_INTERVAL
    FACE_UPSAMPLE_NUM = 1  # Number of times to upsample image for face detection

    # Storage
    FACE_IMAGES_DIR = settings.FACE_IMAGES_DIR
    FACE_SAMPLES_PER_STUDENT = settings.FACE_SAMPLES_PER_STUDENT

ai_config = AIConfig()
