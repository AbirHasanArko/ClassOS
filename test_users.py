import asyncio, sys, os
sys.path.insert(0, os.path.abspath('.'))
from database.session import async_session
from models.user import User, UserRole
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def main():
    async with async_session() as db:
        query = select(User).options(
            selectinload(User.teacher_profile),
            selectinload(User.admin_profile)
        ).where(User.role.in_([UserRole.ADMIN, UserRole.TEACHER]))
        res = await db.execute(query)
        users = res.scalars().all()
        print('Total users:', len(users))

asyncio.run(main())
