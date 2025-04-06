from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, field_validator
from db.models.mlmodel import ModelInputTypeDB, ModelOutputTypeDB

if TYPE_CHECKING:
    from .mlmodel_settings import SettingsRead
    from .request_history import RequestHistoryRead


# Базовый DTO
class MLModelBase(BaseModel):
    name: str
    version: str = "1.0.0"
    input_type: ModelInputTypeDB
    output_type: ModelOutputTypeDB
    cost_per_request: Decimal = Decimal("0.001")
    description: Optional[str] = None
    config: Dict[str, Any] = {}

    @field_validator("version")
    def validate_version(cls, v):
        parts = v.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(
                'Version must be in format "X.Y.Z" where X,Y,Z are numbers'
            )
        return v


# DTO для создания модели
class MLModelCreate(MLModelBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "GPT-4 Vision",
                "version": "1.0.0",
                "input_type": "text",
                "output_type": "generation",
                "cost_per_request": "0.0015",
            }
        }
    )


# DTO для обновления модели
class MLModelUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    cost_per_request: Optional[Decimal] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

    @field_validator("version")
    def validate_version(cls, v):
        if v is not None:
            parts = v.split(".")
            if len(parts) != 3 or not all(p.isdigit() for p in parts):
                raise ValueError('Version must be in format "X.Y.Z"')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cost_per_request": "0.0020",
                "description": "Updated model with new features",
            }
        }
    )


# DTO для чтения (базовый)
class MLModelRead(MLModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# DTO для детального просмотра (со связанными сущностями)
class MLModelDetailRead(MLModelRead):
    settings: List["MLModelSettingRead"] = []
    request_history: List["RequestHistoryRead"] = []
