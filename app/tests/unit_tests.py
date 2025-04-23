import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from decimal import Decimal

# Импортируем ваши модули (замените на актуальные пути)
# from pathlib import Path
# import sys

# sys.path.append(str(Path(__file__).parent.parrent))
from schemas.user import UserCreate
from services.dependencies import (
    get_transaction_service,
    get_user_service,
)
from routes.auth_route import router as auth_router
from routes.users_route import router as user_router
from routes.transaction_route import router as transaction_router

# Создаем тестовое приложение
app = FastAPI()
app.include_router(user_router)
app.include_router(transaction_router)
app.include_router(auth_router)

client = TestClient(app)


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
async def test_login_user_success(session, user_service, valid_user_data):
    # Подменяем зависимость в приложении на наш тестовый user_service
    app.dependency_overrides[get_user_service] = lambda: user_service

    # Пытаемся залогиниться с правильными данными
    response = client.post("/login", json=valid_user_data)

    # Проверяем успешный ответ
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == valid_user_data["username"]
    assert response_data["email"] == valid_user_data["email"]
    assert "access_token" in response_data  # Проверяем наличие токена

    # Очищаем подмену зависимостей
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_user_wrong_password(session, user_service, valid_user_data):
    # Подменяем зависимость в приложении на наш тестовый user_service
    app.dependency_overrides[get_user_service] = lambda: user_service

    # Пытаемся залогиниться с неправильным паролем
    wrong_password_data = {
        "username": valid_user_data["username"],
        "password": "wrong_password",
    }
    response = client.post("/login", json=wrong_password_data)

    # Проверяем ошибку аутентификации
    assert response.status_code == 400
    assert "Неверный логин или пароль" in response.json()["detail"]

    # Очищаем подмену зависимостей
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_duplicate_user(user_service, valid_user_data):
    app.dependency_overrides[get_user_service] = lambda: user_service

    # Второй запрос с теми же данными - должен вернуть ошибку
    response2 = client.post("/signup", json=valid_user_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_user_with_invalid_data(user_service):
    app.dependency_overrides[get_user_service] = lambda: user_service

    # Неправильный email
    invalid_data = {
        "username": "user",
        "email": "not-an-email",
        "password": "pass",
        "balance": "100.00",
    }
    response = client.post("/signup", json=invalid_data)
    assert response.status_code in (400, 422)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_balance_deposit(user_service, transaction_service):
    """Тестирование пополнения баланса"""
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_transaction_service] = lambda: transaction_service
    # Создаем тестового пользователя
    user_data = UserCreate(
        username="deposit_user",
        email="deposit@example.com",
        password="securepassword",
        balance=Decimal("50.00"),
    )
    user = await user_service.register_user(user_data)
    # Пополняем баланс
    response = client.post(
        "/transactions/deposit",
        params={  # Отправляем как query-параметры
            "user_id": user.id,
            "amount": 150.50,
            "description": "Test deposit",
        },
    )
    # Проверяем успешный ответ
    assert response.status_code == 200
    # Проверяем обновленный баланс
    updated_user = await user_service.get_user_by_id(user.id)
    assert updated_user.balance == Decimal("200.50")  # 50.00 + 150.50

    # Проверяем создание транзакции
    transactions = await transaction_service.get_user_transactions(user.id)
    assert len(transactions) == 1
    assert transactions[0].amount == Decimal("150.50")
    assert transactions[0].transaction_type == "deposit"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_balance_withdrawal(user_service, transaction_service):
    """Тестирование списания с баланса"""
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_transaction_service] = lambda: transaction_service
    # Создаем тестового пользователя
    user_data = UserCreate(
        username="withdraw_user",
        email="withdraw@example.com",
        password="securepassword",
        balance=Decimal("200.00"),
    )
    user = await user_service.register_user(user_data)

    withdrawal_amount = Decimal("75.25")
    response = client.post(
        "/transactions/withdraw",
        params={
            "user_id": user.id,
            "amount": 75.25,
            "description": "Test withdrawal",
        },
    )
    # Проверяем успешный ответ
    assert response.status_code == 200

    # Проверяем обновленный баланс
    updated_user = await user_service.get_user_by_id(user.id)
    assert updated_user.balance == Decimal("124.75")  # 200.00 - 75.25

    # Проверяем создание транзакции
    transactions = await transaction_service.get_user_transactions(user.id)
    assert len(transactions) == 1
    assert transactions[0].amount == -withdrawal_amount
    assert transactions[0].transaction_type == "withdrawal"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_balance_history(user_service, transaction_service):
    """Тестирование пополнения баланса"""
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_transaction_service] = lambda: transaction_service
    # Создаем тестового пользователя
    user_data = UserCreate(
        username="balance_user",
        email="balance@example.com",
        password="securepassword",
        balance=Decimal("50.00"),
    )
    user = await user_service.register_user(user_data)

    # Пополняем баланс
    response = client.post(
        "/transactions/deposit",
        params={  # Отправляем как query-параметры
            "user_id": user.id,
            "amount": 150.50,
            "description": "Test deposit",
        },
    )
    response = client.post(
        "/transactions/withdraw",
        params={
            "user_id": user.id,
            "amount": 75.25,
            "description": "Test withdrawal",
        },
    )
    # Проверяем успешный ответ
    response = client.post(
        "/users/{user.id}/transactons",
        params={
            "user_id": user.id,
        },
    )
    # Проверяем количество транзакции
    response_t = client.get(f"/users/{user.id}/transactions")

    # Проверяем ответ
    assert response_t.status_code == 200
    transactions = response_t.json()
    assert len(transactions) == 2  # Должно быть 2 транзакции

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_insufficient_balance_withdrawal(user_service, transaction_service):
    """Тестирование попытки списания при недостаточном балансе"""
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_transaction_service] = lambda: transaction_service

    # Создаем тестового пользователя с малым балансом
    user_data = UserCreate(
        username="poor_user",
        email="poor@example.com",
        password="securepassword",
        balance=Decimal("10.00"),
    )
    user = await user_service.register_user(user_data)

    # Пытаемся списать больше, чем есть на балансе
    withdrawal_amount = Decimal("20.00")
    with pytest.raises(ValueError) as excinfo:
        await transaction_service.process_withdrawal(
            user_id=user.id, amount=withdrawal_amount, description="Test withdrawal"
        )
    assert "Insufficient balance" in str(excinfo.value)

    # Проверяем, что баланс не изменился
    updated_user = await user_service.get_user_by_id(user.id)
    assert updated_user.balance == Decimal("10.00")

    # Проверяем, что транзакция не создалась
    transactions = await transaction_service.get_user_transactions(user.id)
    assert len(transactions) == 0
    app.dependency_overrides.clear()
