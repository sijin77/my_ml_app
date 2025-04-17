from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import timedelta
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from services.request_history_service import RequestHistoryService
from services.dependencies import (
    get_request_history_service,
    get_user_service,
    get_user_roles_service,
)
from services.user_action_history_service import UserActionHistoryService
from db.models.user import UserDB
from db.session import get_async_db
from services.user_service import UserService
from services.user_roles_service import UserRolesService
from schemas.user_roles import UserRoleCreate, UserRoleRead
from schemas.user import (
    UserRead,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/users/{user_id}/roles", response_model=UserRoleRead)
async def assign_role(
    role_data: UserRoleCreate,
    roles_service: UserRolesService = Depends(get_user_roles_service),
):
    try:
        return await roles_service.assign_role_to_user(role_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}", response_model=UserRead)
async def get_user_info(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    try:
        return await user_service.get_user_by_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/stats", response_model=Dict[str, Decimal])
async def get_user_stats(
    user_id: int,
    request_service: RequestHistoryService = Depends(get_request_history_service),
):
    try:
        return await request_service.get_user_stats(user_id)
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
