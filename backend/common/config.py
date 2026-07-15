from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True

    DEBUG: bool = False

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    RATE_LIMIT_BLOCK_MIN_SECONDS: int = 1800
    RATE_LIMIT_BLOCK_MAX_SECONDS: int = 3600
    RATE_LIMIT_WRITE_BURST_LIMIT: int = 10
    RATE_LIMIT_WRITE_MINUTE_LIMIT: int = 30
    RATE_LIMIT_WRITE_HOUR_LIMIT: int = 300
    RATE_LIMIT_READ_BURST_LIMIT: int = 40
    RATE_LIMIT_READ_MINUTE_LIMIT: int = 180
    RATE_LIMIT_READ_HOUR_LIMIT: int = 3000


    # Cloudflare R2 Configuration
    R2_ACCESS_KEY_ID: str 
    R2_SECRET_ACCESS_KEY: str 
    R2_ENDPOINT_HOST: str 
    R2_BUCKET: str 
    R2_PUBLIC_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
