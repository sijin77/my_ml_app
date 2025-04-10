from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict
from db.models.transaction import TransactionTypeDB
from schemas.user import UserRead

if TYPE_CHECKING:
    from .user import UserRead


# Базовый DTO
class TransactionBase(BaseModel):
    amount: Decimal
    transaction_type: TransactionTypeDB
    description: Optional[str] = None
    status: str = "pending"
    user_id: int
    related_transaction_id: Optional[int] = None


# DTO для создания транзакции
class TransactionCreate(TransactionBase):
    pass


# DTO для обновления транзакции
class TransactionUpdate(BaseModel):
    amount: Optional[Decimal] = None
    status: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# DTO для чтения транзакции
class TransactionRead(TransactionBase):
    id: int
    created_at: datetime
    is_completed: bool  # Вычисляемое свойство
    model_config = ConfigDict(from_attributes=True)


# DTO для детального просмотра с зависимостями
class TransactionDetailRead(TransactionRead):
    user: Optional["UserRead"] = None
    related_transaction: Optional["TransactionRead"] = None
    child_transactions: List["TransactionRead"] = []
    model_config = ConfigDict(from_attributes=True)


TransactionDetailRead.model_rebuild()
