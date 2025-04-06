from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from passlib.context import CryptContext
from jose import jwt
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import UserDB
from db.models.user_roles import UserRoleDB
from db.models.user_action_history import UserActionHistoryDB, ActionTypeDB
from schemas.user import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserLogin,
    UserWithToken,
    UserDetailRead,
    UserRoleRead,
    UserActionRead,
)

# Настройки для хеширования паролей и JWT
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key"  # На практике используйте env переменные
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Регистрация и аутентификация ---
    async def register_user(self, user_data: UserCreate) -> UserRead:
        """Регистрация нового пользователя"""
        hashed_password = self._get_password_hash(user_data.password)
        db_user = UserDB(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            balance=user_data.balance,
            is_active=True,
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        user_id = db_user.id
        # Создаем    стандартную роль
        # await self._assign_default_role(user_id)
        # Логируем действие
        await self._log_user_action(
            user_id=user_id, action_type="registration", status="success"
        )
        await self.db.refresh(db_user)

        return UserRead.model_validate(db_user)

    async def authenticate_user(self, login_data: UserLogin) -> Optional[UserWithToken]:
        """Аутентификация пользователя"""
        result = await self.db.execute(
            select(UserDB).where(UserDB.username == login_data.username)
        )
        user = result.scalars().first()

        if not user or not self._verify_password(
            login_data.password, user.password_hash
        ):
            return None

        access_token = self._create_access_token(user.id)
        user_data = UserRead.model_validate(user)

        # Логируем действие
        self._log_user_action(user_id=user.id, action_type="login", status="success")

        return UserWithToken(
            **user_data.model_dump(), access_token=access_token, token_type="bearer"
        )

    # --- Управление пользователями ---
    async def get_user_by_id(self, user_id: int) -> Optional[UserRead]:
        """Получение пользователя по ID со всей связанной информацией"""
        user = await self.db.get(UserDB, user_id)
        if not user:
            return None
        await self.db.refresh(
            user, ["roles", "actions_history", "transactions", "request_history"]
        )
        return UserRead.model_validate(user)

    async def update_user(
        self, user_id: int, update_data: UserUpdate
    ) -> Optional[UserRead]:
        """Обновление данных пользователя"""
        user = await self.db.get(UserDB, user_id)
        if not user:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        if "password" in update_dict:
            update_dict["password_hash"] = self._get_password_hash(
                update_dict.pop("password")
            )

        for field, value in update_dict.items():
            setattr(user, field, value)

        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)
        user_id = user.id
        # Логируем действие
        self._log_user_action(
            user_id=user.id, action_type="profile_update", status="success"
        )

        return UserRead.model_validate(user)

    async def deactivate_user(self, user_id: int) -> bool:
        """Деактивация пользователя"""
        user = await self.db.get(UserDB, user_id)
        if not user:
            return False

        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Логируем действие
        self._log_user_action(
            user_id=user.id, action_type="deactivation", status="success"
        )

        return True

    # --- Управление балансом ---
    async def update_balance(self, user_id: int, amount: Decimal) -> Optional[UserRead]:
        """Обновление баланса пользователя"""
        user = await self.db.get(UserDB).get(user_id)
        if not user:
            return None

        user.balance += amount
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)

        # Логируем действие
        self._log_user_action(
            user_id=user.id,
            action_type="balance_update",
            status="success",
            details=f"Balance changed by {amount}",
        )

        return UserRead.model_validate(user)

    # --- Вспомогательные методы ---
    async def _assign_default_role(self, user_id: int):
        """Назначение стандартной роли пользователю"""
        default_role = UserRoleDB(user_id=user_id, role="user", is_active=True)
        self.db.add(default_role)
        await self.db.commit()

    async def _log_user_action(
        self,
        user_id: int,
        action_type: ActionTypeDB,
        status: str,
        details: Optional[str] = None,
    ):
        """Логирование действия пользователя"""
        stmt = insert(UserActionHistoryDB).values(
            user_id=user_id,
            action_type=action_type,
            status=status,
            action_details=details,
        )

        await self.db.execute(stmt)
        await self.db.commit()

    def _get_password_hash(self, password: str) -> str:
        """Генерация хэша пароля"""
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, user_id: int) -> str:
        """Создание JWT токена"""
        to_encode = {"sub": str(user_id)}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
