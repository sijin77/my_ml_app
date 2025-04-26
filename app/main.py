from pathlib import Path
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi import FastAPI
from routes.chat import router as chat_router
from routes.home import router as home_router
from routes.db_setup import router as db_router
from routes.users_route import router as users_router
from routes.model_route import router as model_router
from routes.profile import router as profile_router
from routes.transaction_route import router as transaction_router
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_route import router as auth_router

app = FastAPI(
    title="ML Model API",
    description="API для управления ML моделями и базой данных",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(profile_router)
app.include_router(auth_router)
app.include_router(home_router)
app.include_router(users_router)
app.include_router(model_router)
app.include_router(transaction_router)
app.include_router(db_router)

BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
