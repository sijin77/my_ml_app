import uvicorn
from fastapi import FastAPI
from config.app_config import settings
from services.user_service import UserService
from models.transaction import Transaction


# Создаем пользователя
user = UserService.create_user(
    user_id=1,
    username="test user",
    email="test@mail.ru",
    password="somepassword123",
    balance=100.0,
)

# Обновляем баланс
UserService.update_balance(user, 50.0)
print(user.balance)

# Добавляем транзакцию
transaction = Transaction(
    transaction_id=1,
    user_id=1,
    amount=100.0,
    transaction_type="deposit",
    timestamp="2023-10-01",
)
UserService.add_transaction(user, transaction)
print(user.transactions)  # Выведет список транзакций

# Проверяем пароль
is_password_correct = UserService.verify_password(
    "securepassword123", user.password_hash
)
print(is_password_correct)

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
