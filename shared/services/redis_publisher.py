from redis.asyncio import Redis

from shared.config import settings
from shared.schemas import PaymentEvent


class RedisStreamPublisher:
    def __init__(self, client: Redis):
        self.client = client

    async def publish(
        self, event: PaymentEvent,
        stream: str = settings.redis.stream_name
    ):
        data = event.model_dump_json(ensure_ascii=False)
        return await self.client.xadd(
            name=stream,
            fields={"data": data}
        )
