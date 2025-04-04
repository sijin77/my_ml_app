import asyncio
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.user import UserCreateDTO
from services.user_service import UserService
from db.session import get_async_db


async def seed_users():
    # Список тестовых пользователей
    test_users = [
        UserCreateDTO(
            username="user1", email="user1@example.com", password="password1"
        ),
        UserCreateDTO(
            username="user2", email="user2@example.com", password="password2"
        ),
        UserCreateDTO(username="admin", email="admin@example.com", password="admin123"),
    ]

    async def get_service():
        async for session in get_async_db():
            yield UserService(session)

    async for service in get_service():
        for user_data in test_users:
            try:
                # Проверяем, существует ли пользователь
                if not await service.repository.get_by_username(user_data.username):
                    await service.create_user(user_data)
                    print(f"User {user_data.username} created")
                else:
                    print(f"User {user_data.username} already exists")
            except Exception as e:
                print(f"Error creating {user_data.username}: {str(e)}")
