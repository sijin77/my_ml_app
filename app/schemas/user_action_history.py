from enum import Enum
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from db.models.user_action_history import ActionTypeDB

if TYPE_CHECKING:
    from .user import UserRead


# Базовый DTO
class UserActionHistoryBase(BaseModel):
    action_type: ActionTypeDB
    action_details: Optional[str] = None
    status: str = "success"
    ip_address: Optional[str] = None
    user_id: int


# DTO для создания записи
class UserActionHistoryCreate(UserActionHistoryBase):
    pass


# DTO для обновления записи
class UserActionHistoryUpdate(BaseModel):
    action_type: Optional[ActionTypeDB] = None
    action_details: Optional[str] = None
    status: Optional[str] = None
    ip_address: Optional[str] = None


# DTO для чтения (с дополнительными полями)
class UserActionHistoryRead(UserActionHistoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_successful: bool  # Вычисляемое свойство

    model_config = ConfigDict(from_attributes=True)


# DTO с деталями пользователя (если нужно включать связанные данные)
class UserActionHistoryReadWithUser(UserActionHistoryRead):
    user: Optional["UserRead"] = None
