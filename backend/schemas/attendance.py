from datetime import datetime
from typing import List, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator
from models.attendance_session import SessionStatus
from models.attendance import AttendanceStatus, AttendanceMethod


class SessionCreate(BaseModel):
    course_id: UUID
    mode: Literal["attendance", "headcount"] = "attendance"


class SessionOut(BaseModel):
    id: UUID
    course_id: UUID
    teacher_id: Optional[UUID] = None
    status: SessionStatus
    mode: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    head_count: int
    recognized_count: int

    model_config = ConfigDict(from_attributes=True)


class SessionList(BaseModel):
    items: List[SessionOut]
    total: int


class ModeSwitch(BaseModel):
    """Request body for switching a session's active mode."""
    mode: Literal["attendance", "headcount"]


class ModeSwitchOut(BaseModel):
    """Response after switching mode."""
    session_id: UUID
    mode: str
    present_count: int
    head_count: int
    camera_1_available: bool


class AttendanceOut(BaseModel):
    id: UUID
    session_id: UUID
    student_id: UUID
    status: AttendanceStatus
    method: AttendanceMethod
    confidence: Optional[float] = None
    marked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus
    method: AttendanceMethod = AttendanceMethod.MANUAL


class MarkAttendanceManual(BaseModel):
    student_id: UUID
    status: AttendanceStatus
    method: AttendanceMethod = AttendanceMethod.MANUAL


class AttendanceRosterItemOut(BaseModel):
    student_uuid: UUID
    student_id: str
    first_name: str
    last_name: str
    status: AttendanceStatus
    method: AttendanceMethod
    confidence: Optional[float] = None
    marked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
