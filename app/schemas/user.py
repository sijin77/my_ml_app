from typing import Optional, List
from pydantic import field_validator, BaseModel
from datetime import datetime
from decimal import Decimal


class UserCreateDTO(BaseModel):
    username: str
    email: str
    password: str  # Will be hashed before storage

    @field_validator("username")
    def username_length(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        return v


class UserUpdateDTO(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None  # need be hashed before storage
    balance: Optional[Decimal] = None


class UserDTO(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    balance: Decimal
    created_at: datetime
    updated_at: datetime | None


class UserWithPasswordDTO(UserDTO):
    password_hash: str  # Only for internal use


class UserLoginDTO(BaseModel):
    username: str
    password: str


# class UserWithRelationsDTO(UserDTO):
#     transactions: List[TransactionDTO] = []
#     request_history: List[RequestHistoryDTO] = []
#     roles: List[UserRoleDTO] = []
#     actions_history: List[UserActionHistoryDTO] = []
