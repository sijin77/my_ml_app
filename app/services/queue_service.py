# services/queue_service.py
import asyncio
import json
import uuid
import aio_pika
from typing import Dict, Any


class QueueService:
    def __init__(self, rabbitmq_url: str, request_queue: str = "ml_requests"):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.request_queue = request_queue

    async def connect(self):
        """Подключение к RabbitMQ"""
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()

        # Объявляем очереди
        await self.channel.declare_queue(self.request_queue, durable=True)
        return self

    async def send_request(
        self, payload: Dict[str, Any], timeout: int = 30
    ) -> Dict[str, Any]:
        """Отправка запроса в очередь и ожидание ответа"""
        try:
            # Создаем временную очередь для ответа
            callback_queue = await self.channel.declare_queue(exclusive=True)

            correlation_id = str(uuid.uuid4())

            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(payload).encode(),
                    reply_to=callback_queue.name,
                    correlation_id=correlation_id,
                    expiration=timeout * 1000,
                ),
                routing_key=self.request_queue,
            )

            # Ожидаем ответ
            async with callback_queue.iterator() as queue_iter:
                async for message in queue_iter:
                    if message.correlation_id == correlation_id:
                        async with message.process():
                            return json.loads(message.body.decode())

            raise TimeoutError("No response received within timeout")

        except asyncio.TimeoutError:
            raise TimeoutError("Request timed out")
        except Exception as e:
            raise ConnectionError(f"Queue error: {str(e)}")

    async def close(self):
        """Закрытие соединения"""
        if self.connection:
            await self.connection.close()
