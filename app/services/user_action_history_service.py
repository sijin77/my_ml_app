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


class UserActionHistoryService:
    def __init__(self, db: Session):
        self.db = db

    # --- Основные CRUD операции ---
    async def create_action(
        self, action_data: UserActionHistoryCreate
    ) -> UserActionHistoryRead:
        """Создание записи о действии пользователя"""
        db_action = UserActionHistoryDB(**action_data.model_dump())

        self.db.add(db_action)
        await self.db.commit()
        await self.db.refresh(db_action)

        return UserActionHistoryRead.model_validate(db_action)

    async def update_action(
        self, action_id: int, update_data: UserActionHistoryUpdate
    ) -> Optional[UserActionHistoryRead]:
        """Обновление записи о действии"""
        action = await self.db.get(UserActionHistoryDB, action_id)
        if not action:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(action, field, value)

        action.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(action)

        return UserActionHistoryRead.model_validate(action)

    # --- Методы получения данных ---
    async def get_action_by_id(
        self, action_id: int, include_user: bool = False
    ) -> Optional[UserActionHistoryRead | UserActionHistoryReadWithUser]:
        """Получение действия по ID"""
        action = await self.db.get(UserActionHistoryDB, action_id)
        if not action:
            return None

        return self._map_to_read_model(action, include_user)

    async def get_user_actions(
        self, user_id: int, limit: int = 100, include_user: bool = False
    ) -> List[UserActionHistoryRead | UserActionHistoryReadWithUser]:
        """Получение действий пользователя"""
        smtm = (
            select(UserActionHistoryDB)
            .where(UserActionHistoryDB.user_id == user_id)
            .order_by(desc(UserActionHistoryDB.created_at))
            .limit(limit)
        )
        result = await self.db.execute(smtm)
        actions = result.scalars().all()

        return [self._map_to_read_model(action, include_user) for action in actions]

    async def get_recent_actions(
        self,
        action_type: Optional[ActionTypeDB] = None,
        limit: int = 100,
        include_user: bool = False,
    ) -> List[UserActionHistoryRead | UserActionHistoryReadWithUser]:
        """Получение последних действий (с возможностью фильтрации по типу)"""

        stmt = select(UserActionHistoryDB).order_by(
            desc(UserActionHistoryDB.created_at)
        )
        result = await self.db.execute(stmt)
        query = result.scalars().all()

        if action_type:
            query = query.filter(UserActionHistoryDB.action_type == action_type)

        actions = query.limit(limit).all()
        return [self._map_to_read_model(action, include_user) for action in actions]

    # --- Вспомогательные методы ---
    def _map_to_read_model(
        self, action: UserActionHistoryDB, include_user: bool = False
    ) -> UserActionHistoryRead | UserActionHistoryReadWithUser:
        """Преобразование ORM модели в соответствующую DTO"""
        if include_user:
            return UserActionHistoryReadWithUser.model_validate(action)
        return UserActionHistoryRead.model_validate(action)

    def log_action(
        self,
        user_id: int,
        action_type: str,
        status: str = "success",
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> UserActionHistoryRead:
        """Упрощенное логирование действия"""
        return self.create_action(
            UserActionHistoryCreate(
                user_id=user_id,
                action_type=action_type,
                status=status,
                action_details=details,
                ip_address=ip_address,
            )
        )
