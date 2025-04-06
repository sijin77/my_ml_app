from enum import Enum
from decimal import Decimal
from typing import List
from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm import declared_attr


class Base(DeclarativeBase):
    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        """Relationships не используются в repr(), т.к. могут вести к неожиданным подгрузкам"""
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"


class BaseMixin:
    @declared_attr
    def __tablename__(cls):
        # Автоматическое имя таблицы на основе имени класса
        return cls.__name__.lower()

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


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


class UserActionHistoryDB(Base, BaseMixin):
    action_type: Mapped[ActionTypeDB] = mapped_column(
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
        ForeignKey("userdb.id"), nullable=False, comment="ID пользователя"
    )
    user: Mapped["UserDB"] = relationship(
        back_populates="actions_history", lazy="joined"
    )

    @property
    def is_successful(self) -> bool:
        return self.status == "success"


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
        "TransactionDB",
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


class ModelInputTypeDB(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TABULAR = "tabular"
    AUDIO = "audio"


class ModelOutputTypeDB(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    GENERATION = "generation"
    DETECTION = "detection"


class MLModelDB(Base, BaseMixin):
    repr_cols = ("name", "version", "status")
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Название модели (например, 'GPT-4 Vision')",
    )
    version: Mapped[str] = mapped_column(
        String(20), default="1.0.0", comment="Версия в формате"
    )

    input_type: Mapped[ModelInputTypeDB] = mapped_column(
        SQLEnum(ModelInputTypeDB), comment="Тип входных данных"
    )
    output_type: Mapped[ModelOutputTypeDB] = mapped_column(
        SQLEnum(ModelOutputTypeDB), comment="Тип выходных данных"
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
    settings: Mapped[List["MLModelSettingsDB"]] = relationship(
        back_populates="mlmodel", cascade="all, delete-orphan", lazy="selectin"
    )
    request_history: Mapped[List["RequestHistoryDB"]] = relationship(
        back_populates="mlmodel",
        lazy="dynamic",
        order_by="desc(RequestHistoryDB.created_at)",
    )

    def calculate_cost(self, requests_count: int) -> Decimal:
        return self.cost_per_request * requests_count

    @staticmethod
    def validate_version(version: str) -> bool:
        parts = version.split(".")
        return len(parts) == 3 and all(p.isdigit() for p in parts)


class MLModelSettingsDB(Base, BaseMixin):
    repr_cols = ("model_id", "parameter", "parameter_value")

    model_id: Mapped[int] = mapped_column(
        ForeignKey("mlmodeldb.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID связанной модели",
    )

    parameter: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Название параметра"
    )
    parameter_value: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Значение параметра в строковом формате"
    )

    # Связи
    mlmodel: Mapped["MLModelDB"] = relationship(
        back_populates="settings", lazy="joined"
    )
