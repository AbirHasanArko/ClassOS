"""
ClassOS — Admin Model
Stores administrator profile information.
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, UUIDMixin, TimestampMixin


class Admin(Base, UUIDMixin, TimestampMixin):
    """Administrator profile linked to a User account."""

    __tablename__ = "admins"

    user_id: Mapped["uuid.UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ----- Relationships -----
    user = relationship("User", back_populates="admin_profile")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Admin: {self.full_name}>"
