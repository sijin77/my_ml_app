from decimal import Decimal
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import UserDB
from schemas.user import UserCreateDTO, UserUpdateDTO
from utils.password import get_password_hash


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreateDTO) -> UserDB:
        hashed_password = get_password_hash(user_data.password)
        user = UserDB(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> UserDB | None:
        result = await self.session.execute(select(UserDB).where(UserDB.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> UserDB | None:
        result = await self.session.execute(
            select(UserDB).where(UserDB.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserDB | None:
        result = await self.session.execute(select(UserDB).where(UserDB.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[UserDB]:
        result = await self.session.execute(select(UserDB).offset(skip).limit(limit))
        return result.scalars().all()

    async def update(self, user_id: int, user_data: UserUpdateDTO) -> UserDB | None:
        update_data = user_data.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(
                update_data.pop("password")
            )

        await self.session.execute(
            update(UserDB).where(UserDB.id == user_id).values(**update_data)
        )
        await self.session.commit()
        return await self.get_by_id(user_id)

    async def delete(self, user_id: int) -> bool:
        await self.session.execute(delete(UserDB).where(UserDB.id == user_id))
        await self.session.commit()
        return True

    async def update_balance(self, user_id: int, amount: Decimal) -> UserDB | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        user.balance += amount
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
