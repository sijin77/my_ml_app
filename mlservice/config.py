import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MODEL_NAME = os.getenv("HF_MODEL_NAME", "Qwen/Qwen2-VL-2B-Instruct")
    DEVICE = os.getenv("DEVICE", "auto")
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin@rabbitmq:5672/")
    ML_QUEUE = os.getenv("ML_QUEUE", "ml_requests")


config = Config()
