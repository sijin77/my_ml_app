from typing import List, Optional
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserWithToken, UserRead, UserLogin, UserDetailRead
from schemas.user_roles import UserRoleCreate, UserRoleRead, UserRoleUpdate
from services.dependencies import get_async_db
from services.user_service import UserService
from services.user_roles_service import UserRolesService

router = APIRouter(prefix="/users")


@router.post("/register", response_model=UserRead)
async def register(user_data: UserCreate, db: Session = Depends(get_async_db)):
    return UserService(db).register_user(user_data)


@router.post("/login", response_model=UserWithToken)
async def login(login_data: UserLogin, db: Session = Depends(get_async_db)):
    return UserService(db).authenticate_user(login_data)


@router.get("/{user_id}", response_model=UserDetailRead)
async def get_user(user_id: int, db: Session = Depends(get_async_db)):
    return UserService(db).get_user_by_id(user_id)


"""------router User Roles ------------------------"""
router = APIRouter(prefix="/user-roles")


@router.post("/", response_model=UserRoleRead)
async def assign_role(role_data: UserRoleCreate, db: Session = Depends(get_async_db)):
    try:
        return UserRolesService(db).assign_role_to_user(role_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}", response_model=List[UserRoleRead])
async def get_user_roles(user_id: int, db: Session = Depends(get_async_db)):
    return UserRolesService(db).get_user_roles(user_id)


@router.patch("/{role_id}", response_model=UserRoleRead)
async def update_role(
    role_id: int, role_data: UserRoleUpdate, db: Session = Depends(get_async_db)
):
    result = UserRolesService(db).update_user_role(role_id, role_data)
    if not result:
        raise HTTPException(status_code=404, detail="Role not found")
    return result


"""------router Action History ------------------------"""
from schemas.user_action_history import (
    UserActionHistoryCreate,
    UserActionHistoryRead,
    UserActionHistoryReadWithUser,
)
from services.user_action_history_service import UserActionHistoryService

router = APIRouter(prefix="/user-actions")


@router.post("/", response_model=UserActionHistoryRead)
async def create_action(
    action_data: UserActionHistoryCreate, db: Session = Depends(get_async_db)
):
    return UserActionHistoryService(db).create_action(action_data)


@router.get("/user/{user_id}", response_model=List[UserActionHistoryReadWithUser])
async def get_user_actions(
    user_id: int, limit: int = 100, db: Session = Depends(get_async_db)
):
    return UserActionHistoryService(db).get_user_actions(
        user_id=user_id, limit=limit, include_user=True
    )


@router.get("/recent", response_model=List[UserActionHistoryReadWithUser])
async def get_recent_actions(
    action_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_async_db),
):
    return UserActionHistoryService(db).get_recent_actions(
        action_type=action_type, limit=limit, include_user=True
    )
