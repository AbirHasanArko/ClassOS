"""
ClassOS — User Model
Central authentication table with role-based access control.
Links to Student, Teacher, or Admin profile via one-to-one relationship.
"""

import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, UUIDMixin, TimestampMixin


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class User(Base, UUIDMixin, TimestampMixin):
    """User authentication model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # ----- Relationships -----
    student_profile = relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    teacher_profile = relationship(
        "Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    admin_profile = relationship(
        "Admin", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
