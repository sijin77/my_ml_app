from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict
from db.models.request_history import RequestTypeDB, RequestStatusDB

if TYPE_CHECKING:
    from .mlmodel import MLModelRead
    from .user import UserRead


# Базовый DTO
class RequestHistoryBase(BaseModel):
    request_type: RequestTypeDB
    input_data: str
    output_data: Optional[str] = None
    output_metrics: Optional[str] = None
    cost: Decimal = Decimal("0.0")
    execution_time_ms: Optional[int] = None
    status: RequestStatusDB = RequestStatusDB.PENDING


# DTO для создания запроса
class RequestHistoryCreate(RequestHistoryBase):
    user_id: int
    model_id: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_type": "prediction",
                "input_data": "{...}",
                "user_id": 1,
                "model_id": 1,
            }
        }
    )


# DTO для обновления запроса
class RequestHistoryUpdate(BaseModel):
    output_data: Optional[str] = None
    output_metrics: Optional[str] = None
    status: Optional[RequestStatusDB] = None
    cost: Optional[Decimal] = None
    execution_time_ms: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"status": "completed", "output_data": "{...}", "cost": "10.50"}
        }
    )


# DTO для чтения (с ID и временными метками)
class RequestHistoryRead(RequestHistoryBase):
    id: int
    user_id: int
    model_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# DTO для детального просмотра (с связанными объектами)
class RequestHistoryDetailRead(RequestHistoryRead):
    user: Optional["UserRead"] = None
    mlmodel: Optional["MLModelRead"] = None

    model_config = ConfigDict(from_attributes=True)
