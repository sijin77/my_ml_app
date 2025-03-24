import uvicorn
from fastapi import FastAPI
from pydantic_settings import BaseSettings
from services.user_service import UserService


# Инициализация
app = FastAPI()


@app.get("/")
def index():
    user = UserService.create_user(
        user_id=1,
        username="test user",
        email="test@mail.ru",
        password="somepassword123",
        balance=100.0,
    )
    return {"username": user.username, "email": user.email, "balance": user.balance}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
