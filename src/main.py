import uvicorn
from fastapi import FastAPI
from config.app_config import settings

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
