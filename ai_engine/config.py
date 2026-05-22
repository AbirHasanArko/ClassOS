from backend.config import settings

class AIConfig:
    # Model Paths
    YOLO_MODEL_PATH = settings.YOLO_MODEL_PATH
    
    # Confidence Thresholds
    FACE_CONFIDENCE_AUTO = settings.FACE_CONFIDENCE_AUTO
    FACE_CONFIDENCE_FINGERPRINT = settings.FACE_CONFIDENCE_FINGERPRINT
    YOLO_CONFIDENCE = settings.YOLO_CONFIDENCE
    
    # Execution parameters
    HEAD_COUNT_INTERVAL = settings.HEAD_COUNT_INTERVAL
    FACE_UPSAMPLE_NUM = 1 # Number of times to upsample image for face detection (higher = smaller faces, slower)
    
    # Storage
    FACE_IMAGES_DIR = settings.FACE_IMAGES_DIR
    FACE_SAMPLES_PER_STUDENT = settings.FACE_SAMPLES_PER_STUDENT

ai_config = AIConfig()
