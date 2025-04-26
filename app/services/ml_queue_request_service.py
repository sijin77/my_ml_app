from typing import Optional
from decimal import Decimal
import json
import logging

from services.request_history_service import RequestHistoryService
from services.queue_service import QueueService
from schemas.request_history import RequestHistoryCreate, RequestHistoryRead
from db.models.request_history import RequestStatusDB

logger = logging.getLogger(__name__)


class MLRequestOrchestratorService:
    def __init__(
        self,
        request_service: RequestHistoryService,
        queue_service: QueueService,
    ):
        self.request_service = request_service
        self.queue_service = queue_service

    async def process_prediction_request(
        self,
        user_id: int,
        model_id: int,
        input_data: dict,
        request_type: str = "prediction",
        timeout: int = 30,
    ) -> RequestHistoryRead:
        """
        Основной метод обработки запроса:
        1. Создает запись в БД
        2. Отправляет в очередь
        3. Обрабатывает ответ
        4. Обновляет запись в БД
        """
        # 1. Создаем запись в БД
        db_request = await self._create_db_request(
            user_id, model_id, input_data, request_type
        )

        # 2. Отправляем в очередь
        try:
            response = await self._send_to_queue(input_data)

            # 3. Обрабатываем ответ
            return await self._handle_queue_response(db_request.id, response)

        except Exception as e:
            logger.error(f"Error processing request {db_request.id}: {str(e)}")
            await self._handle_processing_error(db_request.id, str(e))
            raise

    async def _create_db_request(
        self,
        user_id: int,
        model_id: int,
        input_data: dict,
        request_type: str,
    ) -> RequestHistoryRead:
        """Создание записи в БД"""
        return await self.request_service.create_request(
            RequestHistoryCreate(
                user_id=user_id,
                model_id=model_id,
                input_data=input_data,
                request_type=request_type,
                status=RequestStatusDB.PENDING,
            )
        )

    async def _send_to_queue(
        self,
        input_data: str,
    ) -> dict:
        """Отправка запроса в очередь"""
        payload = {
            "text": input_data,
        }
        return await self.queue_service.send_request(payload)

    async def _handle_queue_response(
        self, request_id: int, response: dict
    ) -> RequestHistoryRead:
        """Обработка ответа от очереди"""
        if response.get("success"):
            return await self._handle_success_response(request_id, response)
        return await self._handle_failed_response(
            request_id,
            response.get("error", "Unknown error"),
            response.get("execution_time_ms"),
        )

    async def _handle_success_response(
        self, request_id: int, response: dict
    ) -> RequestHistoryRead:
        """Обработка успешного ответа"""
        return await self.request_service.complete_request(
            request_id=request_id,
            output_data=response.get("output_data"),
            metrics=json.dumps(response.get("metrics", {})),
            execution_time_ms=response.get("execution_time_ms"),
            cost=Decimal(0.01),
        )

    async def _handle_failed_response(
        self,
        request_id: int,
        error_message: str,
        execution_time_ms: Optional[int] = None,
    ) -> RequestHistoryRead:
        """Обработка неудачного ответа"""
        return await self.request_service.fail_request(
            request_id=request_id,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )

    async def _handle_processing_error(
        self, request_id: int, error_message: str
    ) -> RequestHistoryRead:
        """Обработка ошибок при работе с очередью"""
        return await self.request_service.fail_request(
            request_id=request_id,
            error_message=error_message,
        )
