"""
ClassOS Models Package
Imports all models so they register with SQLAlchemy's metadata.
"""

from models.user import User
from models.student import Student
from models.teacher import Teacher
from models.admin import Admin
from models.course import Course
from models.enrollment import Enrollment
from models.attendance_session import AttendanceSession
from models.attendance import Attendance
from models.face_embedding import FaceEmbedding
from models.fingerprint import FingerprintData

__all__ = [
    "User",
    "Student",
    "Teacher",
    "Admin",
    "Course",
    "Enrollment",
    "AttendanceSession",
    "Attendance",
    "FaceEmbedding",
    "FingerprintData",
]
