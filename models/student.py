"""
ClassOS — Student Model
Stores student profile info, face/fingerprint registration status,
and relationships to embeddings, fingerprints, enrollments, and attendance.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, UUIDMixin, TimestampMixin


class Student(Base, UUIDMixin, TimestampMixin):
    """Student profile linked to a User account."""

    __tablename__ = "students"

    user_id: Mapped["uuid.UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    student_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False,
        comment="Institutional student ID (e.g., 2024-CS-001)"
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    photo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    face_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fingerprint_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ----- Relationships -----
    user = relationship("User", back_populates="student_profile")
    face_embeddings = relationship(
        "FaceEmbedding", back_populates="student", cascade="all, delete-orphan"
    )
    fingerprint_data = relationship(
        "FingerprintData", back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    enrollments = relationship(
        "Enrollment", back_populates="student", cascade="all, delete-orphan"
    )
    attendance_records = relationship(
        "Attendance", back_populates="student", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Student {self.student_id}: {self.full_name}>"
