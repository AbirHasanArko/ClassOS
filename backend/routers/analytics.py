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

    # Get method breakdown
    from models.attendance import AttendanceMethod
    face_result = await db.execute(select(func.count(Attendance.id)).where(Attendance.method == AttendanceMethod.FACE_RECOGNITION))
    fingerprint_result = await db.execute(select(func.count(Attendance.id)).where(Attendance.method == AttendanceMethod.FINGERPRINT))
    manual_result = await db.execute(select(func.count(Attendance.id)).where(Attendance.method == AttendanceMethod.MANUAL))
    
    from backend.schemas.analytics import MethodBreakdown, WeeklyTrend
    method_breakdown = MethodBreakdown(
        face=face_result.scalar_one(),
        fingerprint=fingerprint_result.scalar_one(),
        manual=manual_result.scalar_one()
    )

    # Get weekly trend (last 5 active days)
    from models.attendance_session import AttendanceSession
    sessions_res = await db.execute(
        select(AttendanceSession.started_at, AttendanceSession.recognized_count, AttendanceSession.head_count)
        .order_by(AttendanceSession.started_at.desc())
        .limit(50)
    )
    sessions = sessions_res.all()
    
    date_stats = {}
    for s in sessions:
        day_name = s.started_at.strftime("%a")
        if day_name not in date_stats:
            date_stats[day_name] = {'rec': 0, 'head': 0, 'date_obj': s.started_at.date()}
        date_stats[day_name]['rec'] += s.recognized_count
        date_stats[day_name]['head'] += s.head_count

    # Sort chronologically and take last 5
    sorted_stats = sorted(date_stats.items(), key=lambda x: x[1]['date_obj'])[-5:]
    
    weekly_trend = []
    for day_name, stats in sorted_stats:
        day_rate = (stats['rec'] / stats['head'] * 100) if stats['head'] > 0 else 0
        weekly_trend.append(WeeklyTrend(date=day_name, rate=round(day_rate, 1)))
        
    if not weekly_trend:
        # Default empty state
        weekly_trend = [WeeklyTrend(date="None", rate=0)]

    return AttendanceStats(
        total_students=total_students,
        present=present,
        absent=absent,
        late=late,
        excused=excused,
        attendance_rate=round(rate, 1),
        weekly_trend=weekly_trend,
        method_breakdown=method_breakdown
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

from backend.schemas.analytics import CourseReportOut, CourseReportStudentOut
from collections import defaultdict

def calculate_attendance_score(percentage: float) -> int:
    if percentage >= 90:
        return 10
    elif percentage >= 85:
        return 9
    elif percentage >= 80:
        return 8
    elif percentage >= 75:
        return 7
    elif percentage >= 70:
        return 6
    elif percentage >= 65:
        return 5
    elif percentage >= 60:
        return 4
    else:
        return 0

@router.get("/courses/{course_id}/report", response_model=CourseReportOut)
async def get_course_report(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    # Verify course exists
    course_res = await db.execute(select(Course).where(Course.id == course_id))
    course = course_res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Get all students enrolled in the course
    from models.student import Student
    enrollment_res = await db.execute(
        select(Student)
        .join(Enrollment, Student.id == Enrollment.student_id)
        .where(Enrollment.course_id == course_id)
    )
    enrolled_students = enrollment_res.scalars().all()

    # Get all completed sessions for the course
    session_res = await db.execute(
        select(AttendanceSession)
        .where(AttendanceSession.course_id == course_id)
        .order_by(AttendanceSession.started_at.asc())
    )
    sessions = session_res.scalars().all()

    session_dates = []
    session_ids = []
    for s in sessions:
        date_str = s.started_at.strftime("%Y-%m-%d")
        # Handle multiple sessions on the same day if necessary, but keep it simple with date format
        if date_str in session_dates:
            date_str = s.started_at.strftime("%Y-%m-%d %H:%M")
        session_dates.append(date_str)
        session_ids.append(s.id)

    # Get all attendance records for these sessions
    att_records = []
    if session_ids:
        att_res = await db.execute(
            select(Attendance)
            .where(Attendance.session_id.in_(session_ids))
        )
        att_records = att_res.scalars().all()

    # Build lookup: (student_id, session_id) -> status
    att_lookup = {}
    for att in att_records:
        att_lookup[(att.student_id, att.session_id)] = att.status.value if hasattr(att.status, 'value') else str(att.status)

    student_reports = []
    total_sessions = len(sessions)

    for student in enrolled_students:
        student_sessions = {}
        total_present = 0
        for i, s_id in enumerate(session_ids):
            date_str = session_dates[i]
            status = att_lookup.get((student.id, s_id), "ABSENT").upper()
            student_sessions[date_str] = status
            if status in ["PRESENT", "LATE"]:
                total_present += 1

        percentage = (total_present / total_sessions * 100) if total_sessions > 0 else 0.0
        score = calculate_attendance_score(percentage)

        student_reports.append(CourseReportStudentOut(
            student_id=student.student_id,
            first_name=student.first_name,
            last_name=student.last_name,
            sessions=student_sessions,
            total_present=total_present,
            total_sessions=total_sessions,
            attendance_percentage=round(percentage, 1),
            attendance_score=score
        ))

    # Sort students by last name, then first name
    student_reports.sort(key=lambda x: (x.last_name.lower(), x.first_name.lower()))

    return CourseReportOut(
        course_code=course.course_code,
        course_name=course.course_name,
        session_dates=session_dates,
        students=student_reports
    )

@router.get("/courses/{course_id}/report/csv")
async def export_course_report_csv(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    report_data = await get_course_report(course_id, db, current_user)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    header = ["Student ID", "First Name", "Last Name"] + report_data.session_dates + ["Total Present", "Total Sessions", "Percentage (%)", "Score"]
    writer.writerow(header)
    
    for student in report_data.students:
        row = [
            student.student_id,
            student.first_name,
            student.last_name
        ]
        # Session statuses
        for date_str in report_data.session_dates:
            row.append(student.sessions.get(date_str, "ABSENT"))
            
        row.extend([
            student.total_present,
            student.total_sessions,
            student.attendance_percentage,
            student.attendance_score
        ])
        writer.writerow(row)
        
    output.seek(0)
    
    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{report_data.course_code}_full_report_{date_str}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

