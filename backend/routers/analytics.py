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

from backend.schemas.analytics import SessionSummaryList, SessionSummaryOut
from models.attendance_session import AttendanceSession
from models.teacher import Teacher
from fastapi import Query, HTTPException
from fastapi.responses import StreamingResponse
import io
import csv

@router.get("/sessions", response_model=SessionSummaryList)
async def get_session_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    # Base query for total count
    count_query = select(func.count(AttendanceSession.id))
    
    # Query for the actual data, joined with Course and Teacher
    stmt = (
        select(AttendanceSession, Course, Teacher)
        .join(Course, AttendanceSession.course_id == Course.id)
        .outerjoin(Teacher, AttendanceSession.teacher_id == Teacher.id)
        .order_by(AttendanceSession.started_at.desc())
    )
    
    if current_user.role == UserRole.TEACHER and current_user.teacher_profile:
        # Filter to only show sessions for courses this teacher teaches
        count_query = count_query.join(Course, AttendanceSession.course_id == Course.id).where(Course.teacher_id == current_user.teacher_profile.id)
        stmt = stmt.where(Course.teacher_id == current_user.teacher_profile.id)
        
    total = await db.scalar(count_query)
    
    stmt = stmt.offset(skip).limit(limit)
    res = await db.execute(stmt)
    records = res.all()
    
    items = []
    for session, course, teacher in records:
        teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher else "Unknown"
        items.append(SessionSummaryOut(
            id=session.id,
            course_code=course.course_code,
            course_name=course.course_name,
            teacher_name=teacher_name,
            started_at=session.started_at,
            ended_at=session.ended_at,
            head_count=session.head_count,
            recognized_count=session.recognized_count,
            status=session.status.value if hasattr(session.status, 'value') else str(session.status)
        ))
        
    return SessionSummaryList(items=items, total=total)

@router.get("/sessions/{session_id}/export")
async def export_session_csv(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    # Verify session exists
    session_res = await db.execute(
        select(AttendanceSession, Course)
        .join(Course, AttendanceSession.course_id == Course.id)
        .where(AttendanceSession.id == session_id)
    )
    session_record = session_res.first()
    if not session_record:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session, course = session_record
    
    # Get attendance roster
    from models.student import Student
    stmt = (
        select(Attendance, Student)
        .join(Student, Attendance.student_id == Student.id)
        .where(Attendance.session_id == session_id)
        .order_by(Student.last_name, Student.first_name)
    )
    result = await db.execute(stmt)
    records = result.all()
    
    # Generate CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Student ID", 
        "First Name", 
        "Last Name", 
        "Status", 
        "Method", 
        "Confidence (%)", 
        "Marked At"
    ])
    
    for att, student in records:
        marked_at = att.marked_at.strftime("%Y-%m-%d %H:%M:%S") if att.marked_at else ""
        confidence = f"{(att.confidence * 100):.1f}" if att.confidence else ""
        method = att.method.value if hasattr(att.method, 'value') else str(att.method)
        status = att.status.value if hasattr(att.status, 'value') else str(att.status)
        
        writer.writerow([
            student.student_id,
            student.first_name,
            student.last_name,
            status.upper(),
            method.upper(),
            confidence,
            marked_at
        ])
        
    output.seek(0)
    
    # Return as downloadable file
    date_str = session.started_at.strftime("%Y%m%d")
    filename = f"{course.course_code}_attendance_{date_str}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
