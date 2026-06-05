import cv2
import numpy as np
from typing import List, Tuple
import os

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics package not found. Head counting will be disabled.")

from ai_engine.config import ai_config

class HeadCounter:
    def __init__(self):
        self.model = None
        self._is_loaded = False
        
    def load_model(self):
        """Lazy load the YOLOv8 Nano model."""
        if not YOLO_AVAILABLE:
            return
            
        if self._is_loaded:
            return
            
        model_path = ai_config.YOLO_MODEL_PATH
        if not os.path.exists(model_path):
            print(f"Warning: YOLO model not found at {model_path}. Please run setup script.")
            return
            
        print("Loading YOLOv8 Nano model for head counting...")
        # Workaround for PyTorch 2.6 UnpicklingError with older Ultralytics versions
        import torch
        original_load = torch.load
        
        def bypass_weights_only_load(*args, **kwargs):
            if 'weights_only' not in kwargs:
                kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
            
        try:
            torch.load = bypass_weights_only_load
            self.model = YOLO(model_path)
        finally:
            torch.load = original_load
            
        self._is_loaded = True
        print("YOLOv8 model loaded.")

    def count_people(self, frame: np.ndarray) -> Tuple[int, List[Tuple[int, int, int, int]]]:
        """
        Run YOLO inference to detect people in the frame.
        Returns:
            Tuple of (person_count, list of bounding boxes)
        """
        if not self._is_loaded or self.model is None:
            self.load_model()
            if not self._is_loaded:
                return 0, []

        # Resize for faster inference on Pi (YOLO is heavy)
        # 320x320 is a good trade-off for Nano model on CPU
        resized_frame = cv2.resize(frame, (320, 320))
        
        # Run inference
        # class=0 filters for 'person' class only
        results = self.model(resized_frame, classes=[0], conf=ai_config.YOLO_CONFIDENCE, verbose=False)
        
        person_count = 0
        boxes = []
        
        if len(results) > 0:
            result = results[0]
            person_count = len(result.boxes)
            
            # Map boxes back to original image size
            orig_h, orig_w = frame.shape[:2]
            scale_x = orig_w / 320.0
            scale_y = orig_h / 320.0
            
            for box in result.boxes:
                # Get coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Scale back
                boxes.append((
                    int(x1 * scale_x),
                    int(y1 * scale_y),
                    int(x2 * scale_x),
                    int(y2 * scale_y)
                ))
                
        return person_count, boxes

# Singleton instance
head_counter = HeadCounter()
