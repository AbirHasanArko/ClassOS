"""
ClassOS — Database Seed Script
Creates the initial tables and populates them with a default admin user.
"""

import asyncio
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from database.connection import engine
from database.base import Base
import models  # Important: registers all models with Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_db():
    print(f"🌱 Seeding database: {settings.DATABASE_URL}")

    # 1. Create tables
    async with engine.begin() as conn:
        print("Creating tables if they do not exist...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created.")

    # 2. Add default admin user
    from database.connection import async_session_factory
    from models.user import User, UserRole
    from models.admin import Admin

    async with async_session_factory() as session:
        # Check if admin already exists
        result = await session.execute(
            select(User).where(User.email == "admin@classos.local")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("Default admin already exists. Skipping.")
        else:
            print("Creating default admin: admin@classos.local / changeme123")
            admin_user = User(
                email="admin@classos.local",
                password_hash=pwd_context.hash("changeme123"),
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin_user)
            await session.flush()  # To get the ID

            admin_profile = Admin(
                user_id=admin_user.id,
                first_name="System",
                last_name="Administrator"
            )
            session.add(admin_profile)
            await session.commit()
            print("Default admin created successfully.")

    print("✅ Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_db())
