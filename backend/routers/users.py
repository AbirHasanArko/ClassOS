from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, require_role
from backend.schemas.user import UserCreate, UserOut, UserUpdate, UserListOut
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

@router.get("/", response_model=list[UserListOut])
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    from sqlalchemy.orm import selectinload
    query = select(User).options(
        selectinload(User.teacher_profile),
        selectinload(User.admin_profile)
    )
    
    result = await db.execute(query)
    all_users = result.scalars().all()
    
    items = []
    for u in all_users:
        role_str = str(u.role).lower()
        if "admin" not in role_str and "teacher" not in role_str:
            continue
        item = {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "first_name": None,
            "last_name": None,
            "employee_id": None,
            "department": None,
            "profile_id": None
        }
        if "teacher" in role_str and u.teacher_profile:
            item["first_name"] = u.teacher_profile.first_name
            item["last_name"] = u.teacher_profile.last_name
            item["employee_id"] = u.teacher_profile.employee_id
            item["department"] = u.teacher_profile.department
            item["profile_id"] = u.teacher_profile.id
        elif "admin" in role_str and u.admin_profile:
            item["first_name"] = u.admin_profile.first_name
            item["last_name"] = u.admin_profile.last_name
            item["profile_id"] = u.admin_profile.id
            
        items.append(item)
        
    return items

@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User).options(
            selectinload(User.teacher_profile),
            selectinload(User.admin_profile)
        ).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.email is not None and user_update.email != user.email:
        email_check = await db.execute(select(User).where(User.email == user_update.email))
        if email_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = user_update.email

    if user_update.password is not None and user_update.password.strip():
        user.password_hash = get_password_hash(user_update.password)

    if user.role == UserRole.TEACHER and user.teacher_profile:
        if user_update.first_name is not None:
            user.teacher_profile.first_name = user_update.first_name
        if user_update.last_name is not None:
            user.teacher_profile.last_name = user_update.last_name
        if user_update.department is not None:
            user.teacher_profile.department = user_update.department
        if user_update.employee_id is not None:
            user.teacher_profile.employee_id = user_update.employee_id
            
    elif user.role == UserRole.ADMIN and user.admin_profile:
        if user_update.first_name is not None:
            user.admin_profile.first_name = user_update.first_name
        if user_update.last_name is not None:
            user.admin_profile.last_name = user_update.last_name

    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Don't allow an admin to delete themselves
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    await db.delete(user)
    await db.commit()
    return None
