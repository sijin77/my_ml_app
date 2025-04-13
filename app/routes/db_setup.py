from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
from tests import seed_data
from db.base_model import Base
from db.session import async_engine, AsyncSessionFactory, init_db
from db.models.user import UserDB
from db.models.user_roles import UserRoleDB
from db.models.mlmodel import MLModelDB
from db.models.mlmodel_settings import MLModelSettingsDB
from db.models.request_history import RequestHistoryDB
from db.models.transaction import TransactionDB
from db.models.user_action_history import UserActionHistoryDB
import os

router = APIRouter(
    tags=["Database Management"],
    responses={404: {"description": "Not found"}},
)


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
        await init_db()
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


@router.get(
    "/seed",
    summary="заполнить БД тестовыми данными",
)
async def seed():
    """Проверяет соединение с базой данных"""
    try:
        await seed_data.async_seed_and_test(AsyncSessionFactory)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "database_error",
                "message": str(e),
            },
        )
