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

    # If teacher creates course and teacher_ids not provided, assign themselves
    teacher_ids = course.teacher_ids
    if not teacher_ids and current_user.role == UserRole.TEACHER:
        if current_user.teacher_profile:
            teacher_ids = [current_user.teacher_profile.id]

    new_course = Course(
        course_code=course.course_code,
        course_name=course.course_name,
        schedule=course.schedule,
    )
    
    if teacher_ids:
        from models.teacher import Teacher
        res_teachers = await db.execute(select(Teacher).where(Teacher.id.in_(teacher_ids)))
        new_course.teachers = res_teachers.scalars().all()

    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    
    return {
        "id": new_course.id,
        "course_code": new_course.course_code,
        "course_name": new_course.course_name,
        "schedule": new_course.schedule,
        "teacher_ids": [t.id for t in new_course.teachers]
    }

@router.get("/", response_model=CourseList)
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Course).options(selectinload(Course.teachers))
    
    # Filter by teacher if user is a teacher
    if current_user.role == UserRole.TEACHER and current_user.teacher_profile:
        query = query.where(Course.teachers.any(id=current_user.teacher_profile.id))
        
    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    courses = result.scalars().all()

    items = []
    for c in courses:
        items.append({
            "id": c.id,
            "course_code": c.course_code,
            "course_name": c.course_name,
            "schedule": c.schedule,
            "teacher_ids": [t.id for t in c.teachers]
        })

    return {
        "items": items,
        "total": total
    }

@router.get("/{course_id}", response_model=CourseOut)
async def get_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Course).options(selectinload(Course.teachers)).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    return {
        "id": course.id,
        "course_code": course.course_code,
        "course_name": course.course_name,
        "schedule": course.schedule,
        "teacher_ids": [t.id for t in course.teachers]
    }

@router.get("/{course_id}/students", response_model=list[UUID])
async def get_course_students(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Enrollment.student_id).where(Enrollment.course_id == course_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{course_id}/enroll", status_code=status.HTTP_200_OK)
async def enroll_students(
    course_id: UUID,
    request: EnrollmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    from sqlalchemy import delete
    
    # Verify course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Get current enrollments
    stmt = select(Enrollment.student_id).where(Enrollment.course_id == course_id)
    res = await db.execute(stmt)
    current_student_ids = set(res.scalars().all())
    
    requested_student_ids = set(request.student_ids)
    
    # Delete removed students
    to_remove = current_student_ids - requested_student_ids
    if to_remove:
        del_stmt = delete(Enrollment).where(
            Enrollment.course_id == course_id,
            Enrollment.student_id.in_(to_remove)
        )
        await db.execute(del_stmt)
        
    # Add new students
    to_add = requested_student_ids - current_student_ids
    for student_id in to_add:
        enrollment = Enrollment(course_id=course_id, student_id=student_id)
        db.add(enrollment)
            
    await db.commit()
    return {"message": f"Successfully synced enrollments. Added {len(to_add)}, removed {len(to_remove)}."}

@router.put("/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: UUID,
    course_update: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    result = await db.execute(select(Course).options(selectinload(Course.teachers)).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course_update.course_name is not None:
        course.course_name = course_update.course_name
    if course_update.schedule is not None:
        course.schedule = course_update.schedule
    if course_update.teacher_ids is not None:
        from models.teacher import Teacher
        if not course_update.teacher_ids:
            course.teachers = []
        else:
            res_teachers = await db.execute(select(Teacher).where(Teacher.id.in_(course_update.teacher_ids)))
            course.teachers = res_teachers.scalars().all()

    await db.commit()
    await db.refresh(course)
    
    return {
        "id": course.id,
        "course_code": course.course_code,
        "course_name": course.course_name,
        "schedule": course.schedule,
        "teacher_ids": [t.id for t in course.teachers]
    }

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    await db.delete(course)
    await db.commit()
    return None
