from datetime import datetime
from pathlib import Path
from fastapi import Depends, HTTPException, Response
from services.ml_queue_request_service import MLRequestOrchestratorService
from services.user_roles_service import UserRolesService
from services.user_service import UserService
from services.user_action_history_service import UserActionHistoryService
from services.mlmodel_service import MLModelService
from services.mlmodel_settings_service import MLModelSettingsService
from services.request_history_service import RequestHistoryService
from services.transaction_service import TransactionService
from db.session import AsyncSessionFactory
from services.queue_service import QueueService
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi.templating import Jinja2Templates

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/token"
)  # Укажите ваш эндпоинт для получения токена


def get_response() -> Response:
    # FastAPI автоматически подставит реальный Response
    return Response()


async def get_user_service():
    return UserService(AsyncSessionFactory)


async def get_user_roles_service():
    return UserRolesService(AsyncSessionFactory)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Not authenticated")


async def get_action_history_service():
    return UserActionHistoryService(AsyncSessionFactory)


async def get_mlmodel_service():
    return MLModelService(AsyncSessionFactory)


async def get_mlmodel_settings_service():
    return MLModelSettingsService(AsyncSessionFactory)


async def get_request_history_service():
    return RequestHistoryService(AsyncSessionFactory)


async def get_transaction_service():
    return TransactionService(AsyncSessionFactory)


async def get_queue_service() -> QueueService:
    queue_service = QueueService("amqp://admin:admin@localhost:5672/", "ml_requests")
    await queue_service.connect()  # Устанавливаем соединение при старте
    return queue_service


def get_ml_orchestrator_service(
    request_service: RequestHistoryService = Depends(get_request_history_service),
    queue_service: QueueService = Depends(get_queue_service),
) -> MLRequestOrchestratorService:
    return MLRequestOrchestratorService(request_service, queue_service)


def get_templates():
    BASE_DIR = Path(__file__).resolve().parent.parent
    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    templates.env.filters["datetimeformat"] = lambda value: datetime.fromisoformat(
        value
    ).strftime("%H:%M:%S")
    return templates
