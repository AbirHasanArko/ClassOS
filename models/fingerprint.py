"""
ClassOS — Fingerprint Data Model
Stores hardware mapping for R307 sensor templates.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, UUIDMixin, TimestampMixin


class FingerprintData(Base, UUIDMixin, TimestampMixin):
    """Mapping of student to R307 fingerprint sensor template ID."""

    __tablename__ = "fingerprint_data"

    student_id: Mapped["uuid.UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    sensor_id: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False,
        comment="Page ID / Template ID stored on the physical R307 sensor"
    )
    is_enrolled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # ----- Relationships -----
    student = relationship("Student", back_populates="fingerprint_data")

    def __repr__(self) -> str:
        return f"<FingerprintData Student:{self.student_id} SensorID:{self.sensor_id}>"
