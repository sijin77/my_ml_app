from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import ForeignKey, Text, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base_model import Base, BaseMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User_DB
    from .mlmodel import MLModel_DB


class RequestType_DB(str, Enum):
    PREDICTION = "prediction"
    CUSTOM = "custom"


class RequestStatus_DB(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RequestHistory_DB(Base, BaseMixin):

    request_type: Mapped[RequestType_DB] = mapped_column(
        SQLEnum(RequestType_DB), nullable=False, comment="Тип ML-запроса"
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user_db.id"), nullable=False)
    model_id: Mapped[int] = mapped_column(ForeignKey("mlmodel_db.id"), nullable=False)

    # Входные/выходные данные
    input_data: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Входные данные в текстовом формате"
    )
    output_data: Mapped[Optional[str]] = mapped_column(
        Text, comment="Выходные данные в текстовом формате"
    )
    output_metrics: Mapped[Optional[str]] = mapped_column(
        Text, comment="Метрики выполнения"
    )

    # Ресурсы и стоимость
    cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("0.0"), comment="Стоимость в условных единицах"
    )
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        comment="Время выполнения в миллисекундах"
    )

    # Статус
    status: Mapped[RequestStatus_DB] = mapped_column(
        SQLEnum(RequestStatus_DB),
        default=RequestStatus_DB.PENDING,
        comment="Текущий статус выполнения",
    )

    # Связи
    user: Mapped["User_DB"] = relationship(
        back_populates="request_history", lazy="joined"
    )
    mlmodel: Mapped["MLModel_DB"] = relationship(
        back_populates="request_history", lazy="joined"
    )

    def mark_as_failed(self, error_msg: str = ""):
        self.status = RequestStatus_DB.FAILED
        self.output_metrics = error_msg or "Unknown error"
