from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
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


from fastapi import Request
from fastapi.templating import Jinja2Templates


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
        # Убедитесь, что ваш UserWithToken содержит token
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
