import asyncio
import numpy as np
import face_recognition
from typing import Dict, List, Tuple, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.connection import async_session_factory
from models.face_embedding import FaceEmbedding
from ai_engine.config import ai_config

class FaceRecognizer:
    def __init__(self):
        # In-memory cache of known embeddings
        # Maps student_id (UUID) -> list of 128D numpy arrays
        self.known_embeddings: Dict[UUID, List[np.ndarray]] = {}
        self._is_loaded = False
        
    async def load_embeddings_from_db(self):
        """
        Fetch all face embeddings from PostgreSQL and load into memory.
        Runs on startup or when forced to refresh.
        """
        print("Loading face embeddings from database...")
        self.known_embeddings.clear()
        
        async with async_session_factory() as session:
            result = await session.execute(select(FaceEmbedding))
            embeddings = result.scalars().all()
            
            for emb in embeddings:
                # Convert raw bytes back to numpy array
                vector = np.frombuffer(emb.embedding, dtype=np.float64)
                
                if emb.student_id not in self.known_embeddings:
                    self.known_embeddings[emb.student_id] = []
                self.known_embeddings[emb.student_id].append(vector)
                
        count = sum(len(v) for v in self.known_embeddings.values())
        print(f"Loaded {count} embeddings for {len(self.known_embeddings)} students.")
        self._is_loaded = True

    def _calculate_confidence(self, face_distance: float, face_match_threshold: float = 0.6) -> float:
        """
        Convert Euclidean distance to a percentage confidence score.
        face_recognition uses 0.6 as the default strict cutoff.
        """
        if face_distance > face_match_threshold:
            # Linear decay from 0.6 distance = 50% confidence
            # to 1.0 distance = 0% confidence
            range_val = (1.0 - face_match_threshold)
            linear_val = (1.0 - face_distance) / (range_val * 2.0)
            return max(0.0, linear_val)
        else:
            # Linear curve from 0 distance = 100% confidence
            # to 0.6 distance = 50% confidence
            linear_val = 1.0 - (face_distance / (face_match_threshold * 2.0))
            return linear_val

    def recognize_face(self, unknown_encoding: np.ndarray) -> Tuple[Optional[UUID], float]:
        """
        Compare an unknown encoding against all known embeddings.
        Returns (student_id, confidence) or (None, 0.0) if no match.
        """
        if not self._is_loaded or not self.known_embeddings:
            return None, 0.0

        best_match_id = None
        best_confidence = 0.0
        lowest_distance = 1.0

        for student_id, student_encodings in self.known_embeddings.items():
            # face_distance returns an array of distances for each known encoding
            distances = face_recognition.face_distance(student_encodings, unknown_encoding)
            
            if len(distances) == 0:
                continue
                
            # Use the best matching sample for this student
            min_dist = np.min(distances)
            
            if min_dist < lowest_distance:
                lowest_distance = min_dist
                best_match_id = student_id
                
        confidence = self._calculate_confidence(lowest_distance)
        
        # Only return a match if it meets at least the fingerprint threshold
        if confidence >= ai_config.FACE_CONFIDENCE_FINGERPRINT:
            return best_match_id, confidence
            
        return None, confidence

# Singleton instance
recognizer = FaceRecognizer()
