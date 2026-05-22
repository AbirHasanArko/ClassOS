"""
ClassOS — Attendance Record Model
Stores individual student attendance records within a session.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, UUIDMixin, TimestampMixin


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class AttendanceMethod(str, enum.Enum):
    FACE = "face"
    FINGERPRINT = "fingerprint"
    MANUAL = "manual"


class Attendance(Base, UUIDMixin, TimestampMixin):
    """An individual student's attendance record for a session."""

    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_student_attendance"),
    )

    session_id: Mapped["uuid.UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    student_id: Mapped["uuid.UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus), default=AttendanceStatus.PRESENT, nullable=False
    )
    method: Mapped[AttendanceMethod] = mapped_column(
        Enum(AttendanceMethod), nullable=False
    )
    confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="AI confidence score if method is FACE"
    )
    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # ----- Relationships -----
    session = relationship("AttendanceSession", back_populates="attendance_records")
    student = relationship("Student", back_populates="attendance_records")

    def __repr__(self) -> str:
        return f"<Attendance Student:{self.student_id} Status:{self.status.value}>"
