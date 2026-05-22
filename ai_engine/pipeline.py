import time
import asyncio
import numpy as np
from typing import Callable, List, Tuple
from uuid import UUID

from ai_engine.face_detector import detector as face_detector
from ai_engine.face_recognizer import recognizer
from ai_engine.embedding_generator import EmbeddingGenerator
from ai_engine.head_counter import head_counter
from ai_engine.config import ai_config
from ai_engine.utils import draw_face_box, draw_head_box

class AIPipeline:
    def __init__(self):
        self.frame_count = 0
        self.last_head_count = 0
        self.is_running = False
        
    async def initialize(self):
        """Load models into memory before starting."""
        await recognizer.load_embeddings_from_db()
        head_counter.load_model()
        
    def process_frame(self, frame: np.ndarray, on_result: Callable) -> np.ndarray:
        """
        Process a single frame through the pipeline.
        Draws bounding boxes and triggers callbacks for logic engine.
        Returns the annotated frame.
        """
        self.frame_count += 1
        annotated_frame = frame.copy()
        
        # 1. Face Detection
        # Get bounding boxes (top, right, bottom, left)
        face_locations = face_detector.detect_faces(frame, ai_config.FACE_UPSAMPLE_NUM)
        
        recognized_in_frame = set()
        
        # 2. Face Recognition
        for face_loc in face_locations:
            # Generate embedding for this specific face
            encoding = EmbeddingGenerator.generate_embedding_from_frame(frame, face_loc)
            
            if encoding is not None:
                student_id, confidence = recognizer.recognize_face(encoding)
                
                # Default unknown box
                box_color = (0, 0, 255) # Red
                name = "Unknown"
                
                if student_id:
                    recognized_in_frame.add(student_id)
                    
                    if confidence >= ai_config.FACE_CONFIDENCE_AUTO:
                        box_color = (0, 255, 0) # Green (Auto Attendance)
                        name = str(student_id)[:8] # Simplified for UI
                    elif confidence >= ai_config.FACE_CONFIDENCE_FINGERPRINT:
                        box_color = (0, 165, 255) # Orange (Needs Fingerprint)
                        name = "Verify FP"
                        
                    # Emit result to Attendance Engine
                    on_result({
                        "type": "recognition",
                        "student_id": student_id,
                        "confidence": confidence,
                        "box": face_loc
                    })
                
                # Draw the box
                draw_face_box(annotated_frame, face_loc, name, confidence, box_color)

        # 3. Head Counting (YOLOv8)
        # We only run this every N frames to save CPU, as it's heavy
        if self.frame_count % ai_config.HEAD_COUNT_INTERVAL == 0:
            count, boxes = head_counter.count_people(frame)
            self.last_head_count = count
            
            # Emit result
            on_result({
                "type": "head_count",
                "count": count,
                "recognized_count": len(recognized_in_frame)
            })
            
            # Draw boxes (optional, can be noisy, but good for debug)
            for box in boxes:
                draw_head_box(annotated_frame, box)
                
        # Draw the latest head count on screen
        cv2.putText(annotated_frame, f"Head Count: {self.last_head_count}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
                    
        return annotated_frame

pipeline = AIPipeline()
