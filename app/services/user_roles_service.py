from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from schemas.user import UserRead
from db.models.user_roles import UserRoleDB
from db.models.user import UserDB
from schemas.user_roles import UserRoleCreate, UserRoleRead, UserRoleUpdate


class UserRolesService:
    def __init__(self, db: Session):
        self.db = db

    # --- Основные CRUD операции ---
    async def assign_role_to_user(self, role_data: UserRoleCreate) -> UserRoleRead:
        """Назначение роли пользователю"""
        # Проверяем существует ли пользователь
        user = await self.db.get(UserDB, role_data.user_id)
        if not user:
            raise ValueError("User not found")

        # Проверяем не назначена ли уже такая роль
        stmt = (
            select(UserRoleDB)
            .where(
                and_(
                    UserRoleDB.user_id == role_data.user_id,
                    UserRoleDB.role == role_data.role,
                )
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        existing_role = result.scalars().first()

        if existing_role:
            if not existing_role.is_active:
                existing_role.is_active = True
                existing_role.updated_at = datetime.now(timezone.utc)
                await self.db.commit()
                await self.db.refresh(existing_role)
                return UserRoleRead.model_validate(existing_role)
            raise ValueError("Role already assigned to user")

        # Создаем новую роль
        db_role = UserRoleDB(
            user_id=role_data.user_id, role=role_data.role, is_active=True
        )

        self.db.add(db_role)
        await self.db.commit()
        await self.db.refresh(db_role)

        return UserRoleRead.model_validate(db_role)

    async def update_user_role(
        self, role_id: int, role_data: UserRoleUpdate
    ) -> Optional[UserRoleRead]:
        """Обновление роли пользователя"""
        role = await self.db.get(UserRoleDB, role_id)
        if not role:
            return None

        update_data = role_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(role, field, value)

        role.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(role)

        return UserRoleRead.model_validate(role)

    async def revoke_user_role(self, role_id: int) -> bool:
        """Отзыв роли у пользователя (деактивация)"""
        role = await self.db.get(UserRoleDB, role_id)
        if not role:
            return False

        role.is_active = False
        role.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

        return True

    async def delete_user_role(self, role_id: int) -> bool:
        """Полное удаление роли пользователя"""
        role = await self.db.get(UserRoleDB, role_id)
        if not role:
            return False

        self.db.delete(role)
        await self.db.commit()

        return True

    # --- Методы получения данных ---
    async def get_user_role_by_id(self, role_id: int) -> Optional[UserRoleRead]:
        """Получение роли по ID"""
        role = await self.db.get(UserRoleDB, role_id)

        if not role:
            return None

        return UserRoleRead.model_validate(role)

    async def get_user_roles(self, user_id: int) -> List[UserRoleRead]:
        """Получение всех ролей пользователя"""
        stmt = select(UserRoleDB).where(UserRoleDB.user_id == user_id)
        result = await self.db.execute(stmt)
        roles = result.scalars().all()

        return [UserRoleRead.model_validate(role) for role in roles]

    async def get_active_user_roles(self, user_id: int) -> List[UserRoleRead]:
        """Получение активных ролей пользователя"""
        stmt = select(UserRoleDB).where(
            and_(UserRoleDB.user_id == user_id, UserRoleDB.is_active == True)
        )
        result = await self.db.execute(stmt)
        roles = result.scalars().all()

        return [UserRoleRead.model_validate(role) for role in roles]

    async def get_users_with_role(self, role: str) -> List[UserRead]:
        """Получение всех пользователей с указанной ролью"""
        stmt = (
            select(UserDB)
            .join(UserRoleDB)
            .filter(and_(UserRoleDB.role == role, UserRoleDB.is_active == True))
        )
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        return [UserRead.model_validate(user) for user in users]

    # --- Вспомогательные методы ---
    async def has_role(self, user_id: int, role: str) -> bool:
        """Проверка наличия роли у пользователя"""
        stmt = select(UserRoleDB).where(
            and_(
                UserRoleDB.user_id == user_id,
                UserRoleDB.role == role,
                UserRoleDB.is_active == True,
            )
        )
        result = await self.db.execute(stmt)
        role = result.scalars().first()
        if role:
            return True
        else:
            return False

    def is_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь администратором"""
        return self.has_role(user_id, "admin")
