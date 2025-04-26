from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi import Request, Response
from fastapi.security import OAuth2PasswordBearer
from services.dependencies import get_templates
from schemas.user import UserCreate, UserLogin, UserRead, UserWithToken
from services.dependencies import get_user_service
from services.user_service import UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

router = APIRouter(tags=["Secrete"])


# routers.py
@router.post("/signup", response_model=UserRead)
async def register_user(
    user_data: UserCreate, user_service: UserService = Depends(get_user_service)
):
    try:
        return await user_service.register_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/login")
async def show_login_page(request: Request, templates=Depends(get_templates)):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_model=UserWithToken)
async def login(
    form_data: UserLogin,
    user_service: UserService = Depends(get_user_service),
):
    try:
        user = await user_service.authenticate_user(
            UserLogin(username=form_data.username, password=form_data.password)
        )
        response = (Response(content="ok!"),)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {user.token}",  # Предполагаем, что токен есть в user
            httponly=True,
            max_age=3600,  # Время жизни cookie (1 час)
            path="/",
            samesite="lax",
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
