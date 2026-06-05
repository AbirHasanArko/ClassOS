from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class FaceEmbeddingOut(BaseModel):
    """Response schema for a single face embedding sample."""
    id: UUID
    student_id: UUID
    image_path: Optional[str] = None
    sample_number: int

    model_config = ConfigDict(from_attributes=True)


class FaceRegistrationStatus(BaseModel):
    """Summary of a student's face registration state."""
    student_id: UUID
    face_registered: bool
    total_samples: int
    max_samples: int
    samples: List[FaceEmbeddingOut]


class FaceUploadResult(BaseModel):
    """Response after uploading one or more face images."""
    message: str
    samples_added: int
    total_samples: int
    face_registered: bool
