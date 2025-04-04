from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import ForeignKey, Numeric, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base_model import Base, BaseMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User_DB


class TransactionType_DB(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    REFUND = "refund"


class Transaction_DB(Base, BaseMixin):

    repr_cols = ("transaction_type", "amount", "status")
    repr_cols_num = 3

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="Сумма транзакции"
    )
    transaction_type: Mapped[TransactionType_DB] = mapped_column(
        SQLEnum(TransactionType_DB), nullable=False, comment="Тип транзакции"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Описание транзакции"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="Статус транзакции"
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_db.id"), nullable=False, comment="ID пользователя"
    )
    related_transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transaction_db.id"), comment="ID связанной транзакции"
    )

    # Связи с другими моделями
    user: Mapped["User_DB"] = relationship(back_populates="transactions", lazy="joined")
    related_transaction: Mapped[Optional["Transaction_DB"]] = relationship(
        remote_side="transaction_db.id", lazy="selectin"
    )

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    def mark_as_completed(self):
        self.status = "completed"
