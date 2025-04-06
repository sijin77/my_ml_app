import uvicorn
from fastapi import FastAPI
from routes.db_setup import router as db_router
from routes.users_route import router as users_router
from db.session import get_async_db, init_db
from tests.seed_data import async_seed_and_test, AsyncTestDataSeeder

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
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc",
            "openapi_schema": "/api/openapi.json",
        },
    }


@app.on_event("startup")
async def on_startup():

    await init_db()
    async with get_async_db() as session:
        await async_seed_and_test(session)


@app.on_event("shutdown")
async def shutdown():
    """Закрытие соединений при завершении работы"""
    from db.session import async_engine

    await async_engine.dispose()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
