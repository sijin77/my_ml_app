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
        back_populates="user_id",
        lazy="selectin",
        order_by="desc(Transaction_DB.created_at)",
    )
    request_history: Mapped[List["RequestHistory_DB"]] = relationship(
        back_populates="user_id", lazy="selectin"
    )
    roles: Mapped[List["UserRoles_DB"]] = relationship(
        back_populates="user_id", lazy="selectin"
    )
    actions_history: Mapped[list["UserActionHistory_DB"]] = relationship(
        back_populates="user_id"  # Обратная ссылка
    )


class Roles(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    ANALYST = "analyst"
    GUEST = "guest"
    BOT = "bot"
    SUPPORT = "support"


class UserRole_DB(Base, BaseMixin):
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_db.id"), nullable=False, comment="ID пользователя"
    )
    role: Mapped[Roles] = mapped_column(SQLEnum(Roles), comment="Роль пользователя")
    is_active: Mapped[bool] = mapped_column(default=True)

    # Связи
    user: Mapped["User_DB"] = relationship(back_populates="roles")


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
    mlmodel: Mapped["MLModels_DB"] = relationship(
        back_populates="request_history", lazy="joined"
    )

    def mark_as_failed(self, error_msg: str = ""):
        self.status = RequestStatus_DB.FAILED
        self.output_metrics = error_msg or "Unknown error"
