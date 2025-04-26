from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from passlib.context import CryptContext
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import insert, select
from db.models.user import UserDB
from db.models.user_action_history import UserActionHistoryDB, ActionTypeDB
from schemas.user import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserLogin,
    UserWithToken,
)

# Настройки для хеширования паролей и JWT
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key"  # На практике используйте env переменные
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
from sqlalchemy.ext.asyncio import async_sessionmaker


class UserService:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def register_user(self, user_data: UserCreate) -> UserRead:
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    # Проверка существующего пользователя
                    result = await session.execute(
                        select(UserDB).where(
                            (UserDB.username == user_data.username)
                            | (UserDB.email == user_data.email)
                        )
                    )
                    if result.scalars().first():
                        raise ValueError("User already exists")

                    # Создание нового пользователя
                    hashed_password = self._get_password_hash(user_data.password)
                    db_user = UserDB(
                        username=user_data.username,
                        email=user_data.email,
                        password_hash=hashed_password,
                        balance=user_data.balance,
                        is_active=True,
                    )
                    session.add(db_user)
                    await session.flush()

                    # Логирование действия
                    await session.execute(
                        insert(UserActionHistoryDB).values(
                            user_id=db_user.id,
                            action_type="registration",
                            status="success",
                        )
                    )

                    await session.refresh(db_user)
                    return UserRead.model_validate(db_user)
            except Exception:
                await session.rollback()
                raise

    async def authenticate_user(self, login_data: UserLogin) -> Optional[UserWithToken]:
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(UserDB).where(UserDB.username == login_data.username)
            )
            user = result.scalars().first()

            if not user or not self._verify_password(
                login_data.password, user.password_hash
            ):
                raise ValueError("Неверный логин или пароль")
            access_token = self._create_access_token(user.id)
            user_data = UserRead.model_validate(user)

            # Логирование входа
            await session.execute(
                insert(UserActionHistoryDB).values(
                    user_id=user.id, action_type="login", status="success"
                )
            )
            await session.commit()

            return UserWithToken(
                **user_data.model_dump(), access_token=access_token, token_type="bearer"
            )

    async def get_current_user(self, token: str) -> Optional[UserRead]:
        try:
            # Удаляем 'Bearer ' если есть
            token = token.replace("Bearer ", "").strip()

            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": True},  # Проверка срока действия
            )

            user_id = payload.get("sub")
            if not user_id:
                return None

            async with self.async_session_factory() as session:
                result = await session.execute(
                    select(UserDB).where(UserDB.id == int(user_id))
                )
                user = result.scalars().first()
                return UserRead.model_validate(user) if user else None

        except ExpiredSignatureError:
            print("Token expired")  # Логирование
            return None
        except JWTError as e:
            print(f"JWT Error: {str(e)}")  # Логирование
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")  # Логирование
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[UserRead]:
        async with self.async_session_factory() as session:
            result = await session.execute(select(UserDB).where(UserDB.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return None

            # Явная загрузка связанных данных
            await session.refresh(user, ["roles", "actions_history", "transactions"])
            return UserRead.model_validate(user)

    async def update_user(
        self, user_id: int, update_data: UserUpdate
    ) -> Optional[UserRead]:
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    user = await session.get(UserDB, user_id)
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
                    await session.flush()

                    # Логирование изменения
                    await session.execute(
                        insert(UserActionHistoryDB).values(
                            user_id=user.id,
                            action_type="profile_update",
                            status="success",
                        )
                    )

                    await session.refresh(user)
                    return UserRead.model_validate(user)
            except Exception:
                await session.rollback()
                raise

    async def deactivate_user(self, user_id: int) -> bool:
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    user = await session.get(UserDB, user_id)
                    if not user:
                        return False

                    user.is_active = False
                    user.updated_at = datetime.now(timezone.utc)
                    await session.flush()

                    # Логирование деактивации
                    await session.execute(
                        insert(UserActionHistoryDB).values(
                            user_id=user.id,
                            action_type="deactivation",
                            status="success",
                        )
                    )
                    return True
            except Exception:
                await session.rollback()
                raise

    async def update_balance(self, user_id: int, amount: Decimal) -> Optional[UserRead]:
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    user = await session.get(UserDB, user_id)
                    if not user:
                        return None

                    user.balance += amount
                    user.updated_at = datetime.now(timezone.utc)
                    await session.flush()

                    # Логирование изменения баланса
                    await session.execute(
                        insert(UserActionHistoryDB).values(
                            user_id=user.id,
                            action_type="balance_update",
                            status="success",
                            details=f"Balance changed by {amount}",
                        )
                    )

                    await session.refresh(user)
                    return UserRead.model_validate(user)
            except Exception:
                await session.rollback()
                raise

    # Остальные вспомогательные методы остаются без изменений
    def _get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, user_id: int) -> str:
        to_encode = {"sub": str(user_id)}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
