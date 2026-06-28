"""
ClassOS — Course Model
Represents a class/course taught by a teacher.
"""

import uuid

from sqlalchemy import ForeignKey, String, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, UUIDMixin, TimestampMixin


course_teachers = Table(
    "course_teachers",
    Base.metadata,
    Column("course_id", UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
    Column("teacher_id", UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"), primary_key=True),
)
class Course(Base, UUIDMixin, TimestampMixin):
    """A course or class subject."""

    __tablename__ = "courses"

    course_code: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False,
        comment="E.g., CS101"
    )
    course_name: Mapped[str] = mapped_column(String(200), nullable=False)
    schedule: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # ----- Relationships -----
    teachers = relationship("Teacher", secondary=course_teachers, back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    sessions = relationship("AttendanceSession", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Course {self.course_code}: {self.course_name}>"
