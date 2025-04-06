from enum import Enum
from typing import Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base_model import Base, BaseMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from user import UserDB


class ActionTypeDB(str, Enum):
    """Типы действий пользователя"""

    REGISTRATION = "registration"
    LOGIN = "login"
    LOGOUT = "logout"
    PROFILE_UPDATE = "profile_update"
    PASSWORD_CHANGE = "password_change"
    PAYMENT = "payment"
    SYSTEM = "system_action"
    CUSTOM = "custom"


class UserActionHistoryDB(Base, BaseMixin):
    action_type: Mapped[ActionTypeDB] = mapped_column(
        SQLEnum(ActionTypeDB), nullable=False, comment="Тип выполненного действия"
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
        ForeignKey("userdb.id"), nullable=False, comment="ID пользователя"
    )
    user: Mapped["UserDB"] = relationship(
        back_populates="actions_history", lazy="joined"
    )

    @property
    def is_successful(self) -> bool:
        return self.status == "success"
