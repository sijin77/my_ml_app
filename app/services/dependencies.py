from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import UserService
from db.session import get_async_db


async def get_user_service(db: AsyncSession = Depends(get_async_db)) -> UserService:
    return UserService(db)
