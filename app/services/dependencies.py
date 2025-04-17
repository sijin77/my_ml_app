from fastapi import Depends
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


async def get_user_service():
    return UserService(AsyncSessionFactory)


async def get_user_roles_service():
    return UserRolesService(AsyncSessionFactory)


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
