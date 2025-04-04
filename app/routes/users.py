from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.dependencies import get_user_service
from schemas.user import UserCreateDTO
from services.user_service import UserService
from db.session import get_async_db


router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post(
    "/seed",
    summary="Заполнение тестовыми пользователями",
    response_description="Результат заполнения",
    responses={
        200: {"description": "Пользователи добавлены"},
        500: {"description": "Ошибка сервера"},
    },
)
async def seed_users(service: UserService = Depends(get_user_service)):
    """Добавляет тестовых пользователей в базу данных"""
    test_users = [
        UserCreateDTO(
            username="user1", email="user1@example.com", password="password1"
        ),
        UserCreateDTO(
            username="user2", email="user2@example.com", password="password2"
        ),
        UserCreateDTO(username="admin", email="admin@example.com", password="admin123"),
    ]

    results = []

    for user_data in test_users:
        try:
            # Проверяем существование пользователя
            existing_user = await service.repository.get_by_username(user_data.username)
            if existing_user:
                results.append(
                    {
                        "username": user_data.username,
                        "status": "exists",
                        "message": "Пользователь уже существует",
                    }
                )
                continue

            # Создаем нового пользователя
            created_user = await service.create_user(user_data)
            results.append(
                {
                    "username": user_data.username,
                    "status": "created",
                    "message": "Пользователь создан",
                    "user_id": str(created_user.id),
                }
            )
        except Exception as e:
            results.append(
                {"username": user_data.username, "status": "error", "message": str(e)}
            )
            continue

    return {
        "status": "completed",
        "results": results,
        "total_created": sum(1 for r in results if r["status"] == "created"),
        "total_exists": sum(1 for r in results if r["status"] == "exists"),
        "total_errors": sum(1 for r in results if r["status"] == "error"),
    }
