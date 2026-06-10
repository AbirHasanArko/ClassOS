from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.dependencies import get_db, get_current_user, require_role
from backend.schemas.student import StudentCreate, StudentUpdate, StudentOut, StudentList, StudentAttendanceStatsOut
from models.user import User, UserRole
from models.student import Student
from backend.auth.password import get_password_hash

router = APIRouter()

@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(
    student: StudentCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    # Check if user email exists
    result = await db.execute(select(User).where(User.email == student.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if student ID exists
    result = await db.execute(select(Student).where(Student.student_id == student.student_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Student ID already registered")

    # Create User
    new_user = User(
        email=student.email,
        password_hash=get_password_hash("student123"), # Default password
        role=UserRole.STUDENT
    )
    db.add(new_user)
    await db.flush()

    # Create Student profile
    new_student = Student(
        user_id=new_user.id,
        student_id=student.student_id,
        first_name=student.first_name,
        last_name=student.last_name
    )
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    
    # We need to manually add email from the user object for the schema response since the schema doesn't match DB exactly.
    # A cleaner approach is to use a specific return dict or rely on ORM loading.
    # For now, we return a dict that matches StudentOut schema.
    
    return {
        "id": new_student.id,
        "user_id": new_student.user_id,
        "student_id": new_student.student_id,
        "first_name": new_student.first_name,
        "last_name": new_student.last_name,
        "email": new_user.email,
        "photo_path": new_student.photo_path,
        "face_registered": new_student.face_registered,
        "fingerprint_registered": new_student.fingerprint_registered
    }

@router.get("/", response_model=StudentList)
async def get_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Student).options(selectinload(Student.user))
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Student.first_name.ilike(search_term)) |
            (Student.last_name.ilike(search_term)) |
            (Student.student_id.ilike(search_term))
        )
        
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    students = result.scalars().all()
    
    items = []
    for s in students:
        items.append({
            "id": s.id,
            "user_id": s.user_id,
            "student_id": s.student_id,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "email": s.user.email,
            "photo_path": s.photo_path,
            "face_registered": s.face_registered,
            "fingerprint_registered": s.fingerprint_registered
        })

    return {
        "items": items,
        "total": total,
        "page": skip // limit + 1,
        "size": limit
    }

@router.get("/{student_id}", response_model=StudentOut)
async def get_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Student).options(selectinload(Student.user)).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    return {
        "id": student.id,
        "user_id": student.user_id,
        "student_id": student.student_id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "email": student.user.email,
        "photo_path": student.photo_path,
        "face_registered": student.face_registered,
        "fingerprint_registered": student.fingerprint_registered
    }

@router.put("/{student_id}", response_model=StudentOut)
async def update_student(
    student_id: UUID,
    student_update: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    result = await db.execute(
        select(Student).options(selectinload(Student.user)).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student_update.first_name is not None:
        student.first_name = student_update.first_name
    if student_update.last_name is not None:
        student.last_name = student_update.last_name
    
    if student_update.email is not None and student_update.email != student.user.email:
        # Check if email is already taken
        email_check = await db.execute(select(User).where(User.email == student_update.email))
        if email_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
        student.user.email = student_update.email

    await db.commit()
    await db.refresh(student)
    
    return {
        "id": student.id,
        "user_id": student.user_id,
        "student_id": student.student_id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "email": student.user.email,
        "photo_path": student.photo_path,
        "face_registered": student.face_registered,
        "fingerprint_registered": student.fingerprint_registered
    }

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    # Retrieve student to get user_id
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Delete the user. Because of cascade="all, delete-orphan", this will also delete the student profile.
    user_result = await db.execute(select(User).where(User.id == student.user_id))
    user = user_result.scalar_one_or_none()
    if user:
        await db.delete(user)
        
    await db.commit()
    return None

@router.get("/me/attendance", response_model=StudentAttendanceStatsOut)
async def get_my_attendance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.STUDENT]))
):
    from models.course import Course
    from models.enrollment import Enrollment
    from models.attendance_session import AttendanceSession, SessionStatus
    from models.attendance import Attendance, AttendanceStatus

    student_id = current_user.student_profile.id

    # 1. Get enrolled courses
    stmt = select(Course).join(Enrollment, Course.id == Enrollment.course_id).where(Enrollment.student_id == student_id)
    result = await db.execute(stmt)
    courses = result.scalars().all()

    course_stats = []
    for course in courses:
        # 2. Get total sessions for the course
        sess_stmt = select(func.count()).select_from(AttendanceSession).where(AttendanceSession.course_id == course.id)
        sess_result = await db.execute(sess_stmt)
        total_sessions = sess_result.scalar_one()

        # 3. Get present sessions for this student in this course
        att_stmt = select(func.count()).select_from(Attendance).join(AttendanceSession, Attendance.session_id == AttendanceSession.id).where(
            AttendanceSession.course_id == course.id,
            Attendance.student_id == student_id,
            Attendance.status == AttendanceStatus.PRESENT
        )
        att_result = await db.execute(att_stmt)
        present_sessions = att_result.scalar_one()

        percentage = 0.0
        if total_sessions > 0:
            percentage = (present_sessions / total_sessions) * 100.0

        course_stats.append({
            "course_id": course.id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "total_sessions": total_sessions,
            "present_sessions": present_sessions,
            "attendance_percentage": percentage
        })

    return {
        "student_id": student_id,
        "courses": course_stats
    }

@router.post("/me/courses/{course_id}/enroll", status_code=status.HTTP_200_OK)
async def self_enroll_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.STUDENT]))
):
    from models.course import Course
    from models.enrollment import Enrollment
    from sqlalchemy.exc import IntegrityError

    student_id = current_user.student_profile.id

    # Verify course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    try:
        enrollment = Enrollment(course_id=course_id, student_id=student_id)
        db.add(enrollment)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    return {"message": f"Successfully enrolled in {course.course_code}"}

@router.delete("/me/courses/{course_id}/enroll", status_code=status.HTTP_204_NO_CONTENT)
async def self_unenroll_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.STUDENT]))
):
    from models.enrollment import Enrollment
    from sqlalchemy import delete

    student_id = current_user.student_profile.id

    result = await db.execute(
        delete(Enrollment).where(
            Enrollment.course_id == course_id,
            Enrollment.student_id == student_id
        )
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")
        
    await db.commit()
    return None
