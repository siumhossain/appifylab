import logging

import redis

from common.config import get_settings

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    get_settings().REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
    health_check_interval=30,
)


def check_redis_connection() -> bool:
    try:
        return bool(redis_client.ping())
    except redis.RedisError as e:
        logger.error(f"Redis connection failed: {e}")
        return False
