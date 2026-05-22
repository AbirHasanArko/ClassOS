from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.dependencies import get_db, get_current_user, require_role
from backend.schemas.attendance import SessionCreate, SessionOut, SessionList, AttendanceOut, MarkAttendanceManual
from models.user import User, UserRole
from models.attendance_session import AttendanceSession, SessionStatus
from models.attendance import Attendance, AttendanceStatus, AttendanceMethod
from models.course import Course
from models.enrollment import Enrollment

router = APIRouter()

@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    # Verify course exists
    result = await db.execute(select(Course).where(Course.id == request.course_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if active session already exists for this course
    stmt = select(AttendanceSession).where(
        AttendanceSession.course_id == request.course_id,
        AttendanceSession.status == SessionStatus.ACTIVE
    )
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Active session already exists for this course")

    teacher_id = current_user.teacher_profile.id if current_user.teacher_profile else None

    session = AttendanceSession(
        course_id=request.course_id,
        teacher_id=teacher_id,
        status=SessionStatus.ACTIVE,
        started_at=datetime.now(timezone.utc)
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # Initialize attendance records for all enrolled students as ABSENT
    enrollment_stmt = select(Enrollment).where(Enrollment.course_id == request.course_id)
    enrollment_res = await db.execute(enrollment_stmt)
    enrollments = enrollment_res.scalars().all()
    
    for en in enrollments:
        att = Attendance(
            session_id=session.id,
            student_id=en.student_id,
            status=AttendanceStatus.ABSENT,
            method=AttendanceMethod.MANUAL
        )
        db.add(att)
    
    await db.commit()
    return session

@router.post("/sessions/{session_id}/end", response_model=SessionOut)
async def end_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    result = await db.execute(select(AttendanceSession).where(AttendanceSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")
        
    session.status = SessionStatus.COMPLETED
    session.ended_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(session)
    return session

@router.post("/sessions/{session_id}/attendance", response_model=AttendanceOut)
async def mark_manual_attendance(
    session_id: UUID,
    request: MarkAttendanceManual,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    # Get existing record
    stmt = select(Attendance).where(
        Attendance.session_id == session_id,
        Attendance.student_id == request.student_id
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    
    if not record:
        # Create it if student was added to course mid-session
        record = Attendance(
            session_id=session_id,
            student_id=request.student_id,
            status=request.status,
            method=AttendanceMethod.MANUAL
        )
        db.add(record)
    else:
        record.status = request.status
        record.method = AttendanceMethod.MANUAL
        record.marked_at = datetime.now(timezone.utc)
        
    await db.commit()
    await db.refresh(record)
    
    # Update recognized_count if marked present
    if request.status == AttendanceStatus.PRESENT:
        sess_stmt = select(AttendanceSession).where(AttendanceSession.id == session_id)
        sess_res = await db.execute(sess_stmt)
        session = sess_res.scalar_one()
        session.recognized_count += 1
        await db.commit()
        
    return record
