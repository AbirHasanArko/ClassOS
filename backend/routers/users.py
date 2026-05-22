from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, require_role
from backend.schemas.user import UserCreate, UserOut
from models.user import User, UserRole
from models.teacher import Teacher
from models.admin import Admin
from backend.auth.password import get_password_hash

router = APIRouter()

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        role=request.role
    )
    db.add(new_user)
    await db.flush()

    if request.role == UserRole.TEACHER:
        if not request.employee_id:
            raise HTTPException(status_code=400, detail="Teacher requires employee_id")
        profile = Teacher(
            user_id=new_user.id,
            employee_id=request.employee_id,
            first_name=request.first_name,
            last_name=request.last_name,
            department=request.department
        )
        db.add(profile)
    elif request.role == UserRole.ADMIN:
        profile = Admin(
            user_id=new_user.id,
            first_name=request.first_name,
            last_name=request.last_name
        )
        db.add(profile)

    await db.commit()
    await db.refresh(new_user)
    return new_user
