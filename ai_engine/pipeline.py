import cv2
import numpy as np
from typing import Callable, List, Tuple, Any, Dict, Optional
from uuid import UUID

from ai_engine.face_detector import detector as face_detector
from ai_engine.face_recognizer import recognizer
from ai_engine.embedding_generator import EmbeddingGenerator
from ai_engine.head_counter import head_counter
from ai_engine.config import ai_config
from ai_engine.utils import draw_face_box, draw_head_box


class FaceRecognitionPipeline:
    """
    Processes Camera 0 frames for face recognition only.

    Used during Take Attendance mode. Runs dlib HOG face detection
    and ResNet 128D embedding comparison. Does NOT run YOLO head counting.

    Emits callbacks:
        - type="recognition"  → when a face is matched to a student
        - type="unknown_face" → when a face is detected but not recognized
    """

    def __init__(self):
        self.frame_count = 0
        self.is_running = False
        self.latest_annotated_frame: Optional[np.ndarray] = None

    async def initialize(self):
        """Load face embeddings from DB into memory before starting."""
        await recognizer.load_embeddings_from_db()

    def process_frame(self, frame: np.ndarray, on_result: Callable[[Dict[str, Any]], None]) -> np.ndarray:
        """
        Process a single Camera 0 frame through the face recognition pipeline.

        Draws bounding boxes and triggers callbacks for the attendance engine.
        Returns the annotated frame.

        Box colors:
            Green  (0, 255, 0)   → >= 70% confidence — auto-mark present
            Orange (0, 165, 255) → 30%–69% confidence — fingerprint needed
            Red    (0, 0, 255)   → < 30% / unknown
        """
        self.frame_count += 1
        annotated_frame = frame.copy()

        # 1. Face Detection — dlib HOG (fast, adequate for classroom distances)
        face_locations = face_detector.detect_faces(frame, ai_config.FACE_UPSAMPLE_NUM)

        # 2. Face Recognition
        for face_loc in face_locations:
            encoding = EmbeddingGenerator.generate_embedding_from_frame(frame, face_loc)

            if encoding is not None:
                student_id, confidence = recognizer.recognize_face(encoding)

                # Default: unknown red box
                box_color = (0, 0, 255)
                name = "Unknown"

                if student_id:
                    if confidence >= ai_config.FACE_CONFIDENCE_AUTO:
                        # >= 70% → auto-mark present
                        box_color = (0, 255, 0)   # Green
                        name = str(student_id)[:8]
                    elif confidence >= ai_config.FACE_CONFIDENCE_FINGERPRINT:
                        # 30%–69% → request fingerprint
                        box_color = (0, 165, 255)  # Orange
                        name = f"Verify FP (T:{ai_config.FACE_CONFIDENCE_AUTO:.2f})"

                    # Emit recognition event to Attendance Engine
                    on_result({
                        "type": "recognition",
                        "student_id": student_id,
                        "confidence": confidence,
                        "box": face_loc
                    })
                else:
                    # Face detected but too low confidence to associate with any student
                    on_result({
                        "type": "unknown_face",
                        "confidence": confidence
                    })

                # Draw bounding box on the frame
                draw_face_box(annotated_frame, face_loc, name, confidence, box_color)

        self.latest_annotated_frame = annotated_frame
        return annotated_frame


class HeadCountPipeline:
    """
    Processes Camera 1 frames for head counting only.

    Used during Verify Head Count mode. Runs YOLOv8 Nano to count
    the total number of people in the classroom. Does NOT run face recognition.

    Emits callbacks:
        - type="head_count" → when head counting is performed
    """

    def __init__(self):
        self.frame_count = 0
        self.last_head_count = 0
        self.is_running = False
        self.latest_annotated_frame: Optional[np.ndarray] = None

    def initialize(self):
        """Load the YOLOv8 model into memory."""
        head_counter.load_model()

    def process_frame(self, frame: np.ndarray, on_result: Callable[[Dict[str, Any]], None]) -> np.ndarray:
        """
        Process a single Camera 1 frame through the head counting pipeline.

        Runs YOLO every HEAD_COUNT_INTERVAL frames to save CPU on the Pi.
        Returns the annotated frame with bounding boxes.
        """
        self.frame_count += 1
        annotated_frame = frame.copy()

        # Run YOLO every N frames (configurable, default 5) to conserve CPU
        if self.frame_count % ai_config.HEAD_COUNT_INTERVAL == 0:
            count, boxes = head_counter.count_people(frame)
            self.last_head_count = count

            # Emit head count event with current recognized count
            # The recognized_count is provided by the Attendance Engine caller
            on_result({
                "type": "head_count",
                "count": count,
            })

            # Draw YOLO bounding boxes
            for box in boxes:
                draw_head_box(annotated_frame, box)

        # Overlay the latest head count on screen
        cv2.putText(
            annotated_frame,
            f"Head Count: {self.last_head_count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2
        )

        self.latest_annotated_frame = annotated_frame
        return annotated_frame


# ----- Singleton Instances -----
face_pipeline = FaceRecognitionPipeline()
head_count_pipeline = HeadCountPipeline()

# Backward-compatible alias — stream.py and other code that imports `pipeline`
# will continue to work. face_pipeline is the primary pipeline.
pipeline = face_pipeline
