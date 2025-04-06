from decimal import Decimal
from typing import List
from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base_model import Base, BaseMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .transaction import TransactionDB
    from .request_history import RequestHistoryDB
    from .user_roles import UserRoleDB
    from .user_action_history import UserActionHistoryDB


class UserDB(Base, BaseMixin):
    repr_cols = ("username", "email", "is_active")
    repr_cols_num = 3

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="Уникальное имя пользователя"
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Электронная почта пользователя",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Хэш пароля пользователя"
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), comment="Баланс пользователя"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Флаг активности пользователя"
    )

    # Связи с другими моделями
    transactions: Mapped[List["TransactionDB"]] = relationship(
        back_populates="user",
        lazy="selectin",
        order_by="desc(TransactionDB.created_at)",
    )
    request_history: Mapped[List["RequestHistoryDB"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    roles: Mapped[List["UserRoleDB"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    actions_history: Mapped[list["UserActionHistoryDB"]] = relationship(
        back_populates="user"  # Обратная ссылка
    )
