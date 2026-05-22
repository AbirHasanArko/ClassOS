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
