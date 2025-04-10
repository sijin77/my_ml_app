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

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import and_, select


class MLModelSettingsService:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def create_setting(
        self, setting_data: MLModelSettingCreate
    ) -> MLModelSettingRead:
        """Create a new model setting"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    # Verify model exists
                    model = await session.get(MLModelDB, setting_data.model_id)
                    if not model:
                        raise ValueError("MLModel not found")

                    # Check for existing parameter
                    result = await session.execute(
                        select(MLModelSettingsDB).where(
                            and_(
                                MLModelSettingsDB.model_id == setting_data.model_id,
                                MLModelSettingsDB.parameter == setting_data.parameter,
                            )
                        )
                    )
                    if result.scalars().first():
                        raise ValueError("Parameter already exists for this model")

                    # Create new setting
                    db_setting = MLModelSettingsDB(**setting_data.model_dump())
                    session.add(db_setting)
                    await session.flush()
                    await session.refresh(db_setting)
                    return MLModelSettingRead.model_validate(db_setting)
            except Exception:
                await session.rollback()
                raise

    async def update_setting(
        self, setting_id: int, update_data: MLModelSettingUpdate
    ) -> Optional[MLModelSettingRead]:
        """Update model setting"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    setting = await session.get(MLModelSettingsDB, setting_id)
                    if not setting:
                        return None

                    update_dict = update_data.model_dump(exclude_unset=True)
                    for field, value in update_dict.items():
                        setattr(setting, field, value)

                    setting.updated_at = datetime.now(timezone.utc)
                    await session.flush()
                    await session.refresh(setting)
                    return MLModelSettingRead.model_validate(setting)
            except Exception:
                await session.rollback()
                raise

    async def delete_setting(self, setting_id: int) -> bool:
        """Delete model setting"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    setting = await session.get(MLModelSettingsDB, setting_id)
                    if not setting:
                        return False

                    await session.delete(setting)
                    await session.flush()
                    return True
            except Exception:
                await session.rollback()
                raise

    async def get_setting_by_id(
        self, setting_id: int, include_model: bool = False
    ) -> Optional[MLModelSettingRead | MLModelSettingDetailRead]:
        """Get setting by ID"""
        async with self.async_session_factory() as session:
            setting = await session.get(MLModelSettingsDB, setting_id)
            if not setting:
                return None

            if include_model:
                await session.refresh(setting, ["model"])

            return self._map_to_read_model(setting, include_model)

    async def get_model_settings(
        self, model_id: int, include_model: bool = False, limit: int = 100
    ) -> List[MLModelSettingRead | MLModelSettingDetailRead]:
        """Get all settings for a model"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(MLModelSettingsDB)
                .where(MLModelSettingsDB.model_id == model_id)
                .limit(limit)
            )
            settings = result.scalars().all()

            if include_model:
                for setting in settings:
                    await session.refresh(setting, ["model"])

            return [self._map_to_read_model(s, include_model) for s in settings]

    async def get_settings_by_parameter(
        self, parameter_name: str, include_model: bool = False, limit: int = 100
    ) -> List[MLModelSettingRead | MLModelSettingDetailRead]:
        """Get settings by parameter name"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(MLModelSettingsDB)
                .where(MLModelSettingsDB.parameter == parameter_name)
                .limit(limit)
            )
            settings = result.scalars().all()

            if include_model:
                for setting in settings:
                    await session.refresh(setting, ["model"])

            return [self._map_to_read_model(s, include_model) for s in settings]

    async def bulk_update_settings(
        self, model_id: int, settings_updates: Dict[str, str]
    ) -> List[MLModelSettingRead]:
        """Bulk update model settings"""
        async with self.async_session_factory() as session:
            try:
                async with session.begin():
                    updated_settings = []

                    for param_name, param_value in settings_updates.items():
                        # Find existing setting
                        result = await session.execute(
                            select(MLModelSettingsDB).where(
                                and_(
                                    MLModelSettingsDB.model_id == model_id,
                                    MLModelSettingsDB.parameter == param_name,
                                )
                            )
                        )
                        setting = result.scalars().first()

                        if setting:
                            setting.parameter_value = param_value
                            setting.updated_at = datetime.now(timezone.utc)
                        else:
                            # Create new setting if doesn't exist
                            setting = MLModelSettingsDB(
                                model_id=model_id,
                                parameter=param_name,
                                parameter_value=param_value,
                            )
                            session.add(setting)

                        updated_settings.append(setting)

                    await session.flush()

                    # Refresh all updated settings
                    for setting in updated_settings:
                        await session.refresh(setting)

                    return [
                        MLModelSettingRead.model_validate(s) for s in updated_settings
                    ]
            except Exception:
                await session.rollback()
                raise

    def _map_to_read_model(
        self, setting: MLModelSettingsDB, include_model: bool = False
    ) -> MLModelSettingRead | MLModelSettingDetailRead:
        """Convert ORM model to DTO"""
        if include_model:
            return MLModelSettingDetailRead.model_validate(setting)
        return MLModelSettingRead.model_validate(setting)
