from decimal import Decimal
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository
from schemas.user import UserCreateDTO, UserDTO, UserUpdateDTO  # , UserWithRelationsDTO
from utils.password import verify_password


class UserService:
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)

    async def create_user(self, user_data: UserCreateDTO) -> UserDTO:
        if await self.repository.get_by_username(user_data.username):
            raise ValueError("Username already exists")

        if await self.repository.get_by_email(user_data.email):
            raise ValueError("Email already exists")

        user = await self.repository.create(user_data)
        return UserDTO.model_validate(user)

    async def get_user(self, user_id: int) -> Optional[UserDTO]:
        user = await self.repository.get_by_id(user_id)
        return UserDTO.model_validate(user) if user else None

    # async def get_user_with_relations(
    #     self, user_id: int
    # ) -> Optional[UserWithRelationsDTO]:
    #     user = await self.repository.get_by_id(user_id)
    #     return UserWithRelationsDTO.model_validate(user) if user else None

    async def get_users(self, skip: int = 0, limit: int = 100) -> list[UserDTO]:
        users = await self.repository.get_all(skip, limit)
        return [UserDTO.model_validate(user) for user in users]

    async def update_user(
        self, user_id: int, user_data: UserUpdateDTO
    ) -> Optional[UserDTO]:
        if user_data.email:
            existing_user = await self.repository.get_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("Email already in use")

        user = await self.repository.update(user_id, user_data)
        return UserDTO.model_validate(user) if user else None

    async def delete_user(self, user_id: int) -> bool:
        return await self.repository.delete(user_id)

    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[UserDTO]:
        user = await self.repository.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            return None
        return UserDTO.model_validate(user)

    async def update_user_balance(
        self, user_id: int, amount: Decimal
    ) -> Optional[UserDTO]:
        user = await self.repository.update_balance(user_id, amount)
        return UserDTO.model_validate(user) if user else None
