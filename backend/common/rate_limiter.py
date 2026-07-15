import logging
import random

import redis

from common.config import get_settings
from common.redis_client import redis_client

logger = logging.getLogger(__name__)

settings = get_settings()

_RATE_LIMIT_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 1 then
    return {1, redis.call('TTL', KEYS[1])}
end

local burst = redis.call('INCR', KEYS[2])
if burst == 1 then redis.call('EXPIRE', KEYS[2], ARGV[1]) end

local minute = redis.call('INCR', KEYS[3])
if minute == 1 then redis.call('EXPIRE', KEYS[3], ARGV[3]) end

local hour = redis.call('INCR', KEYS[4])
if hour == 1 then redis.call('EXPIRE', KEYS[4], ARGV[5]) end

if burst > tonumber(ARGV[2]) or minute > tonumber(ARGV[4]) or hour > tonumber(ARGV[6]) then
    redis.call('SET', KEYS[1], '1', 'EX', ARGV[7])
    return {1, tonumber(ARGV[7])}
end

return {0, 0}
"""


class RateLimitProfile:
    def __init__(self, burst_window, burst_limit, minute_window, minute_limit, hour_window, hour_limit):
        self.burst_window = burst_window
        self.burst_limit = burst_limit
        self.minute_window = minute_window
        self.minute_limit = minute_limit
        self.hour_window = hour_window
        self.hour_limit = hour_limit


def method_bucket(method: str) -> str:
    return "read" if method in ("GET", "HEAD") else "write"


def get_client_ip(request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


class RedisRateLimiter:
    KEY_PREFIX = "rl"

    def __init__(self):
        self.block_min_seconds = settings.RATE_LIMIT_BLOCK_MIN_SECONDS
        self.block_max_seconds = settings.RATE_LIMIT_BLOCK_MAX_SECONDS

        self.write_profile = RateLimitProfile(
            burst_window=10, burst_limit=settings.RATE_LIMIT_WRITE_BURST_LIMIT,
            minute_window=60, minute_limit=settings.RATE_LIMIT_WRITE_MINUTE_LIMIT,
            hour_window=3600, hour_limit=settings.RATE_LIMIT_WRITE_HOUR_LIMIT,
        )
        self.read_profile = RateLimitProfile(
            burst_window=10, burst_limit=settings.RATE_LIMIT_READ_BURST_LIMIT,
            minute_window=60, minute_limit=settings.RATE_LIMIT_READ_MINUTE_LIMIT,
            hour_window=3600, hour_limit=settings.RATE_LIMIT_READ_HOUR_LIMIT,
        )
        self._script = redis_client.register_script(_RATE_LIMIT_SCRIPT)

    def profile_for_method(self, method):
        return self.read_profile if method in ("GET", "HEAD") else self.write_profile

    def check(self, identity: str, method: str) -> tuple[bool, int]:
        profile = self.profile_for_method(method)
        bucket = method_bucket(method)
        block_key = f"{self.KEY_PREFIX}:block:{identity}"
        burst_key = f"{self.KEY_PREFIX}:burst:{identity}:{bucket}"
        minute_key = f"{self.KEY_PREFIX}:minute:{identity}:{bucket}"
        hour_key = f"{self.KEY_PREFIX}:hour:{identity}:{bucket}"

        block_ttl = random.randint(self.block_min_seconds, self.block_max_seconds)

        try:
            blocked, retry_after = self._script(
                keys=[block_key, burst_key, minute_key, hour_key],
                args=[
                    profile.burst_window, profile.burst_limit,
                    profile.minute_window, profile.minute_limit,
                    profile.hour_window, profile.hour_limit,
                    block_ttl,
                ],
            )
        except redis.RedisError as e:
            logger.warning(f"[RateLimiter] Redis check failed, failing open: {e}")
            return True, 0

        if blocked:
            return False, int(retry_after) if retry_after > 0 else block_ttl
        return True, 0


rate_limiter = RedisRateLimiter()
