from redis.asyncio import Redis

from shared.config import settings, setup_logger
from shared.services import RedisStreamPublisher


logger = setup_logger(__name__)


async def get_publisher():
    redis_client = RedisManager.get_client()
    return RedisStreamPublisher(client=redis_client)


class RedisManager:
    _redis_client: Redis | None = None

    @classmethod
    def get_client(cls) -> Redis:
        if cls._redis_client is None:
            cls._redis_client = Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                db=settings.redis.db,
                password=settings.redis.password,
                decode_responses=True,
            )
        return cls._redis_client
