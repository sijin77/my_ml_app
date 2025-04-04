import asyncio
from typing import AsyncGenerator
from app.config.config import settings
from contextlib import (
    asynccontextmanager,
)  # Используем асинхронный контекстный менеджер
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=False,
    pool_size=20,  # Размер пула соединений
    max_overflow=30,  # Максимальное количество соединений
    pool_pre_ping=True,  # Проверка активности соединений
    pool_recycle=3600,  # Пересоздание соединений каждый час
    connect_args={
        "timeout": 5,  #  Для asyncpg
        "command_timeout": 10,  # Таймаут выполнения запросов (опционально)
    },
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    db = AsyncSessionLocal()
    try:
        yield db
    except Exception as e:
        await db.rollback()
        raise e
    finally:
        await db.close()


# Теперь можно использовать async with
async def get_db_version():
    async with get_async_db() as db:
        result = await db.execute(text("SELECT version()"))
        print(f"Ураааааааа {result}")


asyncio.run(get_db_version())
