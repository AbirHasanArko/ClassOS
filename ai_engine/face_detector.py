import cv2
import numpy as np
import dlib
from typing import List, Tuple

class FaceDetector:
    def __init__(self):
        # We use dlib's HOG face detector because it is much faster on a 
        # Raspberry Pi CPU than the CNN-based detector, while providing
        # adequate accuracy for classroom distances.
        self.detector = dlib.get_frontal_face_detector()
        
    def detect_faces(self, image: np.ndarray, upsample_num: int = 1) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in an image using dlib HOG.
        
        Args:
            image: BGR numpy array from cv2
            upsample_num: How many times to upsample the image. 
                          Higher finds smaller faces but is slower.
                          
        Returns:
            List of bounding boxes in format (top, right, bottom, left)
            compatible with face_recognition library.
        """
        # Convert BGR (OpenCV) to RGB (dlib/face_recognition expects)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        # Output is a list of dlib.rectangle objects
        faces = self.detector(rgb_image, upsample_num)
        
        # Convert dlib rectangles to (top, right, bottom, left) tuples
        return [(face.top(), face.right(), face.bottom(), face.left()) for face in faces]

# Singleton instance
detector = FaceDetector()
