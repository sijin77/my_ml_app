from datetime import datetime, timezone
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from db.models.mlmodel_settings import MLModelSettingsDB
from db.models.mlmodel import MLModelDB
from schemas.mlmodel_settings import (
    MLModelSettingCreate,
    MLModelSettingRead,
    MLModelSettingUpdate,
    MLModelSettingDetailRead,
)


class MLModelSettingsService:
    def __init__(self, db: Session):
        self.db = db

    # --- Основные CRUD операции ---
    async def create_setting(
        self, setting_data: MLModelSettingCreate
    ) -> MLModelSettingRead:
        """Создание новой настройки для модели"""
        # Проверяем существование модели
        model = await self.db.get(MLModelDB, setting_data.model_id)
        if not model:
            raise ValueError("MLModel not found")

        # Проверяем не существует ли уже такой параметр
        stmt = select(MLModelSettingsDB).where(
            and_(
                MLModelSettingsDB.model_id == setting_data.model_id,
                MLModelSettingsDB.parameter == setting_data.parameter,
            )
        )
        result = await self.db.execute(stmt)
        existing_setting = result.scalars().first()

        if existing_setting:
            raise ValueError("Parameter already exists for this model")

        db_setting = MLModelSettingsDB(**setting_data.model_dump())

        self.db.add(db_setting)
        await self.db.commit()
        await self.db.refresh(db_setting)

        return MLModelSettingRead.model_validate(db_setting)

    async def update_setting(
        self, setting_id: int, update_data: MLModelSettingUpdate
    ) -> Optional[MLModelSettingRead]:
        """Обновление параметра модели"""
        setting = await self.db.get(MLModelSettingsDB, setting_id)
        if not setting:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(setting, field, value)

        setting.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(setting)

        return MLModelSettingRead.model_validate(setting)

    async def delete_setting(self, setting_id: int) -> bool:
        """Удаление параметра модели"""
        setting = await self.db.get(MLModelSettingsDB, setting_id)
        if not setting:
            return False

        self.db.delete(setting)
        await self.db.commit()
        return True

    # --- Методы получения данных ---
    async def get_setting_by_id(
        self, setting_id: int, include_model: bool = False
    ) -> Optional[MLModelSettingRead | MLModelSettingDetailRead]:
        """Получение параметра по ID"""
        setting = await self.db.get(MLModelSettingsDB, setting_id)
        if not setting:
            return None

        return self._map_to_read_model(setting, include_model)

    async def get_model_settings(
        self, model_id: int, include_model: bool = False, limit: int = 100
    ) -> List[MLModelSettingRead | MLModelSettingDetailRead]:
        """Получение всех параметров модели"""

        stmt = select(MLModelSettingsDB).where(MLModelSettingsDB.model_id == model_id)
        result = await self.db.execute(stmt)
        settings = result.limit(limit).all()

        return [self._map_to_read_model(s, include_model) for s in settings]

    async def get_settings_by_parameter(
        self, parameter_name: str, include_model: bool = False, limit: int = 100
    ) -> List[MLModelSettingRead | MLModelSettingDetailRead]:
        """Получение параметров по имени"""
        stmt = select(MLModelSettingsDB).where(
            MLModelSettingsDB.parameter == parameter_name
        )
        result = await self.db.execute(stmt)
        settings = result.limit(limit).all()

        return [self._map_to_read_model(s, include_model) for s in settings]

    # --- Бизнес-логика ---
    async def bulk_update_settings(
        self, model_id: int, settings_updates: Dict[str, str]
    ) -> List[MLModelSettingRead]:
        """Массовое обновление параметров модели"""
        updated_settings = []

        for param_name, param_value in settings_updates.items():
            # Находим существующий параметр
            stmt = select(MLModelSettingsDB).where(
                and_(
                    MLModelSettingsDB.model_id == model_id,
                    MLModelSettingsDB.parameter == param_name,
                )
            )
            result = await self.db.execute(stmt)
            setting = result.scalars().first()

            if setting:
                setting.parameter_value = param_value
                setting.updated_at = datetime.now(timezone.utc)
                updated_settings.append(setting)
            else:
                # Создаем новый параметр, если не существует
                new_setting = MLModelSettingsDB(
                    model_id=model_id,
                    parameter=param_name,
                    parameter_value=param_value,
                )
                self.db.add(new_setting)
                updated_settings.append(new_setting)

        await self.db.commit()
        return [MLModelSettingRead.model_validate(s) for s in updated_settings]

    # --- Вспомогательные методы ---
    def _map_to_read_model(
        self, setting: MLModelSettingsDB, include_model: bool = False
    ) -> MLModelSettingRead | MLModelSettingDetailRead:
        """Преобразование ORM модели в соответствующую DTO"""
        if include_model:
            return MLModelSettingDetailRead.model_validate(setting)
        return MLModelSettingRead.model_validate(setting)
