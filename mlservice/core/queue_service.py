import aio_pika
import json
import logging
from typing import Callable, Awaitable
from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger(__name__)


class QueueService:
    def __init__(self, rabbitmq_url: str, queue_name: str):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.is_consuming = False

    async def start_consuming(self, callback: Callable[[dict], Awaitable[dict]]):
        try:
            # Создаем устойчивое подключение
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                reconnect_interval=5,  # Попытка переподключения каждые 5 секунд
            )

            # Создаем канал
            self.channel = await self.connection.channel()
            await self.channel.set_qos(
                prefetch_count=1
            )  # Обрабатываем по одному сообщению

            # Объявляем очередь с параметрами
            queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True,  # Очередь сохраняется после перезапуска RabbitMQ
                auto_delete=False,  # Очередь не удаляется после отключения потребителей
            )

            async def on_message(message: AbstractIncomingMessage):
                async with message.process():
                    try:
                        logger.info(f"Received message: {message.body}")
                        data = json.loads(message.body.decode())
                        result = await callback(data)

                        # Если есть reply_to, отправляем ответ
                        if message.reply_to:
                            response = aio_pika.Message(
                                body=json.dumps(result).encode(),
                                correlation_id=message.correlation_id,
                            )
                            await self.channel.default_exchange.publish(
                                response, routing_key=message.reply_to
                            )

                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        # Можно добавить логику повторной обработки или DLQ здесь

            self.is_consuming = True
            await queue.consume(on_message)
            logger.info(f"Started consuming queue: {self.queue_name}")

        except Exception as e:
            logger.error(f"Failed to start consuming: {e}", exc_info=True)
            await self.close()
            raise

    async def close(self):
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            self.is_consuming = False
            logger.info("Queue service closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}", exc_info=True)

    async def health_check(self) -> bool:
        return self.connection is not None and not self.connection.is_closed
