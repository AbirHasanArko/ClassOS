import os
import cv2
import numpy as np
import face_recognition
from typing import Optional, Tuple

class EmbeddingGenerator:
    """
    Handles generating 128-dimensional face embeddings from images.
    Used primarily during the student registration phase.
    """
    
    @staticmethod
    def generate_embedding_from_image(image_path: str) -> Optional[np.ndarray]:
        """
        Load an image file, detect faces, and generate an embedding.
        Returns None if no face or multiple faces are found.
        """
        if not os.path.exists(image_path):
            return None
            
        # Load image (face_recognition loads as RGB)
        image = face_recognition.load_image_file(image_path)
        
        # Detect faces
        face_locations = face_recognition.face_locations(image, model="hog")
        
        # For registration, we strictly require exactly ONE face
        if len(face_locations) != 1:
            return None
            
        # Generate 128D encoding
        encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
        
        if not encodings:
            return None
            
        return encodings[0]

    @staticmethod
    def generate_embedding_from_frame(frame: np.ndarray, face_location: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Generate embedding from a live video frame given a specific face location.
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # We pass the pre-computed location so it doesn't have to detect again
        encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=[face_location])
        
        if not encodings:
            return None
            
        return encodings[0]
