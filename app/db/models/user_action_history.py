from enum import Enum
from typing import Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base_model import Base, BaseMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User_DB


class ActionType_DB(str, Enum):
    """Типы действий пользователя"""

    LOGIN = "login"
    LOGOUT = "logout"
    PROFILE_UPDATE = "profile_update"
    PASSWORD_CHANGE = "password_change"
    PAYMENT = "payment"
    SYSTEM = "system_action"
    CUSTOM = "custom"


class UserActionHistory_DB(Base, BaseMixin):
    action_type: Mapped[ActionType_DB] = mapped_column(
        comment="Тип выполненного действия"
    )

    action_details: Mapped[Optional[str]] = mapped_column(
        Text, comment="Дополнительные детали действия в текстовом формате"
    )

    # Статус выполнения
    status: Mapped[str] = mapped_column(
        String(20), default="success", comment="Статус выполнения (success/failed)"
    )

    # IP и user agent
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), comment="IP-адрес пользователя"
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_db.id"), nullable=False, comment="ID пользователя"
    )
    user: Mapped["User_DB"] = relationship(
        back_populates="actions_history", lazy="joined"
    )

    @property
    def is_successful(self) -> bool:
        return self.status == "success"
