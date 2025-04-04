from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from config.config import get_settings

settings = get_settings()
# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URL_asyncpg,
    echo=True,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "timeout": 10  # Для asyncpg используется просто "timeout", а не "connect_timeout"
    },
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(async_engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_async_session() -> AsyncSession:
    """
    Создает и возвращает новую асинхронную сессию без контекстного менеджера.
    Позволяет более гибко управлять жизненным циклом сессии.
    """
    return AsyncSessionLocal()
