"""
ClassOS — Teacher Model
Stores teacher profile with department info and course relationships.
"""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, UUIDMixin, TimestampMixin


class Teacher(Base, UUIDMixin, TimestampMixin):
    """Teacher profile linked to a User account."""

    __tablename__ = "teachers"

    user_id: Mapped["uuid.UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False,
        comment="Institutional employee ID"
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # ----- Relationships -----
    user = relationship("User", back_populates="teacher_profile")
    courses = relationship("Course", back_populates="teacher", cascade="all, delete-orphan")
    sessions = relationship(
        "AttendanceSession", back_populates="teacher", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Teacher {self.employee_id}: {self.full_name}>"
