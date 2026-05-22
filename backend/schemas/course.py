from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class CourseBase(BaseModel):
    course_code: str
    course_name: str
    schedule: Optional[str] = None

class CourseCreate(CourseBase):
    teacher_id: Optional[UUID] = None

class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    schedule: Optional[str] = None
    teacher_id: Optional[UUID] = None

class CourseOut(CourseBase):
    id: UUID
    teacher_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)

class CourseList(BaseModel):
    items: List[CourseOut]
    total: int

class EnrollmentRequest(BaseModel):
    student_ids: List[UUID]
