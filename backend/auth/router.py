"""
ClassOS — Auth API Router
Endpoints for login, logout, and token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth.jwt_handler import create_access_token, create_refresh_token, verify_refresh_token
from backend.auth.password import verify_password
from backend.auth.schemas import LoginRequest, RefreshRequest, TokenResponse
from backend.dependencies import get_db, get_current_user
from models.user import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    # Find user by email and eager load profiles
    stmt = select(User).options(
        selectinload(User.admin_profile),
        selectinload(User.teacher_profile),
        selectinload(User.student_profile),
    ).where(User.email == request.email)
    
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Extract name based on profile
    name = "User"
    profile_id = None
    if user.admin_profile:
        name = user.admin_profile.full_name
        profile_id = str(user.admin_profile.id)
    elif user.teacher_profile:
        name = user.teacher_profile.full_name
        profile_id = str(user.teacher_profile.id)
    elif user.student_profile:
        name = user.student_profile.full_name
        profile_id = str(user.student_profile.id)

    # Create token payload
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "profile_id": profile_id,
            "email": user.email,
            "role": user.role.value,
            "name": name,
        }
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token."""
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    
    # Load user to ensure they still exist and are active
    stmt = select(User).options(
        selectinload(User.admin_profile),
        selectinload(User.teacher_profile),
        selectinload(User.student_profile),
    ).where(User.id == user_id)
    
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active",
        )

    name = "User"
    profile_id = None
    if user.admin_profile:
        name = user.admin_profile.full_name
        profile_id = str(user.admin_profile.id)
    elif user.teacher_profile:
        name = user.teacher_profile.full_name
        profile_id = str(user.teacher_profile.id)
    elif user.student_profile:
        name = user.student_profile.full_name
        profile_id = str(user.student_profile.id)

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
    }

    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user={
            "id": str(user.id),
            "profile_id": profile_id,
            "email": user.email,
            "role": user.role.value,
            "name": name,
        }
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout endpoint.
    Since JWTs are stateless, the client just discards the token.
    We return 200 OK for consistency.
    """
    return {"message": "Successfully logged out"}
