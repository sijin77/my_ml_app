from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import and_, select
from schemas.user import UserRead
from db.models.user_roles import UserRoleDB
from db.models.user import UserDB
from schemas.user_roles import UserRoleCreate, UserRoleRead, UserRoleUpdate
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import and_, select


class UserRolesService:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def assign_role_to_user(self, role_data: UserRoleCreate) -> UserRoleRead:
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    # Проверка существования пользователя
                    user = await session.get(UserDB, role_data.user_id)
                    if not user:
                        raise ValueError("User not found")

                    # Проверка существующей роли
                    result = await session.execute(
                        select(UserRoleDB)
                        .where(
                            and_(
                                UserRoleDB.user_id == role_data.user_id,
                                UserRoleDB.role == role_data.role,
                            )
                        )
                        .limit(1)
                    )
                    existing_role = result.scalars().first()

                    if existing_role:
                        if not existing_role.is_active:
                            existing_role.is_active = True
                            existing_role.updated_at = datetime.now(timezone.utc)
                            await session.flush()
                            return UserRoleRead.model_validate(existing_role)
                        raise ValueError("Role already assigned to user")

                    # Создание новой роли
                    db_role = UserRoleDB(
                        user_id=role_data.user_id, role=role_data.role, is_active=True
                    )
                    session.add(db_role)
                    await session.flush()
                    return UserRoleRead.model_validate(db_role)
            except Exception:
                await session.rollback()
                raise

    async def update_user_role(
        self, role_id: int, role_data: UserRoleUpdate
    ) -> Optional[UserRoleRead]:
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    role = await session.get(UserRoleDB, role_id)
                    if not role:
                        return None

                    update_data = role_data.model_dump(exclude_unset=True)
                    for field, value in update_data.items():
                        setattr(role, field, value)

                    role.updated_at = datetime.now(timezone.utc)
                    await session.flush()
                    return UserRoleRead.model_validate(role)
            except Exception:
                await session.rollback()
                raise

    async def revoke_user_role(self, role_id: int) -> bool:
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    role = await session.get(UserRoleDB, role_id)
                    if not role:
                        return False

                    role.is_active = False
                    role.updated_at = datetime.now(timezone.utc)
                    await session.flush()
                    return True
            except Exception:
                await session.rollback()
                raise

    async def delete_user_role(self, role_id: int) -> bool:
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    role = await session.get(UserRoleDB, role_id)
                    if not role:
                        return False

                    await session.delete(role)
                    await session.flush()
                    return True
            except Exception:
                await session.rollback()
                raise

    async def get_user_role_by_id(self, role_id: int) -> Optional[UserRoleRead]:
        async with self.async_session_factory() as session:
            role = await session.get(UserRoleDB, role_id)
            if not role:
                return None
            return UserRoleRead.model_validate(role)

    async def get_user_roles(self, user_id: int) -> List[UserRoleRead]:
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(UserRoleDB).where(UserRoleDB.user_id == user_id)
            )
            roles = result.scalars().all()
            return [UserRoleRead.model_validate(role) for role in roles]

    async def get_active_user_roles(self, user_id: int) -> List[UserRoleRead]:
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(UserRoleDB).where(
                    and_(UserRoleDB.user_id == user_id, UserRoleDB.is_active == True)
                )
            )
            roles = result.scalars().all()
            return [UserRoleRead.model_validate(role) for role in roles]

    async def get_users_with_role(self, role: str) -> List[UserRead]:
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(UserDB)
                .join(UserRoleDB)
                .where(and_(UserRoleDB.role == role, UserRoleDB.is_active == True))
            )
            users = result.scalars().all()
            return [UserRead.model_validate(user) for user in users]

    async def has_role(self, user_id: int, role: str) -> bool:
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(UserRoleDB).where(
                    and_(
                        UserRoleDB.user_id == user_id,
                        UserRoleDB.role == role,
                        UserRoleDB.is_active == True,
                    )
                )
            )
            return result.scalars().first() is not None

    async def is_admin(self, user_id: int) -> bool:
        return await self.has_role(user_id, "admin")
