from decimal import Decimal
from typing import List, Optional, Dict
from db.models.request_history import RequestHistoryDB
from db.models.user import UserDB
from db.models.mlmodel import MLModelDB
from schemas.request_history import (
    RequestHistoryCreate,
    RequestHistoryRead,
    RequestHistoryUpdate,
    RequestHistoryDetailRead,
)

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import desc, select


class RequestHistoryService:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def create_request(
        self, request_data: RequestHistoryCreate
    ) -> RequestHistoryRead:
        """Create a new model request record"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    # Validate user and model exist
                    user = await session.get(UserDB, request_data.user_id)
                    if not user:
                        raise ValueError("User not found")

                    mlmodel = await session.get(MLModelDB, request_data.model_id)
                    if not mlmodel:
                        raise ValueError("MLModel not found")

                    # Create request
                    db_request = RequestHistoryDB(**request_data.model_dump())
                    session.add(db_request)
                    await session.flush()
                    await session.refresh(db_request)
                    return RequestHistoryRead.model_validate(db_request)
            except Exception:
                await session.rollback()
                raise

    async def update_request(
        self, request_id: int, update_data: RequestHistoryUpdate
    ) -> Optional[RequestHistoryRead]:
        """Update request data"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    request = await session.get(RequestHistoryDB, request_id)
                    if not request:
                        return None

                    update_dict = update_data.model_dump(exclude_unset=True)
                    for field, value in update_dict.items():
                        setattr(request, field, value)

                    await session.flush()
                    await session.refresh(request)
                    return RequestHistoryRead.model_validate(request)
            except Exception:
                await session.rollback()
                raise

    async def complete_request(
        self,
        request_id: int,
        output_data: dict,
        metrics: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        cost: Optional[Decimal] = None,
    ) -> Optional[RequestHistoryRead]:
        """Mark request as completed"""
        return await self.update_request(
            request_id,
            RequestHistoryUpdate(
                status="completed",
                output_data=output_data,
                output_metrics=metrics,
                execution_time_ms=execution_time_ms,
                cost=cost,
            ),
        )

    async def fail_request(
        self,
        request_id: int,
        error_message: str,
        execution_time_ms: Optional[int] = None,
    ) -> Optional[RequestHistoryRead]:
        """Mark request as failed"""
        return await self.update_request(
            request_id,
            RequestHistoryUpdate(
                status="failed",
                output_metrics=error_message,
                execution_time_ms=execution_time_ms,
            ),
        )

    async def get_request_by_id(
        self, request_id: int, include_details: bool = False
    ) -> Optional[RequestHistoryRead | RequestHistoryDetailRead]:
        """Get request by ID"""
        async with self.async_session_factory() as session:
            request = await session.get(RequestHistoryDB, request_id)
            if not request:
                return None

            if include_details:
                await session.refresh(request, ["user", "model"])

            return self._map_to_read_model(request, include_details)

    async def get_user_requests(
        self, user_id: int, limit: int = 100, include_details: bool = False
    ) -> List[RequestHistoryRead | RequestHistoryDetailRead]:
        """Get user's requests"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(RequestHistoryDB)
                .where(RequestHistoryDB.user_id == user_id)
                .order_by(desc(RequestHistoryDB.created_at))
                .limit(limit)
            )
            requests = result.scalars().all()

            if include_details:
                for request in requests:
                    await session.refresh(request, ["user", "model"])

            return [self._map_to_read_model(r, include_details) for r in requests]

    async def get_model_requests(
        self, model_id: int, limit: int = 100, include_details: bool = False
    ) -> List[RequestHistoryRead | RequestHistoryDetailRead]:
        """Get requests for specific model"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(RequestHistoryDB)
                .where(RequestHistoryDB.model_id == model_id)
                .order_by(RequestHistoryDB.created_at)
                .limit(limit)
            )
            requests = result.scalars().all()

            if include_details:
                for request in requests:
                    await session.refresh(request, ["user", "model"])

            return [self._map_to_read_model(r, include_details) for r in requests]

    async def get_pending_requests(
        self, limit: int = 100, include_details: bool = False
    ) -> List[RequestHistoryRead | RequestHistoryDetailRead]:
        """Get pending requests"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(RequestHistoryDB)
                .where(RequestHistoryDB.status == "pending")
                .order_by(RequestHistoryDB.created_at)
                .limit(limit)
            )
            requests = result.scalars().all()

            if include_details:
                for request in requests:
                    await session.refresh(request, ["user", "model"])

            return [self._map_to_read_model(r, include_details) for r in requests]

    async def get_user_stats(self, user_id: int) -> Dict[str, Decimal]:
        """Get user request statistics"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(RequestHistoryDB).where(RequestHistoryDB.user_id == user_id)
            )
            requests = result.scalars().all()

            stats = {
                "total_requests": 0,
                "completed_requests": 0,
                "failed_requests": 0,
                "total_cost": Decimal("0.0"),
                "avg_execution_time": Decimal("0.0"),
            }

            if not requests:
                return stats

            completed = [r for r in requests if r.status == "completed"]
            stats["total_requests"] = len(requests)
            stats["completed_requests"] = len(completed)
            stats["failed_requests"] = len(requests) - len(completed)

            if completed:
                stats["total_cost"] = sum(
                    r.cost for r in completed if r.cost is not None
                )
                avg_time = sum(r.execution_time_ms or 0 for r in completed) / len(
                    completed
                )
                stats["avg_execution_time"] = Decimal(str(avg_time)).quantize(
                    Decimal("0.00")
                )

            return stats

    def _map_to_read_model(
        self, request: RequestHistoryDB, include_details: bool = False
    ) -> RequestHistoryRead | RequestHistoryDetailRead:
        """Convert ORM model to DTO"""
        if include_details:
            return RequestHistoryDetailRead.model_validate(request)
        return RequestHistoryRead.model_validate(request)
