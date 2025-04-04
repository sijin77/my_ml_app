from decimal import Decimal
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User_DB
from schemas.user import UserCreateDTO, UserUpdateDTO
from utils.password import get_password_hash


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreateDTO) -> User_DB:
        hashed_password = get_password_hash(user_data.password)
        user = User_DB(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User_DB | None:
        result = await self.session.execute(
            select(User_DB).where(User_DB.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User_DB | None:
        result = await self.session.execute(
            select(User_DB).where(User_DB.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User_DB | None:
        result = await self.session.execute(
            select(User_DB).where(User_DB.email == email)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User_DB]:
        result = await self.session.execute(select(User_DB).offset(skip).limit(limit))
        return result.scalars().all()

    async def update(self, user_id: int, user_data: UserUpdateDTO) -> User_DB | None:
        update_data = user_data.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(
                update_data.pop("password")
            )

        await self.session.execute(
            update(User_DB).where(User_DB.id == user_id).values(**update_data)
        )
        await self.session.commit()
        return await self.get_by_id(user_id)

    async def delete(self, user_id: int) -> bool:
        await self.session.execute(delete(User_DB).where(User_DB.id == user_id))
        await self.session.commit()
        return True

    async def update_balance(self, user_id: int, amount: Decimal) -> User_DB | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        user.balance += amount
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
