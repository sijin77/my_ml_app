from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import ForeignKey, Text, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base_model import Base, BaseMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import UserDB
    from .mlmodel import MLModelDB


class RequestTypeDB(str, Enum):
    PREDICTION = "prediction"
    CUSTOM = "custom"


class RequestStatusDB(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RequestHistoryDB(Base, BaseMixin):

    request_type: Mapped[RequestTypeDB] = mapped_column(
        SQLEnum(RequestTypeDB), nullable=False, comment="Тип ML-запроса"
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("userdb.id"), nullable=False)
    model_id: Mapped[int] = mapped_column(ForeignKey("mlmodeldb.id"), nullable=False)

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
    status: Mapped[RequestStatusDB] = mapped_column(
        SQLEnum(RequestStatusDB),
        default=RequestStatusDB.PENDING,
        comment="Текущий статус выполнения",
    )

    # Связи
    user: Mapped["UserDB"] = relationship(
        back_populates="request_history", lazy="joined"
    )
    mlmodel: Mapped["MLModelDB"] = relationship(
        back_populates="request_history", lazy="joined"
    )

    def mark_as_failed(self, error_msg: str = ""):
        self.status = RequestStatusDB.FAILED
        self.output_metrics = error_msg or "Unknown error"
