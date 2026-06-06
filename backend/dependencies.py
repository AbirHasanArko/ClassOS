"""
ClassOS — Dependency Injection
Provides reusable FastAPI dependencies for database sessions,
authentication, and role-based access control.
"""

from typing import AsyncGenerator, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import async_session_factory


# ----- HTTP Bearer Token Scheme -----
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session.
    Automatically commits on success, rolls back on exception.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials=Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate JWT token from Authorization header and return the current user.
    Raises 401 if token is invalid or user not found.
    """
    from backend.auth.jwt_handler import verify_access_token
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from models.user import User

    token = credentials.credentials
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    # Eagerly load all profile relationships to prevent async lazy-load crashes
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.admin_profile),
            selectinload(User.teacher_profile),
            selectinload(User.student_profile),
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def require_role(allowed_roles: List[str]):
    """
    Factory that creates a dependency requiring the current user
    to have one of the specified roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(["admin"]))])
    """
    async def role_checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {allowed_roles}",
            )
        return current_user
    return role_checker
