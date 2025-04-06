from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from db.models.user_action_history import ActionTypeDB  # Предполагается, что это есть
from db.models.user_roles import Roles  # Предполагается, что это есть


# Базовые DTO
class UserBase(BaseModel):
    username: str
    email: EmailStr
    balance: Decimal = Decimal("0.00")


# DTO для создания пользователя
class UserCreate(UserBase):
    password: str  # Пароль в открытом виде (для регистрации)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "securepassword123",
                "balance": "100.00",
            }
        }
    )


# DTO для обновления пользователя
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    balance: Optional[Decimal] = None
    password: Optional[str] = None  # Для смены пароля


# DTO для безопасного чтения (без пароля)
class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# DTO для детального просмотра с зависимостями
class UserDetailRead(UserRead):
    roles: List["UserRoleRead"] = []
    actions_history: List["UserActionRead"] = []
    transactions: List["TransactionRead"] = []
    request_history: List["RequestHistoryRead"] = []
    model_config = ConfigDict(from_attributes=True)


# DTO для аутентификации
class UserLogin(BaseModel):
    username: str
    password: str


# DTO для ответа с токеном
class UserWithToken(UserRead):
    access_token: str
    token_type: str = "bearer"


# Вспомогательные DTO (должны быть определены в соответствующих модулях)
class UserRoleRead(BaseModel):
    role: Roles
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class UserActionRead(BaseModel):
    action_type: ActionTypeDB
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TransactionRead(BaseModel):
    amount: Decimal
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RequestHistoryRead(BaseModel):
    endpoint: Optional[str] = None
    method: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
