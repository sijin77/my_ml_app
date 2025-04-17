import asyncio
import logging
from config import config
from aio_pika import logger
from core.queue_service import QueueService
from core.model import QwenVLModel
from services.ml_service import MLService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_ml_service():
    model = QwenVLModel(model_name=config.MODEL_NAME)
    return MLService(model)


async def main():
    ml_service = await create_ml_service()
    queue_service = QueueService(
        rabbitmq_url=config.RABBITMQ_URL, queue_name=config.ML_QUEUE
    )

    async def handler(data: dict):
        return await ml_service.predict(**data)

    try:
        await queue_service.start_consuming(handler)

        # Держим сервис запущенным
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await queue_service.close()


if __name__ == "__main__":
    asyncio.run(main())
