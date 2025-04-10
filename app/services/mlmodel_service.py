from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, select
from db.models.mlmodel import MLModelDB
from schemas.mlmodel import MLModelCreate, MLModelRead, MLModelUpdate, MLModelDetailRead

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import desc, select


class MLModelService:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def create_model(self, model_data: MLModelCreate) -> MLModelRead:
        """Create a new ML model"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    db_model = MLModelDB(**model_data.model_dump())
                    session.add(db_model)
                    await session.flush()
                    await session.refresh(db_model)
                    return MLModelRead.model_validate(db_model)
            except Exception:
                await session.rollback()
                raise

    async def update_model(
        self, model_id: int, update_data: MLModelUpdate
    ) -> Optional[MLModelRead]:
        """Update ML model data"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    model = await session.get(MLModelDB, model_id)
                    if not model:
                        return None

                    update_dict = update_data.model_dump(exclude_unset=True)
                    for field, value in update_dict.items():
                        setattr(model, field, value)

                    model.updated_at = datetime.now(timezone.utc)
                    await session.flush()
                    await session.refresh(model)
                    return MLModelRead.model_validate(model)
            except Exception:
                await session.rollback()
                raise

    async def delete_model(self, model_id: int) -> bool:
        """Delete ML model"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    model = await session.get(MLModelDB, model_id)
                    if not model:
                        return False

                    await session.delete(model)
                    await session.flush()
                    return True
            except Exception:
                await session.rollback()
                raise

    async def get_model_by_id(
        self, model_id: int, include_details: bool = False
    ) -> Optional[MLModelRead | MLModelDetailRead]:
        """Get model by ID"""
        async with self.async_session_factory() as session:
            model = await session.get(MLModelDB, model_id)
            if not model:
                return None

            if include_details:
                await session.refresh(model, ["settings", "request_history"])

            return self._map_to_read_model(model, include_details)

    async def get_all_models(
        self, include_details: bool = False, limit: int = 100
    ) -> List[MLModelRead | MLModelDetailRead]:
        """Get all ML models"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(MLModelDB).order_by(desc(MLModelDB.created_at)).limit(limit)
            )
            models = result.scalars().all()

            if include_details:
                for model in models:
                    await session.refresh(model, ["settings", "request_history"])

            return [self._map_to_read_model(m, include_details) for m in models]

    async def get_models_by_input_type(
        self, input_type: str, include_details: bool = False, limit: int = 100
    ) -> List[MLModelRead | MLModelDetailRead]:
        """Get models by input type"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(MLModelDB)
                .where(MLModelDB.input_type == input_type)
                .order_by(desc(MLModelDB.created_at))
                .limit(limit)
            )
            models = result.scalars().all()

            if include_details:
                for model in models:
                    await session.refresh(model, ["settings", "request_history"])

            return [self._map_to_read_model(m, include_details) for m in models]

    async def get_models_by_output_type(
        self, output_type: str, include_details: bool = False, limit: int = 100
    ) -> List[MLModelRead | MLModelDetailRead]:
        """Get models by output type"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(MLModelDB)
                .where(MLModelDB.output_type == output_type)
                .order_by(desc(MLModelDB.created_at))
                .limit(limit)
            )
            models = result.scalars().all()

            if include_details:
                for model in models:
                    await session.refresh(model, ["settings", "request_history"])

            return [self._map_to_read_model(m, include_details) for m in models]

    async def calculate_cost(
        self, model_id: int, requests_count: int = 1
    ) -> Optional[Decimal]:
        """Calculate cost for given number of requests"""
        async with self.async_session_factory() as session:
            model = await session.get(MLModelDB, model_id)
            if not model:
                return None

            return model.cost_per_request * requests_count

    async def update_model_config(
        self, model_id: int, config_updates: Dict[str, Any]
    ) -> Optional[MLModelRead]:
        """Update model configuration"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    model = await session.get(MLModelDB, model_id)
                    if not model:
                        return None

                    current_config = model.config or {}
                    current_config.update(config_updates)
                    model.config = current_config
                    model.updated_at = datetime.now(timezone.utc)

                    await session.flush()
                    await session.refresh(model)
                    return MLModelRead.model_validate(model)
            except Exception:
                await session.rollback()
                raise

    def _map_to_read_model(
        self, model: MLModelDB, include_details: bool = False
    ) -> MLModelRead | MLModelDetailRead:
        """Convert ORM model to DTO"""
        if include_details:
            return MLModelDetailRead.model_validate(model)
        return MLModelRead.model_validate(model)
