from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, select
from db.models.user_action_history import UserActionHistoryDB, ActionTypeDB
from schemas.user_action_history import (
    UserActionHistoryCreate,
    UserActionHistoryRead,
    UserActionHistoryReadWithUser,
    UserActionHistoryUpdate,
)

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import desc, select


class UserActionHistoryService:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def create_action(
        self, action_data: UserActionHistoryCreate
    ) -> UserActionHistoryRead:
        """Создание записи о действии пользователя"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    db_action = UserActionHistoryDB(**action_data.model_dump())
                    session.add(db_action)
                    await session.flush()
                    await session.refresh(db_action)
                    return UserActionHistoryRead.model_validate(db_action)
            except Exception:
                await session.rollback()
                raise

    async def update_action(
        self, action_id: int, update_data: UserActionHistoryUpdate
    ) -> Optional[UserActionHistoryRead]:
        """Обновление записи о действии"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    action = await session.get(UserActionHistoryDB, action_id)
                    if not action:
                        return None

                    update_dict = update_data.model_dump(exclude_unset=True)
                    for field, value in update_dict.items():
                        setattr(action, field, value)

                    action.updated_at = datetime.now(timezone.utc)
                    await session.flush()
                    await session.refresh(action)
                    return UserActionHistoryRead.model_validate(action)
            except Exception:
                await session.rollback()
                raise

    async def get_action_by_id(
        self, action_id: int, include_user: bool = False
    ) -> Optional[UserActionHistoryRead | UserActionHistoryReadWithUser]:
        """Получение действия по ID"""
        async with self.async_session_factory() as session:
            action = await session.get(UserActionHistoryDB, action_id)
            if not action:
                return None

            if include_user:
                await session.refresh(action, ["user"])

            return self._map_to_read_model(action, include_user)

    async def get_user_actions(
        self, user_id: int, limit: int = 100, include_user: bool = False
    ) -> List[UserActionHistoryRead | UserActionHistoryReadWithUser]:
        """Получение действий пользователя"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(UserActionHistoryDB)
                .where(UserActionHistoryDB.user_id == user_id)
                .order_by(desc(UserActionHistoryDB.created_at))
                .limit(limit)
            )
            actions = result.scalars().all()

            if include_user:
                for action in actions:
                    await session.refresh(action, ["user"])

            return [self._map_to_read_model(action, include_user) for action in actions]

    async def get_recent_actions(
        self,
        action_type: Optional[ActionTypeDB] = None,
        limit: int = 100,
        include_user: bool = False,
    ) -> List[UserActionHistoryRead | UserActionHistoryReadWithUser]:
        """Получение последних действий"""
        async with self.async_session_factory() as session:
            stmt = select(UserActionHistoryDB).order_by(
                desc(UserActionHistoryDB.created_at)
            )

            if action_type:
                stmt = stmt.where(UserActionHistoryDB.action_type == action_type)

            stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            actions = result.scalars().all()

            if include_user:
                for action in actions:
                    await session.refresh(action, ["user"])

            return [self._map_to_read_model(action, include_user) for action in actions]

    def _map_to_read_model(
        self, action: UserActionHistoryDB, include_user: bool = False
    ) -> UserActionHistoryRead | UserActionHistoryReadWithUser:
        """Преобразование ORM модели в соответствующую DTO"""
        if include_user:
            return UserActionHistoryReadWithUser.model_validate(action)
        return UserActionHistoryRead.model_validate(action)

    async def log_action(
        self,
        user_id: int,
        action_type: str,
        status: str = "success",
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> UserActionHistoryRead:
        """Упрощенное логирование действия"""
        return await self.create_action(
            UserActionHistoryCreate(
                user_id=user_id,
                action_type=action_type,
                status=status,
                action_details=details,
                ip_address=ip_address,
            )
        )
