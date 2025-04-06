from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, select
from db.models.mlmodel import MLModelDB
from schemas.mlmodel import MLModelCreate, MLModelRead, MLModelUpdate, MLModelDetailRead


class MLModelService:
    def __init__(self, db: Session):
        self.db = db

    # --- Основные CRUD операции ---
    async def create_model(self, model_data: MLModelCreate) -> MLModelRead:
        """Создание новой ML-модели"""
        db_model = MLModelDB(**model_data.model_dump())

        self.db.add(db_model)
        await self.db.commit()
        await self.db.refresh(db_model)

        return MLModelRead.model_validate(db_model)

    async def update_model(
        self, model_id: int, update_data: MLModelUpdate
    ) -> Optional[MLModelRead]:
        """Обновление данных ML-модели"""
        model = self.db.get(MLModelDB, model_id)
        if not model:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(model, field, value)

        model.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(model)

        return MLModelRead.model_validate(model)

    async def delete_model(self, model_id: int) -> bool:
        """Удаление ML-модели"""
        model = self.db.get(MLModelDB, model_id)
        if not model:
            return False

        self.db.delete(model)
        await self.db.commit()
        return True

    # --- Методы получения данных ---
    async def get_model_by_id(
        self, model_id: int, include_details: bool = False
    ) -> Optional[MLModelRead | MLModelDetailRead]:
        """Получение модели по ID"""
        model = self.db.get(MLModelDB, model_id)
        if not model:
            return None

        return self._map_to_read_model(model, include_details)

    async def get_all_models(
        self, include_details: bool = False, limit: int = 100
    ) -> List[MLModelRead | MLModelDetailRead]:
        """Получение всех ML-моделей"""
        result = await self.db.execute(
            select(MLModelDB).order_by(desc(MLModelDB.created_at)).limit(limit)
        )
        models = result.scalars().all()
        return [await self._map_to_read_model(m, include_details) for m in models]

    async def get_models_by_input_type(
        self, input_type: str, include_details: bool = False, limit: int = 100
    ) -> List[MLModelRead | MLModelDetailRead]:
        """Получение моделей по типу ввода"""
        result = await self.db.execute(
            select(MLModelDB)
            .where(MLModelDB.input_type == input_type)
            .order_by(desc(MLModelDB.created_at))
            .limit(limit)
        )
        models = result.scalars().all()
        # Маппим результаты в схемы
        return [await self._map_to_read_model(m, include_details) for m in models]

    def get_models_by_output_type(
        self, output_type: str, include_details: bool = False, limit: int = 100
    ) -> List[MLModelRead | MLModelDetailRead]:
        """Получение моделей по типу вывода"""
        models = (
            self.db.query(MLModelDB)
            .filter(MLModelDB.output_type == output_type)
            .order_by(desc(MLModelDB.created_at))
            .limit(limit)
            .all()
        )

        return [self._map_to_read_model(m, include_details) for m in models]

    # --- Бизнес-логика ---
    async def calculate_cost(
        self, model_id: int, requests_count: int = 1
    ) -> Optional[Decimal]:
        """Расчет стоимости заданного количества запросов"""
        model = await self.db.get(MLModelDB, model_id)
        if not model:
            return None

        return model.cost_per_request * requests_count

    async def update_model_config(
        self, model_id: int, config_updates: Dict[str, Any]
    ) -> Optional[MLModelRead]:
        """Обновление конфигурации модели"""
        model = await self.db.get(MLModelDB, model_id)
        if not model:
            return None

        # Объединяем существующую конфигурацию с новыми значениями
        current_config = model.config or {}
        current_config.update(config_updates)

        model.config = current_config
        model.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(model)

        return MLModelRead.model_validate(model)

    # --- Вспомогательные методы ---
    def _map_to_read_model(
        self, model: MLModelDB, include_details: bool = False
    ) -> MLModelRead | MLModelDetailRead:
        """Преобразование ORM модели в соответствующую DTO"""
        if include_details:
            return MLModelDetailRead.model_validate(model)
        return MLModelRead.model_validate(model)
