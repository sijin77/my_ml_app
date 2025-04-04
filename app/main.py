import uvicorn
from fastapi import FastAPI
from routes.db_setup import router as db_router
from routes.users import router as users_router
import os

app = FastAPI(
    title="ML Model API",
    description="API для управления ML моделями и базой данных",
    version="1.0.0",
    docs_url="/api/docs",  # Явно указываем путь
    openapi_url="/api/openapi.json",  # Путь к OpenAPI схеме
)

# Подключаем роутер с префиксом
app.include_router(db_router, prefix="/api")
app.include_router(users_router)
# Подключаем роутер
app.include_router(db_router)


@app.get(
    "/",
    summary="Информация о API",
    response_description="Основная информация о доступных эндпоинтах",
)
async def root():
    """Возвращает основную информацию о API и доступных эндпоинтах"""
    return {
        "app": "ML Model Management API",
        "version": app.version,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "database": {
                "create_tables": {
                    "method": "POST",
                    "path": "/api/db/create_tables",
                    "description": "Создание всех таблиц в базе данных",
                },
                "drop_tables": {
                    "method": "DELETE",
                    "path": "/api/db/drop_tables",
                    "description": "Удаление всех таблиц (только для разработки)",
                    "warning": "Требуется ?confirm=true",
                },
                "healthcheck": {
                    "method": "GET",
                    "path": "/api/db/health",
                    "description": "Проверка состояния базы данных",
                },
            },
            "users": {
                "seed_users": {
                    "method": "POST",
                    "path": "/api/users/seed",
                    "description": "Заполнение тестовыми пользователями",
                }
            },
            "documentation": {
                "swagger": "/api/docs",
                "redoc": "/api/redoc",
                "openapi_schema": "/api/openapi.json",
            },
        },
        "instructions": {
            "quick_start": [
                "1. Создать таблицы: POST /api/db/create_tables",
                "2. Заполнить тестовыми данными: POST /api/users/seed",
                "3. Проверить состояние: GET /api/db/health",
            ],
            "warning": "Эндпоинты удаления и заполнения тестовыми данными должны быть отключены в production",
        },
    }


@app.on_event("shutdown")
async def shutdown():
    """Закрытие соединений при завершении работы"""
    from db.session import async_engine

    await async_engine.dispose()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
