import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from decimal import Decimal
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

# Импортируем ваши модули (замените на актуальные пути)
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from services.dependencies import get_user_service
from routes.auth_route import router
from schemas.user import UserCreate, UserRead
from services.user_service import UserService
from db.session import AsyncSessionFactory
from db.base_model import Base
from db.models.user import UserDB as User
from db.models.user_roles import (
    UserRoleDB as UserRole,
)  # Предполагается, что у вас есть эти модели

# Настройка тестовой базы данных (используем SQLite в памяти)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Создаем тестовое приложение
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# Фикстуры для работы с базой данных
@pytest_asyncio.fixture(scope="module")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async_session = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )
    return async_session


@pytest_asyncio.fixture
async def user_service(session):
    return UserService(session)


@pytest.fixture
def valid_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword",
        "balance": "100.00",
    }


# Тесты
@pytest.mark.asyncio
async def test_register_user_success(session, user_service, valid_user_data):
    # Подменяем зависимость в приложении на наш тестовый user_service
    app.dependency_overrides[get_user_service] = lambda: user_service

    # Вызываем endpoint
    response = client.post("/signup", json=valid_user_data)

    # Проверяем ответ
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == valid_user_data["username"]
    assert response_data["email"] == valid_user_data["email"]
    assert Decimal(response_data["balance"]) == Decimal(valid_user_data["balance"])
    assert "id" in response_data

    # Очищаем подмену зависимостей
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_duplicate_user(session, user_service, valid_user_data):
    app.dependency_overrides[get_user_service] = lambda: user_service

    # Первый запрос - должен быть успешным
    response1 = client.post("/signup", json=valid_user_data)
    assert response1.status_code == 200

    # Второй запрос с теми же данными - должен вернуть ошибку
    response2 = client.post("/signup", json=valid_user_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_user_with_invalid_data(session, user_service):
    app.dependency_overrides[get_user_service] = lambda: user_service

    # Неполные данные
    invalid_data = {"username": "user", "password": "pass"}  # Нет email и balance
    response = client.post("/signup", json=invalid_data)
    assert response.status_code == 422  # Ошибка валидации

    # Неправильный email
    invalid_data = {
        "username": "user",
        "email": "not-an-email",
        "password": "pass",
        "balance": "100.00",
    }
    response = client.post("/signup", json=invalid_data)
    assert response.status_code == 400

    app.dependency_overrides.clear()
