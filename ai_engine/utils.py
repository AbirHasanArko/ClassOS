import cv2
import numpy as np
from typing import Tuple

def draw_face_box(frame: np.ndarray, box: Tuple[int, int, int, int], name: str, confidence: float, color: Tuple[int, int, int] = (0, 255, 0)):
    """
    Draw a bounding box around a face with a name and confidence score.
    Args:
        box: (top, right, bottom, left)
        color: BGR tuple, default green
    """
    top, right, bottom, left = box
    
    # Draw box
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    
    # Draw label background
    label = f"{name} ({confidence*100:.1f}%)"
    font = cv2.FONT_HERSHEY_DUPLEX
    text_size = cv2.getTextSize(label, font, 0.5, 1)[0]
    
    cv2.rectangle(frame, (left, bottom), (left + text_size[0] + 6, bottom + text_size[1] + 6), color, cv2.FILLED)
    
    # Draw text
    cv2.putText(frame, label, (left + 3, bottom + text_size[1] + 3), font, 0.5, (255, 255, 255), 1)

def draw_head_box(frame: np.ndarray, box: Tuple[int, int, int, int]):
    """
    Draw a bounding box for a YOLO person detection.
    Args:
        box: (x1, y1, x2, y2)
    """
    x1, y1, x2, y2 = box
    # Purple color for YOLO detection to distinguish from Face detection
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 1)
