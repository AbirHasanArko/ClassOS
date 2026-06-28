import os
import cv2
import numpy as np
import face_recognition
from typing import Optional, Tuple

# Pillow is already a transitive dependency of face_recognition
try:
    from PIL import Image, ExifTags
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


def _load_exif_corrected(image_path: str) -> np.ndarray:
    """
    Load an image as a numpy RGB array with EXIF orientation applied.

    Phone cameras embed an EXIF orientation tag when shooting in portrait
    mode. face_recognition.load_image_file() (which calls PIL internally)
    does NOT apply that tag on older Pillow builds, so the HOG detector
    receives a sideways or upside-down image and fails to find any face.

    This helper forces the orientation correction before handing the
    pixel data to the face_recognition pipeline.
    """
    if not _PIL_AVAILABLE:
        # Fall back to plain load if Pillow is somehow missing
        return face_recognition.load_image_file(image_path)

    img = Image.open(image_path)

    # Resolve the numeric EXIF orientation tag key
    orientation_key = next(
        (k for k, v in ExifTags.TAGS.items() if v == "Orientation"), None
    )

    try:
        exif = img._getexif()  # returns None for non-JPEG or missing EXIF
    except (AttributeError, Exception):
        exif = None

    if exif and orientation_key and orientation_key in exif:
        orientation = exif[orientation_key]
        # Pillow 9.1+ uses Image.Transpose enum; older builds used direct
        # class-level constants (Image.ROTATE_90 etc.). Support both.
        try:
            _T = Image.Transpose  # Pillow 9.1+
            rotation_map = {
                3: _T.ROTATE_180,
                6: _T.ROTATE_270,
                8: _T.ROTATE_90,
            }
            flip_map = {
                2: _T.FLIP_LEFT_RIGHT,
                4: _T.FLIP_TOP_BOTTOM,
                5: _T.TRANSPOSE,
                7: _T.TRANSVERSE,
            }
        except AttributeError:
            # Pillow <9.1 — use the legacy integer constants directly
            rotation_map = {3: 3, 6: 4, 8: 5}   # PIL constant values for ROTATE_*
            flip_map = {2: 0, 4: 1, 5: 2, 7: 7}

        if orientation in rotation_map:
            img = img.transpose(rotation_map[orientation])
        elif orientation in flip_map:
            img = img.transpose(flip_map[orientation])

    # Ensure the image is in RGB mode (handles RGBA, palette, etc.)
    img = img.convert("RGB")
    return np.array(img)


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

        Strategy for gallery / phone photos:
        1. Apply EXIF orientation correction so portrait-mode images are
           upright before HOG detection.
        2. Try HOG detection at upsample_num=1 (fast, works for most photos).
        3. If 0 faces found, retry at upsample_num=2 (slower but catches
           images where the face occupies a smaller portion of the frame).
        4. Reject if the result is anything other than exactly 1 face.
        """
        if not os.path.exists(image_path):
            return None

        # Load with EXIF correction (critical for mobile phone uploads)
        image = _load_exif_corrected(image_path)

        # --- Attempt 1: standard upsample=1 ---
        face_locations = face_recognition.face_locations(image, model="hog", number_of_times_to_upsample=1)

        # --- Attempt 2: upsample=2 if no face found ---
        if len(face_locations) == 0:
            face_locations = face_recognition.face_locations(image, model="hog", number_of_times_to_upsample=2)

        # For registration we require exactly ONE face
        if len(face_locations) != 1:
            return None

        # Generate 128-D encoding
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
