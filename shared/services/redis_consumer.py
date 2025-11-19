import asyncio
import json
from typing import Any, Dict, Optional

import redis.asyncio as redis
from redis.exceptions import ResponseError

from shared.config import setup_logger
from shared.config import settings

logger = setup_logger(__name__)


class RedisStreamConsumer:
    """
    Минимальный Redis Streams consumer (Этап 1).
    - создаёт consumer group при необходимости
    - читает сообщения блокирующим XREADGROUP
    - вызывает простой обработчик handle_message_simple и ACK'ит сообщения
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        stream: str = "payments_stream",
        group: str = "bot_group",
        consumer: str = "bot_consumer",
        block_ms: int = 5000,
        read_count: int = 10,
    ):
        self.redis = redis_client
        self.stream = stream
        self.group = group
        self.consumer = consumer
        self.block_ms = block_ms
        self.read_count = read_count
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def ensure_group(self) -> None:
        """
        Создаёт consumer group, если её нет.
        MKSTREAM=True создаёт сам stream, если он ещё не существует.
        """
        try:
            await self.redis.xgroup_create(self.stream, self.group, id="$", mkstream=True)
            logger.info(
                f"Created consumer group '{self.group}' "
                f"on stream '{self.stream}'"
            )
        except ResponseError as e:
            msg = str(e)
            if "BUSYGROUP" in msg or "NOGROUP" in msg:
                logger.debug(
                    f"Consumer group '{self.group}' already exists ({msg})"
                )
            else:
                logger.exception(f"Error creating group: {e}")
                raise
        except Exception as e:
            logger.exception(f"Unexpected error while creating group: {e}")
            raise

    async def handle_message_simple(self, msg_id: str, fields: Dict[str, Any]) -> None:
        """
        Минимальная обработка сообщения: разобрать JSON в поле 'data' (если есть),
        залогировать и ACK'нуть сообщение.
        """
        try:
            if "data" in fields:
                raw = fields["data"]
            else:
                raw = json.dumps(fields)

            try:
                payload = json.loads(raw)
            except Exception as parse_exc:
                try:
                    await self.redis.xadd(
                        settings.redis.dlq_stream,
                        {
                            "orig_id": msg_id,
                            "orig_raw": raw,
                            "error": f"json_parse_error: {str(parse_exc)}"
                        }
                    )
                    logger.info(
                        f"Pushed malformed message id={msg_id} "
                        f"to DLQ '{settings.redis.dlq_stream}'"
                    )
                except Exception as dlq_exc:
                    logger.exception(
                        f"Failed to push malformed message id={msg_id} "
                        f"to DLQ: {dlq_exc}"
                    )

                await self.redis.xack(self.stream, self.group, msg_id)
                return

            logger.info(f"Received message id={msg_id} payload={payload}")

            from shared.schemas import PaymentEvent
            from bot.services import PaymentHandler
            try:
                event = PaymentEvent.model_validate(payload)
            except Exception as val_exc:
                logger.exception(
                    f"PaymentEvent validation failed for id={msg_id}: {val_exc}"
                )
                try:
                    await self.redis.xadd(
                        settings.redis.dlq_stream,
                        {
                            "orig_id": msg_id,
                            "orig_payload": json.dumps(payload),
                            "error": f"validation_error: {str(val_exc)}"
                        }
                    )
                    logger.info(
                        f"Pushed invalid message id={msg_id} "
                        f"to DLQ '{settings.redis.dlq_stream}'"
                    )
                except Exception as dlq_exc:
                    logger.exception(
                        f"Failed to push invalid message id={msg_id} "
                        f"to DLQ: {dlq_exc}"
                    )

                await self.redis.xack(self.stream, self.group, msg_id)
                return

            logger.info(
                f"Received valid PaymentEvent id={msg_id} payload={event}"
            )

            await PaymentHandler.process(event)
            await self.redis.xack(self.stream, self.group, msg_id)
            logger.info(
                f"Acknowledged message id={msg_id} after successful processing"
            )
        except Exception as e:
            logger.exception(f"Error handling message id={msg_id}: {e}")


    async def start_listening(self) -> None:
        """
        Основной loop: блокирующе читаем новые сообщения в consumer group и обрабатываем их.
        """
        logger.info(
            f"Starting RedisStreamConsumer: stream={self.stream} "
            f"group={self.group} consumer={self.consumer}"
        )
        self._running = True

        while self._running:
            try:
                resp = await self.redis.xreadgroup(
                    groupname=self.group,
                    consumername=self.consumer,
                    streams={self.stream: ">"},
                    count=self.read_count,
                    block=self.block_ms,
                )

                if not resp:
                    continue

                for stream_name, messages in resp:
                    for msg_id, fields in messages:
                        await self.handle_message_simple(msg_id, fields)

            except Exception as e:
                logger.exception(f"Error in listening loop: {e}")
                # Небольшой бэкoff перед новой попыткой
                await asyncio.sleep(1)

        logger.info("Stopped RedisStreamConsumer loop")

    def run_in_background(self) -> None:
        """
        Запустить consumer как background asyncio.Task (внутри уже работающего event loop).
        Возвращает Task (через self._task).
        """
        if self._task and not self._task.done():
            logger.warning("Consumer already running")
            return

        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self.start_listening())

    async def stop(self) -> None:
        """
        Остановить цикл gracefully.
        """
        logger.info("Stopping RedisStreamConsumer...")
        self._running = False
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5)
            except asyncio.TimeoutError:
                logger.warning("Consumer task did not finish in time, cancelling")
                self._task.cancel()
                try:
                    await self._task
                except Exception:
                    pass

    async def run(self) -> None:
        """
        Удобный метод для запуска в качестве основного корутинного runner:
        ensure_group + start_listening.
        """
        await self.ensure_group()
        await self.start_listening()
