from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


# Базовый DTO
class MLModelSettingBase(BaseModel):
    parameter: str
    parameter_value: str


# DTO для создания
class MLModelSettingCreate(MLModelSettingBase):
    model_id: int
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_id": 1,
                "parameter": "temperature",
                "parameter_value": "0.7",
            }
        }
    )


# DTO для обновления
class MLModelSettingUpdate(BaseModel):
    parameter: Optional[str] = None
    parameter_value: Optional[str] = None
    model_config = ConfigDict(json_schema_extra={"example": {"parameter_value": "0.8"}})


# DTO для чтения (с ID и временными метками)
class MLModelSettingRead(MLModelSettingBase):
    id: int
    model_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# DTO для детального просмотра (с связанной моделью)
class MLModelSettingDetailRead(MLModelSettingRead):
    mlmodel: Optional["MLModelRead"] = None


# Референсный DTO для MLModel (должен быть определен в соответствующем модуле)
class MLModelRead(BaseModel):
    id: int
    name: str
    version: str
    model_config = ConfigDict(from_attributes=True)


# Разрешаем рекурсивные типы
MLModelSettingDetailRead.model_rebuild()
