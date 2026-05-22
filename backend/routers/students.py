from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.dependencies import get_db, get_current_user, require_role
from backend.schemas.student import StudentCreate, StudentUpdate, StudentOut, StudentList
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
