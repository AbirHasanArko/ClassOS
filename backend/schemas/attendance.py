from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from models.attendance_session import SessionStatus
from models.attendance import AttendanceStatus, AttendanceMethod

class SessionCreate(BaseModel):
    course_id: UUID

class SessionOut(BaseModel):
    id: UUID
    course_id: UUID
    teacher_id: Optional[UUID] = None
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    head_count: int
    recognized_count: int
    
    model_config = ConfigDict(from_attributes=True)

class SessionList(BaseModel):
    items: List[SessionOut]
    total: int

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
