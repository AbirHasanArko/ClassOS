from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, require_role
from backend.schemas.analytics import AttendanceStats, CourseAnalytics, TrendData, TrendDataPoint
from models.user import User, UserRole
from models.attendance import Attendance, AttendanceStatus
from models.course import Course
from models.enrollment import Enrollment

router = APIRouter()

@router.get("/dashboard/stats", response_model=AttendanceStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    # Dummy logic for dashboard stats - in real app, filter by date range
    total_students_result = await db.execute(select(func.count(Enrollment.id)))
    total_students = total_students_result.scalar_one()

    present_result = await db.execute(select(func.count(Attendance.id)).where(Attendance.status == AttendanceStatus.PRESENT))
    present = present_result.scalar_one()

    absent_result = await db.execute(select(func.count(Attendance.id)).where(Attendance.status == AttendanceStatus.ABSENT))
    absent = absent_result.scalar_one()

    late_result = await db.execute(select(func.count(Attendance.id)).where(Attendance.status == AttendanceStatus.LATE))
    late = late_result.scalar_one()
    
    excused_result = await db.execute(select(func.count(Attendance.id)).where(Attendance.status == AttendanceStatus.EXCUSED))
    excused = excused_result.scalar_one()

    total_records = present + absent + late + excused
    rate = (present / total_records * 100) if total_records > 0 else 0.0

    return AttendanceStats(
        total_students=total_students,
        present=present,
        absent=absent,
        late=late,
        excused=excused,
        attendance_rate=round(rate, 1)
    )
