from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import ForeignKey, Numeric, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base_model import Base, BaseMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import UserDB


class TransactionTypeDB(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    REFUND = "refund"


class TransactionDB(Base, BaseMixin):

    repr_cols = ("transaction_type", "amount", "status")
    repr_cols_num = 3

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="Сумма транзакции"
    )
    transaction_type: Mapped[TransactionTypeDB] = mapped_column(
        SQLEnum(TransactionTypeDB), nullable=False, comment="Тип транзакции"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Описание транзакции"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="Статус транзакции"
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("userdb.id"), nullable=False, comment="ID пользователя"
    )
    related_transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transactiondb.id"), comment="ID связанной транзакции"
    )

    # Связи с другими моделями
    user: Mapped["UserDB"] = relationship(back_populates="transactions", lazy="joined")
    related_transaction: Mapped[Optional["TransactionDB"]] = relationship(
        remote_side="TransactionDB.id",
        back_populates="child_transactions",
        lazy="selectin",
    )

    child_transactions: Mapped[list["TransactionDB"]] = relationship(
        "TransactionDB", back_populates="related_transaction", lazy="selectin"
    )

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    def mark_as_completed(self):
        self.status = "completed"
