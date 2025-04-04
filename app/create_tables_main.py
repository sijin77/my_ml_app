import asyncio
from sqlalchemy import inspect, text
from db.base_model import Base
from db.session import async_engine

from db.models.mlmodel import MLModel_DB
from db.models.mlmodel_settings import MLModelSettings_DB
from db.models.request_history import RequestHistory_DB
from db.models.transaction import Transaction_DB
from db.models.user import User_DB
from db.models.user_action_history import UserActionHistory_DB
from db.models.user_roles import UserRole_DB

MODELS = [
    User_DB,
    UserRole_DB,
    MLModel_DB,
    MLModelSettings_DB,
    RequestHistory_DB,
    Transaction_DB,
    UserActionHistory_DB,
]


async def create_tables():
    """Создает таблицы в заданном порядке"""
    print("\n=== Создание таблиц ===")

    if not Base.metadata.tables:
        print(" Нет таблиц для создания!")
        return False

    try:
        async with async_engine.begin() as conn:
            # Создаем таблицы в явном порядке
            for model in MODELS:
                table = model.__table__
                print(f"Создаем таблицу: {table.name}")
                await conn.run_sync(table.create)

        print("✅ Все таблицы успешно созданы")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        return False


async def list_tables_simple():
    """Простой вывод списка таблиц через SQL"""
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        )
        print("\nТаблицы в БД:", [row[0] for row in result])


async def main():
    # 1. Создаем таблицы
    await create_tables()
    await list_tables_simple()
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
