"""
ClassOS — Attendance Session Model
Represents a specific occurrence of a class (e.g., today's CS101 lecture).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, UUIDMixin, TimestampMixin


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AttendanceSession(Base, UUIDMixin, TimestampMixin):
    """An attendance gathering session."""

    __tablename__ = "attendance_sessions"

    course_id: Mapped["uuid.UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False
    )
    teacher_id: Mapped["uuid.UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False,
        index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Analytics
    head_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recognized_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ----- Relationships -----
    course = relationship("Course", back_populates="sessions")
    teacher = relationship("Teacher", back_populates="sessions")
    attendance_records = relationship(
        "Attendance", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Session {self.id} Status:{self.status.value}>"
