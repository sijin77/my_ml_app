from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from services.dependencies import get_templates, get_user_service
from services.user_service import UserService
from schemas.user import UserCreate, UserLogin, UserRead, UserWithToken
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter(tags=["Auth"])


@router.post("/signup", response_model=UserRead)
async def register_user(
    user_data: UserCreate, user_service: UserService = Depends(get_user_service)
):
    try:
        return await user_service.register_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/signup")
async def show_register_page(
    request: Request, templates=Depends(get_templates), error: Optional[str] = None
):
    return templates.TemplateResponse(
        "register.html", {"request": request, "error": error}
    )


@router.get("/login")
async def show_login_page(
    request: Request, templates=Depends(get_templates), error: Optional[str] = None
):
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": error}
    )


@router.post("/login", response_model=UserWithToken)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    try:
        user = await user_service.authenticate_user(
            UserLogin(username=form_data.username, password=form_data.password)
        )

        # Устанавливаем cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {user.access_token}",
            httponly=True,
            max_age=3600,
            path="/",
            samesite="lax",
        )

        return user

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "success"}
