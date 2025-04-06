from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, select
from db.models.request_history import RequestHistoryDB
from db.models.user import UserDB
from db.models.mlmodel import MLModelDB
from schemas.request_history import (
    RequestHistoryCreate,
    RequestHistoryRead,
    RequestHistoryUpdate,
    RequestHistoryDetailRead,
)


class RequestHistoryService:
    def __init__(self, db: Session):
        self.db = db

    # --- Основные CRUD операции ---
    async def create_request(
        self, request_data: RequestHistoryCreate
    ) -> RequestHistoryRead:
        """Создание записи о запросе к модели"""
        # Проверяем существование пользователя и модели
        user = await self.db.get(UserDB, request_data.user_id)
        if not user:
            raise ValueError("User not found")
        mlmodel = await self.db.get(MLModelDB, request_data.model_id)
        if not mlmodel:
            raise ValueError("MLModel not found")

        db_request = RequestHistoryDB(**request_data.model_dump())

        self.db.add(db_request)
        await self.db.commit()
        await self.db.refresh(db_request)

        return RequestHistoryRead.model_validate(db_request)

    async def update_request(
        self, request_id: int, update_data: RequestHistoryUpdate
    ) -> Optional[RequestHistoryRead]:
        """Обновление данных запроса"""
        request = await self.db.get(RequestHistoryDB, request_id)
        if not request:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(request, field, value)

        await self.db.commit()
        await self.db.refresh(request)

        return RequestHistoryRead.model_validate(request)

    async def complete_request(
        self,
        request_id: int,
        output_data: str,
        metrics: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        cost: Optional[Decimal] = None,
    ) -> Optional[RequestHistoryRead]:
        """Завершение запроса (установка статуса completed)"""
        completed_request = await self.update_request(
            request_id,
            RequestHistoryUpdate(
                status="completed",
                output_data=output_data,
                output_metrics=metrics,
                execution_time_ms=execution_time_ms,
                cost=cost,
            ),
        )
        return completed_request

    async def fail_request(
        self,
        request_id: int,
        error_message: str,
        execution_time_ms: Optional[int] = None,
    ) -> Optional[RequestHistoryRead]:
        """Помечение запроса как неудачного"""
        failed_request = await self.update_request(
            request_id,
            RequestHistoryUpdate(
                status="failed",
                output_metrics=error_message,
                execution_time_ms=execution_time_ms,
            ),
        )
        return failed_request

    # --- Методы получения данных ---
    async def get_request_by_id(
        self, request_id: int, include_details: bool = False
    ) -> Optional[RequestHistoryRead | RequestHistoryDetailRead]:
        """Получение запроса по ID"""
        request = await self.db.get(RequestHistoryDB, request_id)
        if not request:
            return None

        return self._map_to_read_model(request, include_details)

    async def get_user_requests(
        self, user_id: int, limit: int = 100, include_details: bool = False
    ) -> List[RequestHistoryRead | RequestHistoryDetailRead]:
        """Получение запросов пользователя"""
        stmt = (
            select(RequestHistoryDB)
            .where(RequestHistoryDB.user_id == user_id)
            .order_by(RequestHistoryDB.created_at)
            .limit(limit)
        )
        results = await self.db.execute(stmt)
        requests = results.scalars().all()
        return [self._map_to_read_model(r, include_details) for r in requests]

    async def get_model_requests(
        self, model_id: int, limit: int = 100, include_details: bool = False
    ) -> List[RequestHistoryRead | RequestHistoryDetailRead]:
        """Получение запросов к конкретной модели"""
        stmt = (
            select(RequestHistoryDB)
            .where(RequestHistoryDB.model_id == model_id)
            .order_by(RequestHistoryDB.created_at)
            .limit(limit)
        )
        results = await self.db.execute(stmt)
        requests = results.scalars().all()

        return [self._map_to_read_model(r, include_details) for r in requests]

    async def get_pending_requests(
        self, limit: int = 100, include_details: bool = False
    ) -> List[RequestHistoryRead | RequestHistoryDetailRead]:
        """Получение ожидающих выполнения запросов"""
        stmt = (
            select(RequestHistoryDB)
            .where(RequestHistoryDB.status == "pending")
            .order_by(RequestHistoryDB.created_at)
            .limit(limit)
        )
        results = await self.db.execute(stmt)
        requests = results.scalars().all()

        return [self._map_to_read_model(r, include_details) for r in requests]

    # --- Аналитика ---
    async def get_user_stats(self, user_id: int) -> Dict[str, Decimal]:
        """Получение статистики по запросам пользователя"""
        stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "total_cost": Decimal("0.0"),
            "avg_execution_time": Decimal("0.0"),
        }
        stmt = select(RequestHistoryDB).where(RequestHistoryDB.user_id == user_id)
        result = await self.db.execute(stmt)
        requests = result.scalars().all()
        if not requests:
            return stats

        completed = [r for r in requests if r.status == "completed"]
        stats["total_requests"] = len(requests)
        stats["completed_requests"] = len(completed)
        stats["failed_requests"] = len(requests) - len(completed)

        if completed:
            stats["total_cost"] = sum(r.cost for r in completed if r.cost)
            avg_time = sum(r.execution_time_ms or 0 for r in completed) / len(completed)
            stats["avg_execution_time"] = Decimal(str(avg_time)).quantize(
                Decimal("0.00")
            )

        return stats

    # --- Вспомогательные методы ---
    def _map_to_read_model(
        self, request: RequestHistoryDB, include_details: bool = False
    ) -> RequestHistoryRead | RequestHistoryDetailRead:
        """Преобразование ORM модели в соответствующую DTO"""
        if include_details:
            return RequestHistoryDetailRead.model_validate(request)
        return RequestHistoryRead.model_validate(request)
