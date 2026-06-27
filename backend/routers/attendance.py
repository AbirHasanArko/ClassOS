from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.dependencies import get_db, get_current_user, require_role
from backend.schemas.attendance import (
    SessionCreate, SessionOut, SessionList, AttendanceOut,
    MarkAttendanceManual, AttendanceRosterItemOut, ModeSwitch, ModeSwitchOut
)
from models.user import User, UserRole
from models.attendance_session import AttendanceSession, SessionStatus
from models.attendance import Attendance, AttendanceStatus, AttendanceMethod
from models.course import Course
from models.enrollment import Enrollment
from attendance_engine.session_manager import session_manager, MODE_ATTENDANCE, MODE_HEADCOUNT

router = APIRouter()


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    """
    Start a new attendance session for a course.

    Optionally specify `mode` ("attendance" or "headcount"); defaults to "attendance".
    If an active ghost session exists for this course, it is auto-completed first.
    """
    # Verify course exists
    result = await db.execute(select(Course).where(Course.id == request.course_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")

    # Auto-complete any existing ghost session for this course
    stmt = select(AttendanceSession).where(
        AttendanceSession.course_id == request.course_id,
        AttendanceSession.status == SessionStatus.ACTIVE
    )
    res = await db.execute(stmt)
    existing_session = res.scalar_one_or_none()

    if existing_session:
        existing_session.status = SessionStatus.COMPLETED
        existing_session.ended_at = datetime.now(timezone.utc)

        # Remove from memory cache
        session_manager.active_sessions.pop(str(existing_session.id), None)

        await db.commit()

    teacher_id = current_user.teacher_profile.id if current_user.teacher_profile else None

    session = AttendanceSession(
        course_id=request.course_id,
        teacher_id=teacher_id,
        status=SessionStatus.ACTIVE,
        mode=request.mode,
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

    # Register in memory cache so the background engine starts
    session_manager.active_sessions[str(session.id)] = {
        "course_id": str(session.course_id),
        "recognized_students": set(),
        "mode": request.mode,
        "latest_head_count": 0,
        "camera_1_available": False,
    }

    await db.commit()

    return session


@router.post("/sessions/{session_id}/end", response_model=SessionOut)
async def end_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    """End an active attendance session. Stops camera and AI pipeline."""
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

    # Remove from memory cache — engine loop will stop cameras automatically
    session_manager.active_sessions.pop(str(session_id), None)

    return session


@router.post("/sessions/{session_id}/mode", response_model=ModeSwitchOut)
async def switch_session_mode(
    session_id: UUID,
    request: ModeSwitch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    """
    Switch the active mode for a running session.

    Modes:
        - "attendance"  → Take Attendance (Camera 0, face recognition)
        - "headcount"   → Verify Head Count (Camera 1, YOLO)

    Switching modes does NOT lose any attendance data. All students already
    marked present remain present across mode switches.
    """
    # Verify session exists and is active
    result = await db.execute(
        select(AttendanceSession).where(AttendanceSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")

    session_id_str = str(session_id)

    # Validate session is tracked in memory
    if session_id_str not in session_manager.active_sessions:
        raise HTTPException(status_code=400, detail="Session is not currently active in engine")

    # Update mode in both memory and DB
    session_manager.set_mode(session_id_str, request.mode)
    session.mode = request.mode

    await db.commit()

    present_count = session_manager.get_recognized_count(session_id_str)
    head_count = session_manager.get_head_count(session_id_str)
    cam1_available = session_manager.is_camera_1_available(session_id_str)

    return ModeSwitchOut(
        session_id=session_id,
        mode=request.mode,
        present_count=present_count,
        head_count=head_count,
        camera_1_available=cam1_available,
    )


@router.post("/sessions/{session_id}/attendance", response_model=AttendanceOut)
async def mark_manual_attendance(
    session_id: UUID,
    request: MarkAttendanceManual,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    """Manually mark a student's attendance for a session."""
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

        # Update in-memory cache
        session_id_str = str(session_id)
        if session_id_str in session_manager.active_sessions:
            session_manager.mark_student_recognized(session_id_str, request.student_id)

    return record


@router.get("/sessions/{session_id}/roster", response_model=list[AttendanceRosterItemOut])
async def get_session_roster(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    """Get the full attendance roster for a session."""
    from models.student import Student

    stmt = (
        select(Attendance, Student)
        .join(Student, Attendance.student_id == Student.id)
        .where(Attendance.session_id == session_id)
        .order_by(Student.last_name, Student.first_name)
    )
    result = await db.execute(stmt)
    records = result.all()

    roster = []
    for att, student in records:
        roster.append({
            "student_uuid": student.id,
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "status": att.status,
            "method": att.method,
            "confidence": att.confidence,
            "marked_at": att.marked_at
        })

    return roster
