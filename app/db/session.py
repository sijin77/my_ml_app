from typing import AsyncIterator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager
from config.config import get_settings
from db.base_model import Base

settings = get_settings()
# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URL_asyncpg,
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "timeout": 10  # Для asyncpg используется просто "timeout", а не "connect_timeout"
    },
)

# Create async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_async_db() -> AsyncIterator[AsyncSession]:
    """Асинхронный генератор сессий БД"""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            raise exc
        finally:
            await session.close()


async def init_db():
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
