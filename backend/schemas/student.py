from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr

class StudentBase(BaseModel):
    student_id: str
    first_name: str
    last_name: str
    email: EmailStr

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None

class StudentOut(StudentBase):
    id: UUID
    user_id: UUID
    photo_path: Optional[str] = None
    face_registered: bool
    fingerprint_registered: bool
    
    model_config = ConfigDict(from_attributes=True)

class StudentList(BaseModel):
    items: List[StudentOut]
    total: int
    page: int
    size: int

class StudentCourseAttendance(BaseModel):
    course_id: UUID
    course_code: str
    course_name: str
    total_sessions: int
    present_sessions: int
    attendance_percentage: float

class StudentAttendanceStatsOut(BaseModel):
    student_id: UUID
    courses: List[StudentCourseAttendance]
