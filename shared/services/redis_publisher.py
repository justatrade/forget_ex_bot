from redis.asyncio import Redis

from shared.config import settings
from shared.schemas import PaymentEvent


class RedisStreamPublisher:
    def __init__(self, client: Redis):
        self.client = client

    async def publish(
        self, event: PaymentEvent | dict,
        stream: str = settings.redis.stream_name
    ):
        if isinstance(event, PaymentEvent):
            data = event.model_dump_json(ensure_ascii=False)
        else:
            data = event
        return await self.client.xadd(
            name=stream,
            fields={"data": data}
        )
