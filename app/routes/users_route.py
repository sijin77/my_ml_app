from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
from decimal import Decimal
from datetime import timedelta
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from services.dependencies import get_user_service, get_user_roles_service
from services.user_action_history_service import UserActionHistoryService
from db.models.user import UserDB
from db.session import get_async_db
from services.user_service import UserService
from services.user_roles_service import UserRolesService
from schemas.user_roles import UserRoleCreate, UserRoleRead
from schemas.user import (
    UserCreate,
    UserRead,
    UserLogin,
    UserUpdate,
    UserWithToken,
    UserDetailRead,
    UserActionRead,
)

router = APIRouter(prefix="/users", tags=["users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


# routers.py
@router.post("/register", response_model=UserRead)
async def register_user(
    user_data: UserCreate, user_service: UserService = Depends(get_user_service)
):
    try:
        return await user_service.register_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=UserWithToken)
async def login(
    form_data: UserLogin,
    user_service: UserService = Depends(get_user_service),
):
    try:
        return await user_service.authenticate_user(
            UserLogin(username=form_data.username, password=form_data.password)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/roles", response_model=UserRoleRead)
async def assign_role(
    user_id: int,
    role_data: UserRoleCreate,
    roles_service: UserRolesService = Depends(get_user_roles_service),
):
    try:
        return await roles_service.assign_role_to_user(role_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# @router.post("/users/{user_id}/actions/log")
# async def log_user_action(
#     user_id: int,
#     action_type: str,
#     status: str = "success",
#     service: UserActionHistoryService = Depends(get_action_history_service),
# ):
#     return await service.log_action(
#         user_id=user_id, action_type=action_type, status=status
#     )
