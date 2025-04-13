import aio_pika
import json
import base64
from fastapi import UploadFile
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()


class QwenVLClient:
    def __init__(self):
        self.connection = None

    async def connect(self):
        self.connection = await aio_pika.connect(os.getenv("RABBITMQ_URL"))
        return self

    async def query_model(self, text: str, image: UploadFile = None) -> dict:
        """Отправка мультимодального запроса"""
        image_b64 = None
        if image:
            image_data = await image.read()
            image_b64 = base64.b64encode(image_data).decode()

        async with self.connection.channel() as channel:
            callback_queue = await channel.declare_queue(exclusive=True)

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps({"text": text, "image": image_b64}).encode(),
                    reply_to=callback_queue.name,
                ),
                routing_key=os.getenv("ML_REQUEST_QUEUE"),
            )

            async with callback_queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        return json.loads(message.body.decode())


@asynccontextmanager
async def lifespan(app):
    client = await QwenVLClient().connect()
    app.state.qwen_client = client
    yield
    await client.connection.close()
