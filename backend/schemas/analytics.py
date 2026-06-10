from typing import Dict, List
from pydantic import BaseModel

class AttendanceStats(BaseModel):
    total_students: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_rate: float

class CourseAnalytics(BaseModel):
    course_name: str
    course_code: str
    stats: AttendanceStats

class TrendDataPoint(BaseModel):
    date: str
    rate: float

class TrendData(BaseModel):
    trends: List[TrendDataPoint]

from datetime import datetime
from uuid import UUID

class SessionSummaryOut(BaseModel):
    id: UUID
    course_code: str
    course_name: str
    teacher_name: str
    started_at: datetime
    ended_at: datetime | None
    head_count: int
    recognized_count: int
    status: str

class SessionSummaryList(BaseModel):
    items: List[SessionSummaryOut]
    total: int

class CourseReportStudentOut(BaseModel):
    student_id: str
    first_name: str
    last_name: str
    sessions: Dict[str, str]  # Map of session_date (YYYY-MM-DD) to status (PRESENT/ABSENT/LATE/EXCUSED)
    total_present: int
    total_sessions: int
    attendance_percentage: float
    attendance_score: int

class CourseReportOut(BaseModel):
    course_code: str
    course_name: str
    session_dates: List[str]  # Ordered list of dates
    students: List[CourseReportStudentOut]
