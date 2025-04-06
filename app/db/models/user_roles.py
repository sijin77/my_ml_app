from enum import Enum
from sqlalchemy import ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base_model import Base, BaseMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import UserDB


class Roles(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    ANALYST = "analyst"
    GUEST = "guest"
    BOT = "bot"
    SUPPORT = "support"


class UserRoleDB(Base, BaseMixin):
    user_id: Mapped[int] = mapped_column(
        ForeignKey("userdb.id"), nullable=False, comment="ID пользователя"
    )
    role: Mapped[Roles] = mapped_column(SQLEnum(Roles), comment="Роль пользователя")
    is_active: Mapped[bool] = mapped_column(default=True)

    # Связи
    user: Mapped["UserDB"] = relationship(back_populates="roles")
