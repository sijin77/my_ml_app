from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
from db.base_model import Base
from db.session import async_engine, get_async_db
from db.models.user import User_DB
from db.models.user_roles import UserRole_DB
from db.models.mlmodel import MLModel_DB
from db.models.mlmodel_settings import MLModelSettings_DB
from db.models.request_history import RequestHistory_DB
from db.models.transaction import Transaction_DB
from db.models.user_action_history import UserActionHistory_DB
import os

router = APIRouter(
    tags=["Database Management"],
    responses={404: {"description": "Not found"}},
)

MODELS = [
    User_DB,
    UserRole_DB,
    MLModel_DB,
    MLModelSettings_DB,
    RequestHistory_DB,
    Transaction_DB,
    UserActionHistory_DB,
]


def check_environment():
    """Проверка что операция разрешена в текущем окружении"""
    """Заглушка для проверки окружения - оеализую позже TODO"""
    # Всегда разрешаем выполнение (для тестирования)
    return


@router.post(
    "/create_tables",
    summary="Создание всех таблиц",
    response_description="Результат создания таблиц",
    responses={
        200: {"description": "Таблицы успешно созданы"},
        400: {"description": "Нет таблиц для создания"},
        500: {"description": "Ошибка сервера"},
    },
)
async def create_tables():
    """Создает все таблицы в базе данных в правильном порядке"""
    if not Base.metadata.tables:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "No tables found in metadata. Check model imports.",
            },
        )

    try:
        async with async_engine.begin() as conn:
            for model in MODELS:
                table = model.__table__
                print(f"Создаем таблицу: {table.name}")
                await conn.run_sync(table.create)

        # Получаем список созданных таблиц
        async with async_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            )
            tables = [row[0] for row in result]

        return {"status": "success", "created_tables": tables, "count": len(tables)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to create tables: {str(e)}",
                "suggestion": "Check database connection and server logs",
            },
        )


@router.delete(
    "/drop_tables",
    summary="Удаление всех таблиц",
    response_description="Результат удаления таблиц",
    responses={
        200: {"description": "Таблицы успешно удалены"},
        500: {"description": "Ошибка сервера"},
    },
)
async def drop_tables(
    confirm: bool = Query(False, description="Требуется подтверждение (?confirm=true)"),
    db: AsyncSession = Depends(get_async_db),
):
    """Удаляет все таблицы из базы данных"""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "confirmation_required",
                "message": "Добавьте ?confirm=true для подтверждения",
            },
        )

    try:
        async with async_engine.begin() as conn:
            # 1. Получаем список всех таблиц через SQL
            result = await conn.execute(
                text(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                )
            )
            tables = [row[0] for row in result]

            # 2. Временно отключаем проверку внешних ключей
            await conn.execute(text("SET session_replication_role = 'replica'"))

            # 3. Удаляем таблицы в правильном порядке
            for table in reversed(tables):
                await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))

            # 4. Восстанавливаем проверку
            await conn.execute(text("SET session_replication_role = 'origin'"))

            # 5. Удаляем все кастомные типы
            await drop_custom_types(conn)
            return {
                "status": "success",
                "dropped_tables": tables,
                "count": len(tables),
                "message": "Все таблицы успешно удалены",
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Ошибка при удалении таблиц: {str(e)}",
                "solution": "Проверьте активные соединения с БД",
            },
        )


async def drop_custom_types(conn):
    """Удаляет все пользовательские enum типы"""
    # Получаем список всех пользовательских enum типов
    result = await conn.execute(
        text(
            """
        SELECT t.typname 
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        GROUP BY t.typname
    """
        )
    )
    custom_types = [row[0] for row in result]

    # Удаляем каждый тип
    for type_name in custom_types:
        try:
            await conn.execute(text(f'DROP TYPE IF EXISTS "{type_name}" CASCADE'))
        except Exception as e:
            print(f"Ошибка удаления типа {type_name}: {str(e)}")
            continue


@router.get(
    "/health",
    summary="Проверка состояния БД",
    response_description="Статус подключения к БД",
    responses={
        200: {"description": "База данных доступна"},
        500: {"description": "Проблемы с подключением"},
    },
)
async def healthcheck(db: AsyncSession = Depends(get_async_db)):
    """Проверяет соединение с базой данных"""
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "OK",
            "database": "available",
            "details": {
                "connection_test": "successful",
                "environment": os.getenv("ENVIRONMENT", "development"),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "database_error",
                "message": str(e),
                "recovery_steps": [
                    "Check database server status",
                    "Verify connection settings",
                    "Review database logs",
                ],
            },
        )
