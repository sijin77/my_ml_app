import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from db.base_model import Base


@pytest.fixture(scope="session")
async def async_engine():
    """Фикстура для создания асинхронного движка БД"""
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def setup_database(async_engine):
    """Фикстура для настройки тестовой базы данных"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
def async_session_factory(async_engine):
    """Фабрика для создания асинхронных сессий"""
    return sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
async def async_session(async_session_factory, setup_database):
    """Фикстура для создания асинхронной сессии"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
