from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.dependencies import get_db, get_current_user, require_role
from backend.schemas.course import CourseCreate, CourseUpdate, CourseOut, CourseList, EnrollmentRequest
from models.user import User, UserRole
from models.course import Course
from models.enrollment import Enrollment
from models.student import Student

router = APIRouter()

@router.post("/", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(
    course: CourseCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    # Check if course code exists
    result = await db.execute(select(Course).where(Course.course_code == course.course_code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Course code already exists")

    # If teacher creates course and teacher_id not provided, assign themselves
    teacher_id = course.teacher_id
    if not teacher_id and current_user.role == UserRole.TEACHER:
        if current_user.teacher_profile:
            teacher_id = current_user.teacher_profile.id

    new_course = Course(
        course_code=course.course_code,
        course_name=course.course_name,
        schedule=course.schedule,
        teacher_id=teacher_id
    )
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    return new_course

@router.get("/", response_model=CourseList)
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Course)
    
    # Filter by teacher if user is a teacher
    if current_user.role == UserRole.TEACHER and current_user.teacher_profile:
        query = query.where(Course.teacher_id == current_user.teacher_profile.id)
        
    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    courses = result.scalars().all()

    return {
        "items": courses,
        "total": total
    }

@router.get("/{course_id}", response_model=CourseOut)
async def get_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    return course

@router.post("/{course_id}/enroll", status_code=status.HTTP_200_OK)
async def enroll_students(
    course_id: UUID,
    request: EnrollmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    # Verify course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Enroll students
    enrolled_count = 0
    for student_id in request.student_ids:
        # Check if already enrolled
        stmt = select(Enrollment).where(
            Enrollment.course_id == course_id, 
            Enrollment.student_id == student_id
        )
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            enrollment = Enrollment(course_id=course_id, student_id=student_id)
            db.add(enrollment)
            enrolled_count += 1
            
    await db.commit()
    return {"message": f"Successfully enrolled {enrolled_count} students"}
