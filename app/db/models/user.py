from decimal import Decimal
from typing import List
from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base_model import Base, BaseMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .transaction import Transaction_DB
    from .request_history import RequestHistory_DB
    from .user_roles import UserRole_DB
    from .user_action_history import UserActionHistory_DB


class User_DB(Base, BaseMixin):
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

    # Связи с другими моделями
    transactions: Mapped[List["Transaction_DB"]] = relationship(
        back_populates="user",
        lazy="selectin",
        order_by="desc(Transaction_DB.created_at)",
    )
    request_history: Mapped[List["RequestHistory_DB"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    roles: Mapped[List["UserRole_DB"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    actions_history: Mapped[list["UserActionHistory_DB"]] = relationship(
        back_populates="user"  # Обратная ссылка
    )
