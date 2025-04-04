from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import JSON, String, ForeignKey, Enum as SQLEnum, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base_model import Base, BaseMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mlmodel_settings import MLModelSettings_DB
    from .request_history import RequestHistory_DB


class ModelInputType_DB(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TABULAR = "tabular"
    AUDIO = "audio"


class ModelOutputType_DB(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    GENERATION = "generation"
    DETECTION = "detection"


class MLModel_DB(Base, BaseMixin):
    repr_cols = ("name", "version", "status")
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Название модели (например, 'GPT-4 Vision')",
    )
    version: Mapped[str] = mapped_column(
        String(20), default="1.0.0", comment="Версия в формате"
    )

    input_type: Mapped[ModelInputType_DB] = mapped_column(
        SQLEnum(ModelInputType_DB), comment="Тип входных данных"
    )
    output_type: Mapped[ModelOutputType_DB] = mapped_column(
        SQLEnum(ModelOutputType_DB), comment="Тип выходных данных"
    )

    cost_per_request: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        default=Decimal("0.001"),
        comment="Стоимость 1 запроса в условных единицах",
    )

    description: Mapped[Optional[str]] = mapped_column(Text, comment="Описание модели")
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default={}, comment="Конфигурация модели в JSON"
    )
    settings: Mapped[List["MLModelSettings_DB"]] = relationship(
        back_populates="mlmodel", cascade="all, delete-orphan", lazy="selectin"
    )
    request_history: Mapped[List["RequestHistory_DB"]] = relationship(
        back_populates="mlmodel",
        lazy="dynamic",
        order_by="desc(RequestHistory_DB.created_at)",
    )

    def calculate_cost(self, requests_count: int) -> Decimal:
        return self.cost_per_request * requests_count

    @staticmethod
    def validate_version(version: str) -> bool:
        parts = version.split(".")
        return len(parts) == 3 and all(p.isdigit() for p in parts)
